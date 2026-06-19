"""
포트폴리오 스크린샷 OCR → 종목명 추출 + stocks.csv 매칭
EasyOCR으로 한글 인식 후, 3,004종목 DB와 퍼지 매칭
"""
import csv
import re
import os
from difflib import SequenceMatcher

# stocks.csv 경로 (Flask 기준)
STOCKS_CSV = os.path.join(os.path.dirname(__file__), 'data', 'stocks.csv')

# 종목명 정규식: ETF/종목 패턴들
STOCK_NAME_PATTERNS = [
    # 일반적인 한글+영문 ETF 종목명 (예: ACE 글로벌반도체TOP4)
    r'[A-Za-z]+\s*[가-힣A-Za-z0-9]+(?:TOP\d*|액티브|플러스|\+)?',
    r'[가-힣]+\s*[A-Za-z0-9]+',
]

# 수량 패턴 (잔고란에 나오는 정수)
QTY_PATTERN = re.compile(r'\b(\d{1,3}(?:,\d{3})*)\b')

# 무시할 행 (헤더/메타데이터)
IGNORE_KEYWORDS = [
    '주식실시간잔고', '총 평가손익', '총매입금액', '총평가금액', '추정자산',
    '실현손익', '예수금', '매매단가', '평가손익', '수익률', '현재가',
    '종목명', '잔고', '구분', '가능', '거래내역', '관심 종목',
    '주식 현재가', '주식 주문', '주식 잔고', '모의', 'KRX',
]

def load_stock_db(csv_path=None):
    """stocks.csv → [(ticker, name, market), ...] 로드"""
    if csv_path is None:
        csv_path = STOCKS_CSV
    stocks = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stocks.append((row['ticker'], row['name'], row.get('market', '')))
    return stocks


def fuzzy_search(name, stock_db, threshold=0.5):
    """OCR로 추출된 종목명과 stocks.csv를 퍼지 매칭 + substring 보너스"""
    best_score = 0
    best_match = None
    name_clean = name.strip().upper()
    name_short = re.sub(r'\s+', '', name_clean)
    
    for ticker, stock_name, market in stock_db:
        stock_clean = stock_name.strip().upper()
        stock_short = re.sub(r'\s+', '', stock_clean)
        
        # SequenceMatcher 점수
        seq_score = SequenceMatcher(None, name_clean, stock_clean).ratio()
        
        # Substring 보너스: OCR 텍스트가 종목명에 포함되거나 그 반대
        sub_bonus = 0
        if len(name_short) >= 3 and name_short in stock_short:
            sub_bonus = 0.2
        elif len(stock_short) >= 3 and stock_short in name_short:
            sub_bonus = 0.15
        
        # 짧은 단어 매칭 보너스 (예: "CD금리액티브" → "CD금리액티브(합성)")
        if len(name_short) >= 5:
            # 종목명에서 괄호/접미사 떼고 비교
            stock_base = re.sub(r'\([^)]*\)|Plus$|액티브$', '', stock_short)
            name_base = re.sub(r'\([^)]*\)|Plus$|액티브$', '', name_short)
            if name_base and stock_base:
                base_score = SequenceMatcher(None, name_base, stock_base).ratio()
                seq_score = max(seq_score, base_score)
        
        total_score = seq_score + sub_bonus
        if total_score > best_score:
            best_score = total_score
            best_match = (ticker, stock_name, market, total_score)
    
    if best_score >= threshold:
        return best_match
    return None


# ETF 접두사 브랜드 (이름이 분리될 경우 병합)
ETF_PREFIXES = ['KODEX', 'TIGER', 'ACE', 'TIME', 'HANARO', 'RISE', 'SOL', 'KoAct',
                'KB', 'KIWOOM', '1Q', 'PLUS', 'ARIRANG', 'KBSTAR', 'KINDEX',
                'MASTER', 'NH-Amundi', 'TREX', 'WOORI', 'FOCUS', 'TIMEFOLIO',
                'BNK', 'DB', 'HANA', 'IBK', 'KCGI', 'KTB', 'MERITZ', 'MIREA',
                'NAVER', 'Samsung', 'Shinhan', 'SMART', 'TIGER ETF']

STOCK_NAME_CHARS = re.compile(r'[A-Za-z0-9가-힣&()+.,%\-\s]+')

def _is_stock_name(text):
    """주식 종목명으로 보이는지 확인 (요약/헤더 제외)"""
    t = text.strip()
    if len(t) < 3:
        return False
    if any(kw in t for kw in IGNORE_KEYWORDS):
        return False
    # 순수 숫자만 있는 건 제외
    if re.match(r'^[\d,.\-+%]+$', t):
        return False
    # 종목명에 포함될 법한 문자 구성인지
    return bool(STOCK_NAME_CHARS.fullmatch(t))


