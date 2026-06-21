"""
포트폴리오 스크린샷 OCR -> 종목명 추출 + stocks.csv 매칭
EasyOCR + 3,004종목 DB 퍼지매칭. KRX 모바일 + HTS 모두 지원.
v2: 종목명 인식에 집중, 수량/현재가 추출 제거.
"""
import csv, re, os
from difflib import SequenceMatcher

STOCKS_CSV = os.path.join(os.path.dirname(__file__), 'data', 'stocks.csv')

IGNORE_TEXTS = {
    '주식실시간잔고', '실시간계좌관리', 'KRX', '모의',
    '총 평가손익', '총매입금액', '총평가금액', '추정자산', '총매입', '총손익', '총평가',
    '실현손익', '예수금', '매매단가', '평가손익', '수익률', '매입가', '매 입 가',
    '종목명', '잔고', '구분', '가능', '보유수량', '가능수량', '현재가',
    '거래내역', '관심 종목', '주식 현재가', '주식 주문', '주식 잔고',
    '계좌번호', '원장미체결', '주문가능', '잔고확인', '잔고확민',
    '유의사항', '조회', '일괄매도', '닫기', '개별', '전체', '제비용', '합',
    '선택한 종목 추가', '인식된 종목', 'OCR 기능', 'Render', '사진 추가', '종목 추가',
    'KOSPI', 'KOSDAQ', '현금', '자동입력', '통수의률', '통손의', '수의물', '일너매도',
}


def load_stock_db(csv_path=None):
    if csv_path is None: csv_path = STOCKS_CSV
    stocks = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            stocks.append((row['ticker'], row['name'], row.get('market', '')))
    return stocks


def fuzzy_search(name, stock_db, threshold=0.5):
    """퍼지 매칭. 우선주 패널티 + 정확일치 보너스 + ETF 브랜드 선호"""
    best_score, best_match = 0, None
    nc = name.strip().upper()
    ns = re.sub(r'\s+', '', nc)
    
    for ticker, sn, market in stock_db:
        sc = sn.strip().upper()
        ss = re.sub(r'\s+', '', sc)
        score = SequenceMatcher(None, nc, sc).ratio()
        bonus = 0
        
        # 정확 일치
        if nc == sc:
            bonus = 0.5
        # substring
        elif len(ns) >= 3 and ns in ss:
            bonus = 0.3
        elif len(ss) >= 3 and ss in ns:
            bonus = 0.25
        
        # 괄호/접미사 떼고 비교
        if len(ns) >= 4:
            sb = re.sub(r'\([^)]*\)|Plus$|액티브$|합성$', '', ss)
            nb = re.sub(r'\([^)]*\)|Plus$|액티브$|합성$', '', ns)
            if nb and sb and len(nb) >= 3:
                score = max(score, SequenceMatcher(None, nb, sb).ratio())
        
        # 우선주 강력 패널티 (한국금융지주 >> 한국금융지주우)
        if '우' in sc and '우' not in nc:
            bonus -= 0.25
        
        total = score + bonus
        
        # ETF 브랜드 선호 타이브레이커
        if total > best_score or (best_match is not None and abs(total - best_score) < 0.10):
            preferred = ['KODEX ', 'TIGER ', 'ACE ', 'TIME ', 'HANARO ', 'RISE ', 'SOL ']
            if best_match is not None and abs(total - best_score) < 0.10:
                old_pref = any(best_match[1].upper().startswith(p) for p in preferred)
                new_pref = any(sn.upper().startswith(p) for p in preferred)
                if old_pref and not new_pref:
                    continue
            best_score = total
            best_match = (ticker, sn, market, total)
    
    return best_match if best_score >= threshold else None


def _is_num(t):
    return bool(re.match(r'^-?[\d,]+$', t))


def _looks_like_stock(text):
    t = text.strip()
    if len(t) < 2: return False
    if t in IGNORE_TEXTS: return False
    if _is_num(t): return False
    if re.match(r'^[가-힣]$', t): return False
    return bool(re.search(r'[가-힣]|[A-Za-z]{2,}', t))


