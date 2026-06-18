from flask import Flask, render_template, request, jsonify
from models import init_db, get_db
import scorer

app = Flask(__name__)
init_db()

@app.route('/')
def index():
    stars = request.args.get('stars', 'all')
    ticker = request.args.get('ticker', '')

    db = get_db()
    query = 'SELECT * FROM news WHERE 1=1'
    params = []

    if stars != 'all':
        query += ' AND stars = ?'
        params.append(int(stars))
    if ticker:
        query += ' AND (title LIKE ? OR title LIKE ?)'
        params.extend([f'%{ticker}%', f'%{get_name(ticker)}%'])

    query += ' ORDER BY stars DESC, published_at DESC LIMIT 50'
    news_list = db.execute(query, params).fetchall()
    db.close()
    return render_template('index.html', news_list=news_list, current_stars=stars)

@app.route('/api/news')
def api_news():
    db = get_db()
    news_list = db.execute(
        'SELECT * FROM news ORDER BY stars DESC, published_at DESC LIMIT 20'
    ).fetchall()
    db.close()
    return jsonify([dict(row) for row in news_list])

def get_name(ticker):
    names = {'005930': '삼성전자', '000660': 'SK하이닉스', '329180': 'HD현대중공업'}
    return names.get(ticker, ticker)

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
    db.close()
    return '', 204

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5050))
    app.run(debug=False, host='0.0.0.0', port=port)
