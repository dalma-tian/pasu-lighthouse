# 파수 플랫폼 청사진 v0.1

## DB 스키마 (SQLite)

### 1. news — 뉴스 원본
```sql
CREATE TABLE news (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    link TEXT UNIQUE,
    source TEXT,
    published_at TIMESTAMP,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance INTEGER DEFAULT 0,      -- 0~100 점수
    stars INTEGER DEFAULT 0,            -- 1~3 변환
    category TEXT,                       -- macro/stock/crypto/forex
    summary TEXT,                        -- LLM 1줄 요약 (나중에)
    impact TEXT                          -- market_impact 태그
);
```

### 2. watchlist — 관심종목
```sql
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY,
    ticker TEXT NOT NULL,               -- 005930, AAPL
    name TEXT,                           -- 삼성전자, Apple
    market TEXT,                         -- KOSPI/NASDAQ/NYSE
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. calendar — 경제 캘린더
```sql
CREATE TABLE calendar (
    id INTEGER PRIMARY KEY,
    event_name TEXT NOT NULL,
    event_date DATE,
    event_time TIME,
    country TEXT,                        -- US/KR/CN
    importance INTEGER,                  -- 1~3
    forecast TEXT,
    previous TEXT,
    actual TEXT,
    category TEXT                        -- cpi/fomc/employment/gdp
);
```

### 4. indicators — 지표 스냅샷
```sql
CREATE TABLE indicators (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,                  -- KOSPI/USDKRW/DXY
    value REAL,
    change_pct REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 폴더 구조
```
~/Desktop/pasu-platform/
├── app.py              # Flask 메인
├── models.py           # DB 모델
├── collector.py        # 뉴스 수집 크롤러
├── scorer.py           # 중요도 점수 계산
├── templates/
│   ├── index.html      # 뉴스피드 (홈)
│   ├── watchlist.html  # 관심종목
│   ├── calendar.html   # 경제캘린더
│   └── dashboard.html  # 지표 대시보드
├── static/
│   └── style.css
└── data/
    └── pasu.db         # SQLite
```

## URL 설계
```
/                    → 뉴스피드 (기본 ★★★ + 선택가능)
/news?stars=3        → ★★★ 뉴스만
/news?ticker=005930  → 삼성전자 관련 뉴스
/watchlist           → 관심종목 관리
/calendar            → 경제 캘린더
/dashboard           → 지표 대시보드
/api/news            → JSON API (AJAX 무한스크롤용)
```

## 핵심 알고리즘

### 중요도 점수 (scorer.py)
```python
EMERGENCY_KW = ["긴급","속보","FOMC","금리","CPI","인상","폭락","급등"]
PREMIUM_SRC = {"연합뉴스","로이터","블룸버그","한국경제","매일경제"}

def score(news):
    pts = 0
    if any(kw in news.title for kw in EMERGENCY_KW): pts += 30
    if news.source in PREMIUM_SRC: pts += 25
    if news.duplicate_count > 5: pts += 15
    if (now - news.published).seconds < 600: pts += 10
    return pts
```

### 종목-뉴스 매칭
```python
def match(news, ticker):
    # 직접: 종목명/티커가 제목에 등장
    if ticker in news.title or name in news.title: return "직접"
    # 간접: 공급망 키워드
    if SUPPLY_CHAIN[ticker] & set(news.keywords): return "간접"
    # 섹터: 같은 업종
    if SECTOR[ticker] == news.sector: return "섹터"
```

## MVP 범위 (1차)
- [x] 청사진
- [ ] DB 생성 + 샘플 데이터
- [ ] 뉴스피드 페이지 (정적)
- [ ] 뉴스 수집 Cron
- [ ] 중요도 점수 적용
- [ ] Flask 서버 구동

## 이후
- [ ] 관심종목 UI + 매칭 알고리즘
- [ ] 캘린더 페이지 + 데이터 연동
- [ ] 지표 대시보드 + 실시간 API
- [ ] AI 요약 (아침 브리핑)