def _make_items(ocr_results):
    items = []
    for bbox, text, conf in sorted(ocr_results, key=lambda r: (r[0][0][1], r[0][0][0])):
        if conf < 0.15: continue
        clean = text.strip()
        if len(clean) <= 1 and not clean.isdigit(): continue
        if clean in IGNORE_TEXTS: continue
        if len(clean) == 1 and clean.isalpha() and clean not in 'AI': continue
        items.append({
            'text': clean, 'conf': conf,
            'x': (bbox[0][0] + bbox[2][0]) / 2,
            'y': (bbox[0][1] + bbox[2][1]) / 2,
        })
    return items


def _group_rows(items, threshold):
    if not items: return []
    rows, cur = [], [items[0]]
    for it in items[1:]:
        if abs(it['y'] - cur[-1]['y']) <= threshold:
            cur.append(it)
        else:
            rows.append(cur); cur = [it]
    rows.append(cur)
    return rows


def extract_stocks_from_ocr_results(ocr_results):
    """
    종목명만 추출. 수량/현재가 무시, 종목명 인식 정확도에 집중.
    2-pass: (1) row 단위 텍스트 (2) 좌측 30% 영역 fallback
    """
    items = _make_items(ocr_results)
    if not items: return []

    seen_names = set()
    result = []

    # Pass 1: row grouping — 각 row의 텍스트(한글/영문)에서 종목명 추출
    for threshold in [14, 22]:
        rows = _group_rows(items, threshold)
        for row in rows:
            row.sort(key=lambda it: it['x'])
            name_parts = [it['text'] for it in row if _looks_like_stock(it['text'])]
            if not name_parts:
                continue
            name = ' '.join(name_parts)
            key = name.strip().upper()
            if key in seen_names: continue
            seen_names.add(key)
            result.append({'name': name, 'qty': 0, 'price': 0})

    # Pass 2: 좌측 30% 영역 fallback — row grouping이 놓친 종목
    max_x = max(it['x'] for it in items) if items else 500
    left = sorted(
        [it for it in items if it['x'] < max_x * 0.3 and _looks_like_stock(it['text'])],
        key=lambda it: it['y']
    )
    if left:
        groups, cur = [], [left[0]]
        for it in left[1:]:
            if it['y'] - cur[-1]['y'] <= 15:
                cur.append(it)
            else:
                groups.append(cur); cur = [it]
        groups.append(cur)

        SOLO = {'ACE','TIGER','KODEX','TIME','TIIME','HANARO','RISE','SOL',
                'KoAct','KIWOOM','1Q','PLUS','KB','TIGER ETF'}
        for grp in groups:
            grp.sort(key=lambda it: it['x'])
            name = ' '.join(it['text'] for it in grp)
            if name.strip().upper() in SOLO: continue
            key = name.strip().upper()
            if key not in seen_names:
                seen_names.add(key)
                result.append({'name': name, 'qty': 0, 'price': 0})

    return result


def _format_ocr_rows(ocr_results):
    """OCR 결과를 row 단위 텍스트로 포맷 (LLM 입력용)"""
    items = _make_items(ocr_results)
    if not items: return ""
    
    lines = []
    for threshold in [12, 18]:
        rows = _group_rows(items, threshold)
        for row in rows:
            row.sort(key=lambda it: it['x'])
            line = " | ".join(it['text'] for it in row)
            if line.strip():
                lines.append(line)
        if len(lines) >= 5:
            break
    
    return "\n".join(lines)


