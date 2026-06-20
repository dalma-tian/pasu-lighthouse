"""파수의 등대 — 뉴스 크롤러 (구글 RSS + 네이버 금융 HTML)"""
import urllib.request
import xml.etree.ElementTree as ET
import sqlite3
import os
import re
from html import unescape
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'pasu.db')
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=%EA%B2%BD%EC%A0%9C+%EA%B8%88%EC%9C%B5+%EC%A6%9D%EC%8B%9C&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=economy+finance+stock+market&hl=en&gl=US&ceid=US:en",
]

NAVER_URLS = [
    ("네이버금융", "https://finance.naver.com/news/mainnews.nhn"),
    ("네이버시황", "https://finance.naver.com/news/news_list.nhn?mode=LSS2D&section_id=101&section_id2=258"),
    ("네이버종목", "https://finance.naver.com/news/news_list.nhn?mode=LSS3D&section_id=101&section_id2=258&section_id3=300"),
    ("네이버국제", "https://finance.naver.com/news/news_list.nhn?mode=LSS2D&section_id=101&section_id2=259"),
    ("네이버증권", "https://finance.naver.com/news/news_list.nhn?mode=LSS3D&section_id=101&section_id2=258&section_id3=301"),
]


def parse_pubdate(pubdate_str):
    if not pubdate_str:
        return datetime.now(timezone.utc).isoformat()
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(pubdate_str).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def extract_source(title):
    m = re.search(r'[-–—]\s*([^\s-]+)$', title)
    if m:
        return m.group(1).strip()
    return '구글뉴스'


def clean_title(raw):
    title = re.sub(r'\s*[-–—]\s*[^\s-]+$', '', raw).strip()
    return unescape(title)


def is_english(text):
    """텍스트가 영문인지 감지 (한글 없고 ASCII 위주)"""
    has_korean = bool(re.search(r'[가-힣]', text))
    ascii_ratio = sum(1 for c in text if ord(c) < 128) / max(len(text), 1)
    return not has_korean and ascii_ratio > 0.7


def translate_title(english_title):
    """영문 제목 → 한글 번역 (원문)"""
    try:
        from deep_translator import GoogleTranslator
        t = GoogleTranslator(source='en', target='ko')
        ko = t.translate(english_title)
        if ko and ko != english_title:
            return f"{ko} ({english_title})"
    except Exception:
        pass
    return english_title