def extract_stocks_from_ocr_results(ocr_results):
    """
    EasyOCR 결과 → 종목명+수량 추출.
    반환: [(종목명_raw, 수량), ...]
    """
    # y좌표 기준 정렬
    sorted_results = sorted(ocr_results, key=lambda r: (r[0][0][1], r[0][0][0]))
    
    # 유효한 텍스트만 (위치 정보 포함)
    items = []
    for bbox, text, conf in sorted_results:
        if conf < 0.2:
            continue
        clean = text.strip()
        if len(clean) <= 1:
            continue
        if any(kw in clean for kw in IGNORE_KEYWORDS):
            continue
        # 순수 숫자/기호만 있는 것도 제외하지 않음 (수량/가격 데이터로 필요)
        x_center = (bbox[0][0] + bbox[2][0]) / 2
        y_center = (bbox[0][1] + bbox[2][1]) / 2
        items.append({
            'text': clean,
            'x': x_center,
            'y': y_center,
            'w': bbox[2][0] - bbox[0][0],
            'h': bbox[2][1] - bbox[0][1],
            'conf': conf
        })
    
    # 행(row) 그룹핑: y좌표 차이가 폰트 크기의 1.5배 이내면 같은 행
    if not items:
        return []
    
    avg_h = sum(it['h'] for it in items) / len(items)
    row_threshold = max(avg_h * 1.5, 20)
    
    rows = []
    current_row = [items[0]]
    
    for item in items[1:]:
        if abs(item['y'] - current_row[-1]['y']) <= row_threshold:
            current_row.append(item)
        else:
            rows.append(current_row)
            current_row = [item]
    rows.append(current_row)
    
    # 각 행 내에서 x좌표 순으로 정렬
    for row in rows:
        row.sort(key=lambda it: it['x'])
    
    # 행들을 순회하며 종목명+수량 쌍 찾기
    # 패턴: [종목명 파트들...] [수량(50-9999)] [매입단가] [평가손익] ...
    stocks = []
    i = 0
    while i < len(rows):
        row = rows[i]
        row_texts = [it['text'] for it in row]
        
        # 수량 찾기 (첫 번째 50-9999 범위의 정수)
        qty = None
        qty_pos = None
        for pos, item in enumerate(row):
            t = item['text'].replace(',', '')
            if re.match(r'^\d{2,4}$', t):
                val = int(t)
                if 50 <= val <= 9999:
                    qty = val
                    qty_pos = pos
                    break
        
        if qty is None:
            i += 1
            continue
        
        # 종목명: 현재 행에서 수량보다 왼쪽(x좌표)에 있는 텍스트들만 수집
        name_parts = []
        for item in row[:qty_pos]:
            t = item['text']
            # 한글/영문이 하나라도 포함된 텍스트만 종목명 후보
            if re.search(r'[가-힣A-Za-z]', t):
                name_parts.append(t)
        
        if not name_parts:
            # 수량 왼쪽에 종목명이 없으면, 같은 행에서 수량 왼쪽 + 이전 행 전체에서 검색
            for item in row[:qty_pos]:
                if re.search(r'[가-힣A-Za-z]', item['text']):
                    name_parts.append(item['text'])
            if not name_parts and i > 0:
                prev_row = rows[i-1]
                for item in prev_row:
                    if re.search(r'[가-힣A-Za-z]', item['text']):
                        name_parts.append(item['text'])
        
        if not name_parts:
            i += 1
            continue
        
        raw_name = ' '.join(name_parts)
        
        # ETF 접두사 병합
        if len(name_parts) >= 2:
            last_prefix = None
            merged = []
            for part in name_parts:
                part_upper = part.upper().strip()
                is_prefix = any(part_upper == p.upper() for p in ETF_PREFIXES)
                if is_prefix:
                    last_prefix = part
                else:
                    if last_prefix and not part_upper.startswith(last_prefix.upper()):
                        merged.append(f"{last_prefix} {part}")
                        last_prefix = None
                    else:
                        if last_prefix:
                            merged.append(last_prefix)
                            last_prefix = None
                        merged.append(part)
            if last_prefix:
                merged.append(last_prefix)
            raw_name = ' '.join(merged)
        
        stocks.append((raw_name, qty))
        i += 1
    
    return stocks


def process_portfolio_image(image_path, stock_db=None):
    """
    포트폴리오 이미지 → 매칭된 종목 리스트
    반환: [(ticker, name, qty, confidence), ...]
    """
    import easyocr
    
    if stock_db is None:
        stock_db = load_stock_db()
    
    # EasyOCR 실행 (한국어+영어)
    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    results = reader.readtext(image_path)
    
    # 종목 추출
    raw_stocks = extract_stocks_from_ocr_results(results)
    
    # stocks.csv와 매칭
    matched = []
    for raw_name, qty in raw_stocks:
        match = fuzzy_search(raw_name, stock_db)
        if match:
            ticker, name, market, score = match
            matched.append({
                'ticker': ticker,
                'name': name,
                'market': market,
                'quantity': qty,
                'confidence': round(score, 2),
                'raw_ocr': raw_name
            })
    
    return matched