def _llm_extract_stocks(ocr_text, api_key=None):
    """LLM에게 OCR 텍스트를 보내 종목명만 추출"""
    import json, os
    import urllib.request
    
    if not api_key:
        api_key = os.environ.get('LLM_API_KEY', os.environ.get('DEEPSEEK_API_KEY', os.environ.get('OPENAI_API_KEY', '')))
    if not api_key:
        return None  # API 키 없으면 LLM 생략
    
    base_url = os.environ.get('LLM_BASE_URL', 'https://api.deepseek.com/v1')
    model = os.environ.get('LLM_MODEL', 'deepseek-chat')
    
    prompt = f"""You are extracting stock/ETF names from a Korean brokerage app screenshot OCR result.

Below are text items detected by OCR from a "보유종목/잔고" (holdings/balance) screen.
Each line represents one row of text from the screen, with items separated by "|".

OCR rows:
{ocr_text}

Your task: Extract ONLY the actual stock/ETF names held in the portfolio. 

Rules:
- IGNORE: UI labels (메뉴, 관심종목, 계좌, 주문, 차트, 현재가, 국내잔고, 미체결, 예수금, 주문가능금액, 유의, 계산기, 융자별, 융자합, 나스닥, S&P500, 지수, 채팅), tab names (키움 잔고, 타사 잔고), account info (계좌번호, 사람이름), financial figures (손익, 매입, 평가, 수익률, 원, %), column headers (종목명, 매입가, 현재가, 보유수량, 평가손익, 수익률), ranking labels (MY랭킹, 순위)
- IMPORTANT: If a stock/ETF name is split across multiple items on the same row, COMBINE them. Example: "KODEX" + "코스닥150" → "KODEX 코스닥150". "HANARO Fn" + "K-반도체" → "HANARO Fn K-반도체".
- Include both Korean stocks (삼성전자, NAVER) and ETFs (KODEX, TIGER, HANARO, ACE, etc.)
- If OCR slightly misread a name (e.g., "한화오선" → "한화오션", "한국금움지주" → "한국금융지주"), correct it to the most likely real stock name.

Return ONLY a JSON array of strings, nothing else. Example: ["삼성전자", "NAVER", "KODEX 코스닥150"]"""

    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 200
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode('utf-8'))
            content = body['choices'][0]['message']['content'].strip()
            # JSON 배열만 추출 (마크다운 코드블록 제거)
            if content.startswith('```'):
                content = content.split('\n', 1)[1]
                if content.endswith('```'):
                    content = content.rsplit('\n', 1)[0]
            names = json.loads(content)
            return names if isinstance(names, list) else None
    except Exception as e:
        print(f"[LLM extract] Failed: {e}")
        return None


def process_portfolio_image(image_path, stock_db=None, api_key=None):
    import easyocr, numpy as np
    from PIL import Image
    
    if stock_db is None: stock_db = load_stock_db()
    
    img = Image.open(image_path)
    w, h = img.size
    if min(w, h) < 1200:
        img = img.resize((w * 2, h * 2), Image.LANCZOS)
    
    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    ocr_results = reader.readtext(np.array(img))
    
    # 1. LLM 기반 추출 시도
    ocr_text = _format_ocr_rows(ocr_results)
    llm_names = _llm_extract_stocks(ocr_text, api_key=api_key)
    
    if llm_names:
        # LLM 결과를 fuzzy 매칭
        matched, seen_tickers = [], set()
        for name in llm_names:
            m = fuzzy_search(name, stock_db, threshold=0.55)
            if m:
                ticker, sname, market, score = m
                if ticker in seen_tickers: continue
                seen_tickers.add(ticker)
                matched.append({
                    'ticker': ticker, 'name': sname, 'market': market,
                    'quantity': 0, 'price': 0,
                    'confidence': round(min(score, 1.0), 2),
                    'raw_ocr': name,
                    'method': 'llm'
                })
        return matched
    
    # 2. LLM 실패 시 기존 규칙 기반 fallback
    raw = extract_stocks_from_ocr_results(ocr_results)
    matched, seen_tickers = [], set()
    for stock in raw:
        m = fuzzy_search(stock['name'], stock_db, threshold=0.65)
        if m:
            ticker, sname, market, score = m
            if ticker in seen_tickers: continue
            seen_tickers.add(ticker)
            matched.append({
                'ticker': ticker, 'name': sname, 'market': market,
                'quantity': stock['qty'],
                'price': stock['price'],
                'confidence': round(min(score, 1.0), 2),
                'raw_ocr': stock['name'],
                'method': 'rule'
            })
    return matched
