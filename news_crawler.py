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
                # 영문 → 번역
                if is_english(title):
                    title = translate_title(title)
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


def crawl_naver(db):
    """네이버 금융 HTML 파싱 (5개 섹션)"""
    new_count = 0
    for source_label, url in NAVER_URLS:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('euc-kr', errors='replace')

            items = re.findall(
                r'<a\s+href="(/news/news_read[^"]+)"[^>]*>(.*?)</a>',
                html, re.DOTALL
            )
            for href, text in items:
                title = unescape(re.sub(r'<[^>]+>', '', text).strip())
                if not title or len(title) < 6:
                    continue
                link = 'https://finance.naver.com' + href.replace('&amp;', '&')
                exists = db.execute('SELECT id FROM news WHERE link = ?', (link,)).fetchone()
                if exists:
                    continue
                published_at = datetime.now(timezone.utc).isoformat()
                from scorer import score, to_stars
                imp = score(title, source_label, published_at)
                stars = to_stars(imp)
                db.execute(
                    'INSERT INTO news (title, link, source, published_at, importance, stars) VALUES (?,?,?,?,?,?)',
                    (title, link, source_label, published_at, imp, stars)
                )
                new_count += 1
        except Exception as e:
            print(f"[ERR] Naver {source_label}: {e}")
    return new_count


def crawl():
    db = sqlite3.connect(DB_PATH)
    n_google = crawl_google(db)
    n_naver = crawl_naver(db)
    db.commit()
    total = n_google + n_naver
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Google:{n_google} + Naver:{n_naver} = {total} new")
    db.close()
    return total


if __name__ == '__main__':
    crawl()
