"""파수의 등대 — 뉴스 크롤러 (구글 뉴스 RSS + 네이버 금융 백업)"""
import urllib.request
import xml.etree.ElementTree as ET
import sqlite3
import os
import re
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'pasu.db')
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ▸ RSS 소스 목록
RSS_FEEDS = [
    # 구글 뉴스 — 한국 경제
    "https://news.google.com/rss/search?q=%EA%B2%BD%EC%A0%9C+%EA%B8%88%EC%9C%B5+%EC%A6%9D%EC%8B%9C&hl=ko&gl=KR&ceid=KR:ko",
    # 구글 뉴스 — 글로벌 경제 (영문)
    "https://news.google.com/rss/search?q=economy+finance+stock+market&hl=en&gl=US&ceid=US:en",
]


def parse_pubdate(pubdate_str):
    """RSS pubDate 파싱 → ISO 포맷"""
    if not pubdate_str:
        return datetime.now(timezone.utc).isoformat()
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(pubdate_str).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def extract_source(title):
    """제목에서 출처 추출 (구글 뉴스 형식: '제목 - 출처')"""
    m = re.search(r'[-–—]\s*([^\s-]+)$', title)
    if m:
        return m.group(1).strip()
    return '구글뉴스'


def extract_clean_title(title):
    """'제목 - 출처' → 제목만"""
    return re.sub(r'\s*[-–—]\s*[^\s-]+$', '', title).strip()


def crawl():
    """모든 RSS 피드에서 뉴스 수집 → DB 저장"""
    db = sqlite3.connect(DB_PATH)
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

                if title_el is None or not title_el.text:
                    continue

                raw_title = title_el.text.strip()
                title = extract_clean_title(raw_title)
                source = extract_source(raw_title)
                link = link_el.text.strip() if link_el is not None and link_el.text else ''
                published_at = parse_pubdate(pubdate_el.text if pubdate_el is not None else None)

                # 중복 체크 (link 기준)
                exists = db.execute(
                    'SELECT id FROM news WHERE link = ?', (link,)
                ).fetchone()
                if exists:
                    continue

                # 중요도 점수 계산
                from scorer import score, to_stars
                importance = score(title, source, published_at)
                stars = to_stars(importance)

                db.execute(
                    '''INSERT INTO news (title, link, source, published_at, importance, stars)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (title, link, source, published_at, importance, stars)
                )
                new_count += 1

        except Exception as e:
            print(f"[ERROR] {feed_url[:60]}: {e}")

    db.commit()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {new_count} new articles")
    db.close()
    return new_count


if __name__ == '__main__':
    crawl()
