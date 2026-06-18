import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'pasu.db')

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
                name TEXT,
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
        ''')
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == '__main__':
    init_db()
    print("DB initialized")
