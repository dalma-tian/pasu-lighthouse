# 파수의 등대 — Phase 1.5 디자인 수정 (히어로 섹션 + 그라데이션)

## 현재 상태
Phase 1 디자인 완료. tokens.css + style.css 546줄 + 4개 템플릿 개선 완료.

## 추가 수정사항

### 1. 히어로 섹션 (YouTube Music 레퍼런스)
- **현재**: 상단바 바로 아래부터 뉴스 카드 시작
- **변경**: 상단바 아래에 220px 높이의 브랜딩 히어로 섹션 추가
- 히어로는 홈페이지(/)에서만 표시. 다른 페이지(watchlist, calendar, dashboard)는 기존대로.
- 레이아웃: 좌측 텍스트 + 우측 일러스트
  - 좌측: 볼드 태그라인 "파수의 등대" (24px), 서브텍스트 "금융정보의 빛이 되는 곳" (14px, text-secondary)
  - 우측: 등대 3D 일러스트 (static/lighthouse-hero.png), max-width 160px

### 2. 파스텔 핑크 그라데이션 배경 (토스증권 레퍼런스)
- 히어로 섹션의 배경에만 적용
- 그라데이션: `linear-gradient(135deg, #fce4ec 0%, #f8bbd0 25%, #ffffff 70%, #e8eaf6 100%)`
- `background-size: 400% 400%`
- 슬로우 키프레임 애니메이션 (20초 루프, 물결처럼 부드럽게):
```css
@keyframes heroGradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

### 3. 히어로 섹션 아래 뉴스 콘텐츠
- 히어로 섹션 직후에 기존 뉴스피드가 이어짐
- filter-bar, tab-bar, feed는 그대로 유지

## 구현 방법
1. `templates/index.html`: `<main class="feed">` 바로 앞에 히어로 섹션 HTML 추가
2. `static/style.css`: 히어로 섹션 CSS + 그라데이션 애니메이션 추가
3. 이미지: `static/lighthouse-hero.png` (984KB, 이미 배치됨)
4. 반응형: 모바일(≤480px)에서는 히어로 높이 160px, 일러스트 100px

## 중요
- 기존 CSS/JS/템플릿 기능 전혀 건드리지 말 것
- filter-bar, tab-bar, feed, 카드 컴포넌트 그대로 유지
- dashboard, calendar, watchlist 페이지는 히어로 없이 그대로
