"""
포트폴리오 스크린샷 OCR → 종목명 + 보유수량 + 현재가 추출 + stocks.csv 매칭
EasyOCR + 3,004종목 DB 퍼지매칭. KRX 모바일 + HTS 모두 지원.
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
        
        # 우선주 패널티 (한국금융지주 > 한국금융지주우)
        if '우' in sc and '우' not in nc:
            bonus -= 0.15
        
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


def _parse_num(t):
    """텍스트에서 숫자 추출 (쉼표, 마이너스 처리)"""
    t = t.replace(',', '').replace('~', '-').replace('D', '0').replace('O', '0')
    t = re.sub(r'[^0-9\-]', '', t)
    try: return int(t)
    except: return None


def extract_stocks_from_ocr_results(ocr_results):
    """
    모든 row에서 (종목명, 보유수량, 현재가) 추출.
    보유수량 = row에서 가장 작은 숫자 (1~1000)
    현재가 = row에서 가장 오른쪽 큰 숫자
    """
    items = _make_items(ocr_results)
    if not items: return []
    
    # 2-pass row grouping
    rows_14 = _group_rows(items, 14)
    rows_22 = _group_rows(items, 22)
    all_rows = rows_14 + rows_22
    
    seen_names = set()
    result = []
    
    for row in all_rows:
        row.sort(key=lambda it: it['x'])
        
        # 숫자들만 추출
        nums = []
        for it in row:
            val = _parse_num(it['text'])
            if val is not None and 0 < val < 9999999:
                nums.append({'val': val, 'x': it['x'], 'raw': it['text']})
        
        if not nums:
            continue
        
        # 보유수량 = 가장 작은 숫자 (1~5000)
        small_nums = [n for n in nums if 1 <= n['val'] <= 5000]
        qty = min(small_nums, key=lambda n: n['val']) if small_nums else None
        
        # 현재가 = 가장 오른쪽에 있는 4~7자리 숫자
        right_nums = sorted(nums, key=lambda n: -n['x'])
        price = None
        for n in right_nums:
            if 1000 <= n['val'] <= 9999999:
                price = n['val']
                break
        
        # 종목명
        qty_x = qty['x'] if qty else 99999
        name_parts = [it['text'] for it in row if it['x'] < qty_x and _looks_like_stock(it['text'])]
        
        # fallback: 수량 없으면 row의 가장 왼쪽 텍스트
        if not name_parts:
            name_parts = [it['text'] for it in row if _looks_like_stock(it['text'])]
        
        if not name_parts:
            continue
        
        name = ' '.join(name_parts)
        key = name.strip().upper()
        if key in seen_names: continue
        seen_names.add(key)
        
        result.append({
            'name': name,
            'qty': qty['val'] if qty else 0,
            'price': price or 0,
        })
    
    # Fallback: 왼쪽 30% 영역에서 종목명만 추출
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


def process_portfolio_image(image_path, stock_db=None):
    import easyocr, numpy as np
    from PIL import Image
    
    if stock_db is None: stock_db = load_stock_db()
    
    img = Image.open(image_path)
    w, h = img.size
    if min(w, h) < 1200:
        img = img.resize((w * 2, h * 2), Image.LANCZOS)
    
    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    results = reader.readtext(np.array(img))
    raw = extract_stocks_from_ocr_results(results)
    
    matched, seen_tickers = [], set()
    for stock in raw:
        m = fuzzy_search(stock['name'], stock_db)
        if m:
            ticker, sname, market, score = m
            if ticker in seen_tickers: continue
            seen_tickers.add(ticker)
            matched.append({
                'ticker': ticker, 'name': sname, 'market': market,
                'quantity': stock['qty'],
                'price': stock['price'],
                'confidence': round(min(score, 1.0), 2),
                'raw_ocr': stock['name']
            })
    return matched