def crawl_google(db):
    """구글 뉴스 RSS → 실제 출처 + 한글 번역"""
    new_count = 0
    for feed_url in RSS_FEEDS:
        try:
            req = urllib.request.Request(feed_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode('utf-8', errors='replace')
            root = ET.fromstring(content)
            for item in root.findall('.//item'):
                title_el = item.find('title')
                link_el = item.find('link')
                pubdate_el = item.find('pubDate')
                source_el = item.find('source')
                if title_el is None or not title_el.text:
                    continue
                raw = title_el.text.strip()
                # 실제 출처 추출
                source = extract_source(raw)
                # 구글뉴스 폴백: <source> 태그 사용
                if source == '구글뉴스' and source_el is not None and source_el.text:
                    source = source_el.text.strip()
                title = clean_title(raw)
                # 영문 → 번역 (메모리 문제로 일시 비활성화. OpenAI 크레딧 받은 후 적용 예정)
                # if is_english(title):
                #     title = translate_title(title)
                link = link_el.text.strip() if link_el is not None and link_el.text else ''
                published_at = parse_pubdate(pubdate_el.text if pubdate_el is not None else None)
                if not link:
                    continue
                exists = db.execute('SELECT id FROM news WHERE link = ?', (link,)).fetchone()
                if exists:
                    continue
                from scorer import score, to_stars
                imp = score(title, source, published_at)
                stars = to_stars(imp)
                db.execute(
                    'INSERT INTO news (title, link, source, published_at, importance, stars) VALUES (?,?,?,?,?,?)',
                    (title, link, source, published_at, imp, stars)
                )
                new_count += 1
        except Exception as e:
            print(f"[ERR] Google RSS: {e}")
    return new_count


def extract_press(summary_html):
    """<dd class=articleSummary>에서 언론사명 추출"""
    # news_list.nhn: <span class="press">언론사</span>
    m = re.search(r'<span class="press">(.*?)</span>', summary_html)
    if m:
        return m.group(1).strip()
    # mainnews.nhn: 일반 텍스트, '|' 기준으로 언론사명 찾기
    text = re.sub(r'<[^>]+>', '', summary_html).strip()
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    # 패턴: ... 요약문, 언론사, |, 날짜
    for i in range(len(lines)-1, -1, -1):
        if re.match(r'\d{4}-\d{2}-\d{2}', lines[i]):
            if i >= 2 and lines[i-1] == '|':
                return lines[i-2]
            elif i >= 1:
                return lines[i-1]
    # fallback: <span class="bar">|</span> 패턴
    m2 = re.search(r'<span class="bar">\|</span>', summary_html)
    if m2:
        before_bar = summary_html[:m2.start()]
        text_before = re.sub(r'<[^>]+>', '', before_bar).strip()
        parts = [p.strip() for p in text_before.split('\n') if p.strip()]
        if parts:
            return parts[-1]
    return '네이버금융'


def convert_link(raw_href):
    """구형 링크(/news/news_read.naver?...) → n.news.naver.com 신형 링크"""
    from urllib.parse import urlparse, parse_qs
    if 'n.news.naver.com' in raw_href:
        return raw_href
    if '/news/news_read.' in raw_href:
        qs = parse_qs(urlparse(raw_href).query)
        article_id = qs.get('article_id', [None])[0]
        office_id = qs.get('office_id', [None])[0]
        if article_id and office_id:
            return f'https://n.news.naver.com/mnews/article/{office_id}/{article_id}'
    return 'https://finance.naver.com' + raw_href.replace('&amp;', '&')


def crawl_naver(db):
    """네이버 금융 HTML 파싱 — 언론사명 + 신형 링크 (5개 섹션)"""
    new_count = 0
    for source_label, url in NAVER_URLS:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('euc-kr', errors='replace')

            # <dl> 블록 단위로 파싱 (articleSubject + articleSummary 짝)
            dl_blocks = re.findall(r'<dl>(.*?)</dl>', html, re.DOTALL)
            for dl_html in dl_blocks:
                subject_match = re.search(
                    r'<dd class="articleSubject">(.*?)</dd>',
                    dl_html, re.DOTALL
                )
                summary_match = re.search(
                    r'<dd class="articleSummary">(.*?)</dd>',
                    dl_html, re.DOTALL
                )
                if not subject_match:
                    continue

                a_match = re.search(
                    r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>',
                    subject_match.group(1), re.DOTALL
                )
                if not a_match:
                    continue

                title = unescape(re.sub(r'<[^>]+>', '', a_match.group(2).strip()))
                if not title or len(title) < 6:
                    continue

                link = convert_link(a_match.group(1))
                press = extract_press(summary_match.group(1)) if summary_match else source_label

                exists = db.execute('SELECT id FROM news WHERE link = ?', (link,)).fetchone()
                if exists:
                    continue

                published_at = datetime.now(timezone.utc).isoformat()
                from scorer import score, to_stars
                imp = score(title, press, published_at)
                stars = to_stars(imp)
                db.execute(
                    'INSERT INTO news (title, link, source, published_at, importance, stars) VALUES (?,?,?,?,?,?)',
                    (title, link, press, published_at, imp, stars)
                )
                new_count += 1
        except Exception as e:
            print(f"[ERR] Naver {source_label}: {e}")
    return new_count


def crawl_watchlist_news(db):
    """워치리스트 종목별 뉴스 수집 — 각 종목명으로 Google News 검색"""
    import urllib.parse
    import time
    
    stocks = db.execute('SELECT name, ticker FROM watchlist').fetchall()
    if not stocks:
        print("[watchlist-news] 관심종목 없음, 건너뜀")
        return 0
    
    new_count = 0
    for name, ticker in stocks:
        # 검색어: "종목명 주식" (ex: 삼성전자 주식)
        query = f"{name} 주식"
        encoded = urllib.parse.quote(query)
        feed_url = f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"
        
        try:
            req = urllib.request.Request(feed_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode('utf-8', errors='replace')
            root = ET.fromstring(content)
            
            added_for_stock = 0
            for item in root.findall('.//item'):
                title_el = item.find('title')
                link_el = item.find('link')
                pubdate_el = item.find('pubDate')
                source_el = item.find('source')
                
                if title_el is None or not title_el.text:
                    continue
                
                raw = title_el.text.strip()
                source = extract_source(raw)
                if source == '구글뉴스' and source_el is not None and source_el.text:
                    source = source_el.text.strip()
                title = clean_title(raw)
                link = link_el.text.strip() if link_el is not None and link_el.text else ''
                if not link:
                    continue
                
                published_at = parse_pubdate(pubdate_el.text if pubdate_el is not None else None)
                
                # 중복 체크
                exists = db.execute('SELECT id FROM news WHERE link = ?', (link,)).fetchone()
                if exists:
                    continue
                
                from scorer import score, to_stars
                imp = score(title, source, published_at)
                stars = to_stars(imp)
                db.execute(
                    'INSERT INTO news (title, link, source, published_at, importance, stars) VALUES (?,?,?,?,?,?)',
                    (title, link, source, published_at, imp, stars)
                )
                added_for_stock += 1
            
            if added_for_stock > 0:
                print(f"[watchlist-news] {name}: {added_for_stock}건")
            new_count += added_for_stock
            
            # Rate limit: Google News에 연속 요청 방지
            time.sleep(1.5)
            
        except Exception as e:
            print(f"[watchlist-news] {name} 크롤링 실패: {e}")
    
    return new_count


def crawl():
    db = sqlite3.connect(DB_PATH)
    n_google = crawl_google(db)
    n_naver = crawl_naver(db)
    n_watchlist = crawl_watchlist_news(db)
    db.commit()
    total = n_google + n_naver + n_watchlist
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Google:{n_google} + Naver:{n_naver} + Watchlist:{n_watchlist} = {total} new")
    db.close()
    return total


if __name__ == '__main__':
    crawl()
