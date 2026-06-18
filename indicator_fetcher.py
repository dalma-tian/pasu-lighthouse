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
    """FRED API → 최신 값"""
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_KEY}&file_type=json&sort_order=desc&limit=2"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    obs = data["observations"]
    latest = obs[0]
    prev = obs[1] if len(obs) > 1 else {"value": "0"}
    try:
        val = float(latest["value"])
        pval = float(prev["value"])
        chg = round(val - pval, 2) if pval != 0 else 0
        return val, chg
    except (ValueError, KeyError):
        return latest["value"], 0


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
    """6개 핵심 지표 수집 → DB 저장"""
    indicators = []

    try:
        val, chg = fetch_fred("FEDFUNDS")
        indicators.append(("미국 기준금리", val, chg))
    except Exception as e:
        print(f"[ERR] FRED 기준금리: {e}")

    try:
        val, chg = fetch_fred("SP500")
        indicators.append(("S&P500", val, chg))
    except Exception as e:
        print(f"[ERR] S&P500: {e}")

    try:
        val, chg = fetch_fred("DCOILWTICO")
        indicators.append(("WTI 유가", val, chg))
    except Exception as e:
        print(f"[ERR] WTI: {e}")

    try:
        val, chg = fetch_ecos()
        indicators.append(("한국 기준금리", val, chg))
    except Exception as e:
        print(f"[ERR] ECOS: {e}")

    try:
        val, chg = fetch_kospi()
        indicators.append(("KOSPI", val, chg))
    except Exception as e:
        print(f"[ERR] KOSPI: {e}")

    try:
        val, chg = fetch_usdkrw()
        indicators.append(("원/달러 환율", val, chg))
    except Exception as e:
        print(f"[ERR] 환율: {e}")

    # DB 저장
    db = sqlite3.connect(DB_PATH)
    now = datetime.now(timezone.utc).isoformat()
    for name, val, chg in indicators:
        db.execute(
            "INSERT OR REPLACE INTO indicators (name, value, change_pct, updated_at) VALUES (?, ?, ?, ?)",
            (name, val, chg, now),
        )
        # 히스토리도 기록 (분 단위 중복 방지)
        now_minute = now[:16]
        last_hist = db.execute(
            "SELECT recorded_at FROM indicator_history WHERE name=? ORDER BY recorded_at DESC LIMIT 1",
            (name,)
        ).fetchone()
        if not last_hist or last_hist[0][:16] < now_minute:
            db.execute(
                "INSERT INTO indicator_history (name, value, recorded_at) VALUES (?, ?, ?)",
                (name, val, now)
            )
    db.commit()
    db.close()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 지표 {len(indicators)}건 업데이트")
    return len(indicators)


if __name__ == "__main__":
    fetch_indicators()
