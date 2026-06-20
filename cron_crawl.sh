#!/bin/bash
# 파수의 등대 — 워치리스트 뉴스 수집 (크론 전용)
cd /c/Users/USER/Desktop/pasu-platform

# 1. 로컬 DB 수집
LOCAL_OUT=$(python -c "
from news_crawler import crawl
total = crawl()
print(f'로컬 {total}건')
" 2>&1)

# 2. Render 공개링크에도 트리거
RENDER_OUT=$(curl -s "https://pasu-lighthouse.onrender.com/api/crawl" 2>&1)
RENDER_COUNT=$(echo "$RENDER_OUT" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('new_articles','?'))" 2>/dev/null || echo "?")

echo "🕯️ $LOCAL_OUT | Render $RENDER_COUNT건"
