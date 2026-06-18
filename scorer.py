from datetime import datetime, timedelta

EMERGENCY_KW = ["긴급", "속보", "FOMC", "금리", "CPI", "인상", "폭락", "급등", "발표", "돌파"]
PREMIUM_SRC = {"연합뉴스", "로이터", "블룸버그", "한국경제", "매일경제", "서울경제", "파이낸셜뉴스"}

def score(title, source, published_at, duplicate_count=0):
    pts = 0

    # 키워드 가중치 (30점)
    for kw in EMERGENCY_KW:
        if kw in title:
            pts += 5 if kw not in ["긴급", "속보"] else 10
    pts = min(pts, 30)

    # 출처 권위 (25점)
    if source in PREMIUM_SRC:
        pts += 25

    # 중복 보도 (15점)
    if duplicate_count >= 5:
        pts += 15

    # 시간 민감도 (10점) — 10분 이내 발표
    if published_at:
        try:
            pub = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            if datetime.now().replace(tzinfo=None) - pub.replace(tzinfo=None) < timedelta(minutes=10):
                pts += 10
        except:
            pass

    return min(pts, 100)

def to_stars(importance):
    if importance >= 70:
        return 3
    elif importance >= 40:
        return 2
    return 1
