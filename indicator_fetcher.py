"""파수의 등대 — 경제지표 수집기 (FRED + ECOS + 네이버 + 무료API)"""
import urllib.request
import json
import re
import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'pasu.db')
HEADERS = {"User-Agent": "Mozilla/5.0"}
FRED_KEY = "4540566a460d045bc28db02191084b21"
ECOS_KEY = "KYL8SRKT2V4NHZCJ6OTW"


def fetch_fred(series_id):
    """FRED API → 최신 값 + 변화량"""
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_KEY}&file_type=json&sort_order=desc&limit=2"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    obs = data["observations"]
    if not obs:
        return 0, 0
    latest = obs[0]
    prev = obs[1] if len(obs) > 1 else {"value": "0"}
    try:
        val = float(latest["value"])
        pval = float(prev["value"])
        chg = round(val - pval, 2) if pval != 0 else 0
        return val, chg
    except (ValueError, KeyError):
        return 0, 0


def fetch_fred_history(series_id):
    """FRED API → 최근 30건 시계열 (날짜, 값)"""
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_KEY}&file_type=json&sort_order=desc&limit=30"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    obs = data.get("observations", [])
    history = []
    for o in obs:
        try:
            history.append((o["date"], float(o["value"])))
        except (ValueError, KeyError):
            continue
    return history


def fetch_kospi():
    """네이버 금융 → KOSPI 지수"""
    url = "https://finance.naver.com/sise/sise_index.nhn?code=KOSPI"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as r:
        html = r.read().decode("euc-kr", errors="replace")
    m = re.search(r'id="now_value">([0-9,.]+)</em>', html)
    chg = re.search(r'id="change_value">([0-9,.]+)</em>', html)
    if m:
        val = float(m.group(1).replace(",", ""))
        c = float(chg.group(1).replace(",", "")) if chg else 0
        return val, c
    return 0, 0


def fetch_usdkrw():
    """무료 환율 API"""
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    return data["rates"]["KRW"], 0


def fetch_ecos():
    """한국은행 ECOS → 기준금리"""
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{ECOS_KEY}/json/kr/1/1/722Y001/A/2025/2026/0101000"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    rows = data["StatisticSearch"]["row"]
    if rows:
        latest = rows[-1]
        return float(latest["DATA_VALUE"]), 0
    return 0, 0


def fetch_indicators():
    """6개 핵심 지표 수집 → DB 저장 (현재값 + 히스토리 30건)"""
    indicators = []
    history_bulk = []  # (name, value, date)

    # FRED 3종 — 현재값 + 30건 히스토리
    for series_id, name in [("FEDFUNDS", "미국 기준금리"), ("SP500", "S&P500"), ("DCOILWTICO", "WTI 유가")]:
        try:
            val, chg = fetch_fred(series_id)
            indicators.append((name, val, chg))
            # 히스토리 30건
            hist = fetch_fred_history(series_id)
            for date_str, hval in hist:
                history_bulk.append((name, hval, date_str))
        except Exception as e:
            print(f"[ERR] FRED {name}: {e}")

    # ECOS: 한국 기준금리
    try:
        val, chg = fetch_ecos()
        indicators.append(("한국 기준금리", val, chg))
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        history_bulk.append(("한국 기준금리", val, now_str))
    except Exception as e:
        print(f"[ERR] ECOS: {e}")

    # KOSPI
    try:
        val, chg = fetch_kospi()
        indicators.append(("KOSPI", val, chg))
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        history_bulk.append(("KOSPI", val, now_str))
    except Exception as e:
        print(f"[ERR] KOSPI: {e}")

    # 환율
    try:
        val, chg = fetch_usdkrw()
        indicators.append(("원/달러 환율", val, chg))
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        history_bulk.append(("원/달러 환율", val, now_str))
    except Exception as e:
        print(f"[ERR] 환율: {e}")

    # DB 저장
    db = sqlite3.connect(DB_PATH)
    now = datetime.now(timezone.utc).isoformat()

    # 현재값 upsert
    for name, val, chg in indicators:
        db.execute(
            "INSERT OR REPLACE INTO indicators (name, value, change_pct, updated_at) VALUES (?, ?, ?, ?)",
            (name, val, chg, now),
        )

    # 히스토리: 날짜별 중복 제거하고 INSERT OR IGNORE
    seen = set()
    for name, hval, date_str in history_bulk:
        key = (name, date_str)
        if key in seen:
            continue
        seen.add(key)
        db.execute(
            "INSERT OR IGNORE INTO indicator_history (name, value, recorded_at) VALUES (?, ?, ?)",
            (name, hval, date_str)
        )

    db.commit()
    db.close()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 지표 {len(indicators)}건 + 히스토리 {len(history_bulk)}건")
    return len(indicators)


if __name__ == "__main__":
    fetch_indicators()
