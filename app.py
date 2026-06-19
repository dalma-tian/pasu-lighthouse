from flask import Flask, render_template, request, jsonify
import sqlite3
from models import init_db, get_db, backup_watchlist
import scorer

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
init_db()

@app.context_processor
def inject_asset_version():
    import os
    try:
        css_path = os.path.join(app.root_path, 'static', 'style.css')
        return {'asset_version': int(os.path.getmtime(css_path))}
    except OSError:
        return {'asset_version': 1}

@app.after_request
def prevent_static_cache(response):
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-store, max-age=0'
    return response

@app.route('/')
def index():
    stars = request.args.get('stars', 'all')
    tab = request.args.get('tab', 'all')
    ticker = request.args.get('ticker', '')

    db = get_db()
    query = 'SELECT * FROM news WHERE 1=1'
    params = []

    if stars != 'all':
        query += ' AND stars = ?'
        params.append(int(stars))
    if tab == 'domestic':
        query += " AND (link LIKE '%n.news.naver.com%' OR link LIKE '%finance.naver.com%')"
    elif tab == 'global':
        query += " AND (link NOT LIKE '%n.news.naver.com%' AND link NOT LIKE '%finance.naver.com%')"
    elif tab == 'portfolio':
        # 관심종목 뉴스: watchlist에 등록된 종목명/티커가 제목에 포함된 기사
        watchlist_items = db.execute('SELECT name, ticker FROM watchlist').fetchall()
        if watchlist_items:
            conditions = []
            for item in watchlist_items:
                conditions.append('(title LIKE ? OR title LIKE ?)')
                params.extend([f'%{item["name"]}%', f'%{item["ticker"]}%'])
            query += ' AND (' + ' OR '.join(conditions) + ')'
        else:
            # 관심종목 없으면 빈 결과
            query += ' AND 1=0'
    if ticker:
        query += ' AND (title LIKE ? OR title LIKE ?)'
        params.extend([f'%{ticker}%', f'%{get_name(ticker)}%'])

    query += ' ORDER BY stars DESC, published_at DESC LIMIT 50'
    news_list = db.execute(query, params).fetchall()
    db.close()
    return render_template('index.html', news_list=news_list, current_stars=stars, current_tab=tab)

@app.route('/api/news')
def api_news():
    db = get_db()
    news_list = db.execute(
        'SELECT * FROM news ORDER BY stars DESC, published_at DESC LIMIT 20'
    ).fetchall()
    db.close()
    return jsonify([dict(row) for row in news_list])

def get_name(ticker):
    db = get_db()
    row = db.execute('SELECT name FROM stocks WHERE ticker = ? LIMIT 1', (ticker,)).fetchone()
    db.close()
    return row['name'] if row else ticker

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    if len(q) < 1:
        return jsonify([])
    db = get_db()
    rows = db.execute(
        'SELECT ticker, name, market, type FROM stocks WHERE name LIKE ? ORDER BY '
        'CASE WHEN name = ? THEN 0 WHEN name LIKE ? THEN 1 ELSE 2 END, '
        'name LIMIT 8',
        (f'%{q}%', q, f'{q}%')
    ).fetchall()
    db.close()
    results = []
    for r in rows:
        results.append({
            'ticker': r['ticker'],
            'name': r['name'],
            'market': r['market'],
            'type': r['type'],
            'label': f"{r['name']} ({r['ticker']}, {r['market']})"
        })
    return jsonify(results)

@app.route('/watchlist', methods=['GET', 'POST'])
@app.route('/portfolio', methods=['GET', 'POST'])
def watchlist():
    db = get_db()
    if request.method == 'POST':
        ticker = request.form.get('ticker', '').strip().upper()
        name = request.form.get('name', '').strip()
        item_type = request.form.get('type', 'stock')
        market = request.form.get('market', 'KOSPI')
        if ticker and name:
            try:
                db.execute(
                    'INSERT INTO watchlist (ticker, name, type, market) VALUES (?, ?, ?, ?)',
                    (ticker, name, item_type, market)
                )
                db.commit()
                backup_watchlist()
            except sqlite3.IntegrityError:
                pass  # 중복 무시
        db.close()
        return '', 204

    # GET
    items = db.execute(
        'SELECT * FROM watchlist ORDER BY added_at DESC'
    ).fetchall()
    db.close()
    return render_template('watchlist.html', items=items)

@app.route('/watchlist/delete/<int:item_id>', methods=['POST'])
def watchlist_delete(item_id):
    db = get_db()
    db.execute('DELETE FROM watchlist WHERE id = ?', (item_id,))
    db.commit()
    backup_watchlist()
    db.close()
    return '', 204

@app.route('/calendar')
def calendar():
    db = get_db()
    events = db.execute(
        'SELECT * FROM calendar ORDER BY event_date ASC'
    ).fetchall()
    db.close()
    return render_template('calendar.html', events=events)

@app.route('/dashboard')
def dashboard():
    db = get_db()
    indicators = db.execute(
        'SELECT * FROM indicators ORDER BY name'
    ).fetchall()
    db.close()
    return render_template('dashboard.html', indicators=indicators)

@app.route('/api/crawl')
def api_crawl():
    """뉴스 크롤링 수동 트리거 (cron용)"""
    import news_crawler
    count = news_crawler.crawl()
    return jsonify({'status': 'ok', 'new_articles': count})

@app.route('/api/indicators')
def api_indicators():
    """지표 수동 갱신 트리거"""
    import indicator_fetcher
    count = indicator_fetcher.fetch_indicators()
    return jsonify({'status': 'ok', 'updated': count})

@app.route('/api/indicator/history/<path:name>')
def api_indicator_history(name):
    """지표별 시계열 히스토리 (최근 60건)"""
    from urllib.parse import unquote
    name = unquote(name)
    db = get_db()
    rows = db.execute(
        'SELECT value, recorded_at FROM indicator_history WHERE name = ? ORDER BY recorded_at DESC LIMIT 120',
        (name,)
    ).fetchall()
    db.close()
    return jsonify([{'value': r['value'], 'date': r['recorded_at'][:10]} for r in reversed(rows)])

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5050))
    app.run(debug=False, host='0.0.0.0', port=port)
