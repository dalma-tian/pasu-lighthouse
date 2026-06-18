import sqlite3
import os
import csv

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'pasu.db')
STOCKS_CSV = os.path.join(os.path.dirname(__file__), 'data', 'stocks.csv')

def init_db():
    os.makedirs('data', exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT UNIQUE,
                source TEXT,
                published_at TIMESTAMP,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                importance INTEGER DEFAULT 0,
                stars INTEGER DEFAULT 0,
                category TEXT
            );
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT DEFAULT 'stock',
                market TEXT DEFAULT 'KOSPI',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT NOT NULL,
                event_date DATE,
                event_time TIME,
                country TEXT DEFAULT 'US',
                importance INTEGER DEFAULT 1,
                forecast TEXT,
                previous TEXT,
                actual TEXT,
                category TEXT
            );
            CREATE TABLE IF NOT EXISTS indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                value REAL,
                change_pct REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS indicator_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_ind_hist ON indicator_history(name, recorded_at);
            CREATE TABLE IF NOT EXISTS stocks (
                ticker TEXT NOT NULL,
                name TEXT NOT NULL,
                market TEXT NOT NULL,
                type TEXT DEFAULT 'stock',
                PRIMARY KEY (ticker, market)
            );
        ''')
        # 마이그레이션: type 컬럼 없으면 추가
        cols = [row[1] for row in conn.execute('PRAGMA table_info(watchlist)').fetchall()]
        if 'type' not in cols:
            conn.execute('ALTER TABLE watchlist ADD COLUMN type TEXT DEFAULT \'stock\'')
        # stocks 시드: 비어있으면 CSV에서 import
        count = conn.execute('SELECT COUNT(*) FROM stocks').fetchone()[0]
        if count == 0 and os.path.exists(STOCKS_CSV):
            with open(STOCKS_CSV, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                conn.executemany(
                    'INSERT OR IGNORE INTO stocks (ticker, name, market, type) VALUES (?, ?, ?, ?)',
                    reader
                )
        # ETF/ETN 구분 마이그레이션 — 이름에 ETN/ETF 포함 시 type=etf
        conn.execute(
            "UPDATE stocks SET type='etf' WHERE (name LIKE '%ETN%' OR name LIKE '%ETF%') AND type='stock'"
        )
        # 캘린더 시드 (비어있으면 2026년 경제 일정 자동입력)
        cal_count = conn.execute('SELECT COUNT(*) FROM calendar').fetchone()[0]
        if cal_count == 0:
            cal_seed = [
                ('FOMC 회의 (1월)', '2026-01-28', '2026-01-29', 'US', 3, '금리 결정'),
                ('FOMC 회의 (3월)', '2026-03-18', '2026-03-19', 'US', 3, '금리 결정'),
                ('FOMC 회의 (5월)', '2026-05-06', '2026-05-07', 'US', 3, '금리 결정'),
                ('FOMC 회의 (6월)', '2026-06-17', '2026-06-18', 'US', 3, '금리 결정'),
                ('FOMC 회의 (7월)', '2026-07-29', '2026-07-30', 'US', 3, '금리 결정'),
                ('FOMC 회의 (9월)', '2026-09-16', '2026-09-17', 'US', 3, '금리 결정'),
                ('FOMC 회의 (11월)', '2026-11-04', '2026-11-05', 'US', 3, '금리 결정'),
                ('FOMC 회의 (12월)', '2026-12-16', '2026-12-17', 'US', 3, '금리 결정'),
                ('한은 금통위 (1월)', '2026-01-16', None, 'KR', 3, '금리 결정'),
                ('한은 금통위 (2월)', '2026-02-27', None, 'KR', 3, '금리 결정'),
                ('한은 금통위 (4월)', '2026-04-17', None, 'KR', 3, '금리 결정'),
                ('한은 금통위 (5월)', '2026-05-29', None, 'KR', 3, '금리 결정'),
                ('한은 금통위 (7월)', '2026-07-17', None, 'KR', 3, '금리 결정'),
                ('한은 금통위 (8월)', '2026-08-28', None, 'KR', 3, '금리 결정'),
                ('한은 금통위 (10월)', '2026-10-16', None, 'KR', 3, '금리 결정'),
                ('한은 금통위 (11월)', '2026-11-27', None, 'KR', 3, '금리 결정'),
                ('CPI 발표 (7월)', '2026-07-15', None, 'US', 2, '소비자물가'),
                ('CPI 발표 (8월)', '2026-08-12', None, 'US', 2, '소비자물가'),
                ('고용보고서 (7월)', '2026-07-04', None, 'US', 2, '비농업고용'),
                ('고용보고서 (8월)', '2026-08-01', None, 'US', 2, '비농업고용'),
                ('GDP 발표 (Q2)', '2026-07-30', None, 'KR', 2, 'GDP'),
                ('수출입동향 (7월)', '2026-08-01', None, 'KR', 1, '무역수지'),
            ]
            conn.executemany(
                'INSERT INTO calendar (event_name, event_date, event_time, country, importance, category) VALUES (?,?,?,?,?,?)',
                cal_seed
            )
        # watchlist CSV 복원 (Render sleep 대응)
        restore_watchlist(conn)
    conn.close()

WATCHLIST_CSV = os.path.join(os.path.dirname(__file__), 'data', 'watchlist.csv')

def restore_watchlist(conn):
    """CSV에서 watchlist 복원 (DB가 비어있을 때)"""
    count = conn.execute('SELECT COUNT(*) FROM watchlist').fetchone()[0]
    if count > 0:
        return
    if not os.path.exists(WATCHLIST_CSV):
        return
    try:
        with open(WATCHLIST_CSV, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return
            for row in reader:
                if len(row) >= 4:
                    conn.execute(
                        'INSERT OR IGNORE INTO watchlist (ticker, name, type, market) VALUES (?,?,?,?)',
                        (row[0], row[1], row[2], row[3])
                    )
        print(f"[watchlist] CSV에서 {conn.execute('SELECT COUNT(*) FROM watchlist').fetchone()[0]}종목 복원됨")
    except Exception as e:
        print(f"[WARN] watchlist restore: {e}")

def backup_watchlist():
    """DB → CSV 백업"""
    os.makedirs(os.path.dirname(WATCHLIST_CSV), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute('SELECT ticker, name, type, market FROM watchlist ORDER BY added_at DESC').fetchall()
    with open(WATCHLIST_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ticker', 'name', 'type', 'market'])
        for row in rows:
            writer.writerow(row)
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == '__main__':
    init_db()
    print("DB initialized")
