"""
포트폴리오 스크린샷 OCR → 종목명 추출 + stocks.csv 매칭
EasyOCR + 3,004종목 DB 퍼지매칭. KRX 모바일 + HTS 모두 지원.

전략: 2-pass 추출 (tight threshold + loose threshold) → 결과 병합.
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
    'KOSPI', 'KOSDAQ', '현금', '자동입력',
}


def load_stock_db(csv_path=None):
    if csv_path is None: csv_path = STOCKS_CSV
    stocks = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            stocks.append((row['ticker'], row['name'], row.get('market', '')))
    return stocks


def fuzzy_search(name, stock_db, threshold=0.5):
    best_score, best_match = 0, None
    nc = name.strip().upper()
    ns = re.sub(r'\s+', '', nc)
    for ticker, sn, market in stock_db:
        sc = sn.strip().upper()
        ss = re.sub(r'\s+', '', sc)
        score = SequenceMatcher(None, nc, sc).ratio()
        bonus = 0
        if len(ns) >= 3 and ns in ss: bonus = 0.25
        elif len(ss) >= 3 and ss in ns: bonus = 0.2
        if len(ns) >= 4:
            sb = re.sub(r'\([^)]*\)|Plus$|액티브$|합성$', '', ss)
            nb = re.sub(r'\([^)]*\)|Plus$|액티브$|합성$', '', ns)
            if nb and sb and len(nb) >= 3:
                score = max(score, SequenceMatcher(None, nb, sb).ratio())
        # Prefer longer names (avoid matching "1Q" prefix when "KODEX" exists)
        total = score + bonus
        # Tie-break: prefer well-known ETF brands over minor ones
        if total > best_score or (best_match is not None and abs(total - best_score) < 0.10):
            # Prefer KODEX/TIGER/ACE/TIME over 1Q/KIWOOM etc
            preferred = ['KODEX ', 'TIGER ', 'ACE ', 'TIME ', 'HANARO ', 'RISE ', 'SOL ']
            if best_match is not None and abs(total - best_score) < 0.10:
                old_pref = any(best_match[1].upper().startswith(p) for p in preferred)
                new_pref = any(sn.upper().startswith(p) for p in preferred)
                if old_pref and not new_pref:
                    continue  # keep old match
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
    # 1글자 한글은 무시 (예: "관", "심")
    if re.match(r'^[가-힣]$', t): return False
    return bool(re.search(r'[가-힣]|[A-Za-z]{2,}', t))


def _make_items(ocr_results):
    """OCR 결과 → 정제된 아이템 리스트 (x, y, text)"""
    items = []
    for bbox, text, conf in sorted(ocr_results, key=lambda r: (r[0][0][1], r[0][0][0])):
        if conf < 0.15: continue
        clean = text.strip()
        if len(clean) <= 1 and not clean.isdigit(): continue
        if clean in IGNORE_TEXTS: continue
        # "X 아이콘" 같이 의미없는 단일 영문자
        if len(clean) == 1 and clean.isalpha() and clean not in 'AI': continue
        items.append({
            'text': clean,
            'x': (bbox[0][0] + bbox[2][0]) / 2,
            'y': (bbox[0][1] + bbox[2][1]) / 2,
            'conf': conf
        })
    return items


def _group_rows(items, threshold):
    """y좌표 기준 행 그룹핑"""
    if not items: return []
    rows, cur = [], [items[0]]
    for it in items[1:]:
        if abs(it['y'] - cur[-1]['y']) <= threshold:
            cur.append(it)
        else:
            rows.append(cur)
            cur = [it]
    rows.append(cur)
    return rows


def _extract_pass(items, row_threshold, qty_min=1):
    """한 번의 패스로 종목 추출. (종목명_왼쪽, 수량_오른쪽)"""
    rows = _group_rows(items, row_threshold)
    stocks = []
    
    for row in rows:
        row.sort(key=lambda it: it['x'])
        
        # 수량 찾기 (qty_min ~ 99999)
        qty, qty_pos = None, None
        for pos, it in enumerate(row):
            t = it['text'].replace(',', '')
            if re.match(r'^\d{1,5}$', t):
                val = int(t)
                if qty_min <= val <= 99999:
                    qty = val
                    qty_pos = pos
                    break
        
        if qty is None:
            continue
        
        # 종목명: 수량 왼쪽
        parts = [it['text'] for it in row[:qty_pos] if _looks_like_stock(it['text'])]
        if not parts:
            continue
        
        name = ' '.join(parts)
        stocks.append((name, qty))
    
    return stocks


def extract_stocks_from_ocr_results(ocr_results):
    """
    2-pass 추출:
    Pass 1: tight threshold (14px) → 작은 수량도 허용
    Pass 2: loose threshold (22px) → 50+ 수량
    
    + 수량 없는 종목도 이름만 추출하는 fallback
    결과 병합 (중복 제거)
    """
    items = _make_items(ocr_results)
    if not items:
        return []
    
    all_stocks = []
    
    # Pass 1: tight (HTS)
    s1 = _extract_pass(items, row_threshold=14, qty_min=1)
    all_stocks.extend(s1)
    
    # Pass 2: loose (KRX mobile)
    s2 = _extract_pass(items, row_threshold=22, qty_min=50)
    all_stocks.extend(s2)
    
    # Fallback: 수량 없는 종목명도 추출 (HTS에서 보유수량 인식 실패 대비)
    # 가장 왼쪽 영역(x < 전체 너비의 30%)에서 종목명 추출
    max_x = max(it['x'] for it in items) if items else 500
    left_items = sorted(
        [it for it in items if it['x'] < max_x * 0.3 and _looks_like_stock(it['text'])],
        key=lambda it: it['y']
    )
    # y좌표로 그룹핑하여 연속된 텍스트 병합
    if left_items:
        groups, cur = [], [left_items[0]]
        for it in left_items[1:]:
            if it['y'] - cur[-1]['y'] <= 20:
                cur.append(it)
            else:
                groups.append(cur); cur = [it]
        groups.append(cur)
    
    # ETF 단독 접두사 (종목명의 일부로만 의미있음)
    SOLO_PREFIXES = {'ACE', 'TIGER', 'KODEX', 'TIME', 'TIIME', 'HANARO', 'RISE', 'SOL', 
                     'KoAct', 'KIWOOM', '1Q', 'PLUS', 'KB', 'TIGER ETF'}
    
    for grp in groups:
            grp.sort(key=lambda it: it['x'])
            name = ' '.join(it['text'] for it in grp)
            # 단독 ETF 접두사만 있는 경우 스킵
            if name.strip().upper() in SOLO_PREFIXES:
                continue
            all_stocks.append((name, 0))
    
    # 중복 제거
    seen, result = set(), []
    for name, qty in all_stocks:
        key = name.strip().upper()
        if key not in seen:
            seen.add(key)
            result.append((name, qty))
    
    return result


def process_portfolio_image(image_path, stock_db=None):
    import easyocr
    if stock_db is None: stock_db = load_stock_db()
    
    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    results = reader.readtext(image_path)
    raw = extract_stocks_from_ocr_results(results)
    
    matched, seen_tickers = [], set()
    for name, qty in raw:
        m = fuzzy_search(name, stock_db)
        if m:
            ticker, sname, market, score = m
            if ticker in seen_tickers: continue
            seen_tickers.add(ticker)
            matched.append({
                'ticker': ticker, 'name': sname, 'market': market,
                'quantity': qty, 'confidence': round(min(score, 1.0), 2),
                'raw_ocr': name
            })
    return matched
