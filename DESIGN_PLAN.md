# 파수의 등대 — Phase 2.5: 고급화 리디자인 (GPT API 실행용)

> **상태: 계획 저장 완료 — 실행 대기 중**
> 실행 시 Claude Code/GPT API에 이 파일을 프롬프트로 전달할 것.

---

## 작업 1: 타이틀 타이포그래피 이미지 → 검색바 위 배치

### 현재
- 히어로 섹션 내 좌측: "파수의 등대" + "금융정보의 빛이 되는 곳" (텍스트)

### 목표
- **FAL 이미지 생성**으로 "파수의 등대" + "금융정보의 빛이 되는 곳"을 고급 타이포그래피 이미지로 제작
- 검색바 **위** 공간에 배치 (히어로 섹션 완전 제거)
- 검색바 + 필터바 전체를 아래로 밀기

### FAL 프롬프트
```
A minimalist luxury typography design on transparent background.
Main text "파수의 등대" in elegant Korean serif font, large, centered.
Subtitle "금융정보의 빛이 되는 곳" below in small refined sans-serif.
Color: deep charcoal (#1a1a2e) on transparent.
Style: high-end magazine masthead, subtle letter-spacing, thin weight.
No decorations, no icons, no background — pure typography only.
Aspect ratio: 4:1 (wide banner), minimal padding.
```

### 배치 스펙
- `index.html` 최상단 (topbar 아래, 검색바 위)
- `<img>` 태그로 삽입
- max-width: 600px, 중앙 정렬
- 상하 margin: 32px → 검색바가 자연스럽게 밀려 내려감

### HTML 구조
```html
<nav class="topbar">...</nav>

<!-- 신규: 타이틀 타이포그래피 이미지 -->
<div class="title-banner">
  <img src="/static/title-typography.png" alt="파수의 등대">
</div>

<!-- 검색바 (원래 위치에서 아래로 밀림) -->
<div class="search-bar">...</div>
```

### CSS
```css
.title-banner {
  text-align: center;
  margin: 32px auto 24px;
  max-width: 600px;
}
.title-banner img {
  width: 100%;
  height: auto;
  display: block;
}
```

### 수정 파일
- `static/title-typography.png` — FAL로 신규 생성
- `templates/index.html` — 히어로 섹션 제거 → `.title-banner` 추가
- `static/style.css` — `.hero-section` 제거 → `.title-banner` 추가
- `static/style.css` — `.hero-section`, `.hero-text` → `.hero-text-refined` 로 교체

---

## 작업 2: 우측 상단 등대 이미지 삭제

### 현재
```html
<div class="hero-image">
  <img src="/static/lighthouse-hero.png" alt="등대 일러스트">
</div>
```

### 목표
- `.hero-image` 영역 전체 제거
- CSS에서 `.hero-image`, `.hero-image img` 규칙 삭제
- 히어로 섹션이 텍스트만 중앙 정렬하도록 변경

### 수정 파일
- `templates/index.html` — `.hero-image` div 제거
- `static/style.css` — `.hero-image`, `.hero-image img` 규칙 삭제

---

## 작업 3: 워터마크 → 중앙으로 확대 이동 + 아티팩트 애니메이션

### 현재
```css
.watermark-lighthouse {
  position: fixed;
  bottom: 40px;
  right: 30px;
  width: 240px;
  height: 240px;
  opacity: 0.10;
}
```

### 목표
- `bottom: 40px; right: 30px` → 페이지 **중앙** (빗금 영역 = empty state 자리)
- `width: 240px` → **500~600px** 로 대폭 확대
- `opacity: 0.10` → **0.06~0.08** (더 은은하게, 커졌으니)
- 주변 아티팩트(금화·화살표)를 실제 DOM 요소로 5~6개 추가, 각각 떠다니는 애니메이션

### CSS 스펙
```css
/* 중앙 대형 워터마크 */
.watermark-lighthouse-center {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 520px;
  height: 520px;
  background: url('/static/lighthouse-watermark.png') no-repeat center/contain;
  opacity: 0.06;
  pointer-events: none;
  z-index: 0;
  animation: floatCenter 12s ease-in-out infinite;
}

/* 떠다니는 아티팩트 6개 */
.watermark-artifact {
  position: fixed;
  pointer-events: none;
  z-index: 0;
  border-radius: 50%;
}
.artifact-coin {
  width: 28px; height: 28px;
  background: radial-gradient(circle, #fbbf24 0%, transparent 70%);
  opacity: 0.12;
}
.artifact-arrow {
  width: 20px; height: 20px;
  background: radial-gradient(circle, #f472b6 0%, transparent 70%);
  opacity: 0.10;
}

/* 각 아티팩트 개별 위치 + 애니메이션 */
.artifact-1 { top: 38%; left: 30%; animation: floatA 8s ease-in-out infinite; }
.artifact-2 { top: 45%; left: 65%; animation: floatB 10s ease-in-out infinite; }
.artifact-3 { top: 55%; left: 25%; animation: floatC 7s ease-in-out infinite; }
.artifact-4 { top: 35%; left: 55%; animation: floatD 9s ease-in-out infinite; }
.artifact-5 { top: 60%; left: 70%; animation: floatE 11s ease-in-out infinite; }
.artifact-6 { top: 50%; left: 40%; animation: floatF 8.5s ease-in-out infinite; }

@keyframes floatCenter {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  33% { transform: translate(-50%, -53%) scale(1.03); }
  66% { transform: translate(-50%, -48%) scale(0.98); }
}
@keyframes floatA { 0%,100%{transform:translate(0,0)} 50%{transform:translate(30px,-25px)} }
@keyframes floatB { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-20px,-30px)} }
@keyframes floatC { 0%,100%{transform:translate(0,0)} 50%{transform:translate(15px,-20px)} }
@keyframes floatD { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-35px,-15px)} }
@keyframes floatE { 0%,100%{transform:translate(0,0)} 50%{transform:translate(25px,-35px)} }
@keyframes floatF { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-15px,-28px)} }
```

### HTML 추가 (index.html <body> 내)
```html
<div class="watermark-lighthouse-center"></div>
<div class="watermark-artifact artifact-coin artifact-1"></div>
<div class="watermark-artifact artifact-arrow artifact-2"></div>
<div class="watermark-artifact artifact-coin artifact-3"></div>
<div class="watermark-artifact artifact-arrow artifact-4"></div>
<div class="watermark-artifact artifact-coin artifact-5"></div>
<div class="watermark-artifact artifact-arrow artifact-6"></div>
```

### 수정 파일
- `templates/index.html` — 기존 워터마크 div 교체 + 아티팩트 6개 추가
- `static/style.css` — `.watermark-lighthouse` → `.watermark-lighthouse-center` 로 교체, 아티팩트 애니메이션 추가

---

## 작업 4: 픽토그램 — Windows 이모지 → 고급 SVG 픽토그램

### 현재 (Windows 이모지)
| 현재 | 위치 | 용도 |
|---|---|---|
| 🔭 | topbar h1 | 사이트 로고 |
| 🔍 | 검색바 | 검색 아이콘 |
| ★★★/★★/★ | 필터바 | 중요도 |
| 🌐/🇰🇷/🌍/💼 | 필터바 | 지역/포트폴리오 |
| 🔥 | 주요뉴스 헤더 | 섹션 아이콘 |
| 📰 | 뉴스피드 헤더 | 섹션 아이콘 |
| 👁 | 카드 하단 | 조회수 |

### 목표
- Windows 기본 이모지 대신 **고급 SVG 픽토그램**(Lucide, Phosphor, Feather Icons 스타일)으로 교체
- 얇은 선(stroke-width: 1.5~2), 단색(#555~#999), 16~20px

### 변경 맵핑
| 기존 이모지 | → SVG 픽토그램 | 아이콘 라이브러리 |
|---|---|---|
| 🔭 | `telescope` 또는 lighthouse 커스텀 | Lucide |
| 🔍 | `search` | Lucide |
| ★★★ | 별 3개 SVG 인라인 | 커스텀 |
| 🌐 | `globe` | Lucide |
| 🇰🇷 | 태극기 SVG 인라인 | 커스텀 |
| 🌍 | `globe` (다른 색상) | Lucide |
| 💼 | `briefcase` | Lucide |
| 🔥 | `flame` 또는 `trending-up` | Lucide |
| 📰 | `newspaper` | Lucide |
| 👁 | `eye` | Lucide |
| ▾ | `chevron-down` | Lucide |
| 🔄 | `refresh-cw` | Lucide |

### 구현 방식 (선택)
**방법 A: Lucide CDN** (권장 — 가장 간단)
```html
<!-- head 태그 내 -->
<script src="https://unpkg.com/lucide@latest"></script>
```
```html
<!-- 사용 예 -->
<i data-lucide="search" class="icon-sm"></i>
<i data-lucide="globe" class="icon-sm"></i>
<i data-lucide="flame" class="icon-sm icon-accent"></i>
<!-- 페이지 하단에서 초기화 -->
<script>lucide.createIcons();</script>
```

**방법 B: 인라인 SVG** (CDN 없는 경우)
- 각 아이콘을 인라인 SVG로 직접 삽입

### CSS
```css
.icon-sm { width: 16px; height: 16px; stroke-width: 1.8; color: #888; }
.icon-accent { color: #f59e0b; /* 🔥 불꽃 색상 */ }
```

### 수정 파일
- `templates/index.html` — `<head>`에 Lucide CDN, 모든 이모지 → `<i data-lucide>` 교체
- `templates/watchlist.html` — 아이콘 교체
- `templates/dashboard.html` — 아이콘 교체
- `templates/calendar.html` — 아이콘 교체
- `static/style.css` — `.icon-*` 클래스 추가

---

## 작업 5: 실행 타이밍 — 지금은 저장만

### 현재 상태
- 이 파일(`DESIGN_PLAN.md`)에 전체 작업 계획 저장 완료
- **실제 코드 수정/실행은 하지 않음**

### 실행 방법 (나중에)
```bash
cd C:\Users\USER\Desktop\pasu-platform
claude -p "$(cat DESIGN_PLAN.md)" --model sonnet --max-turns 25
```
또는 GPT API에 이 파일 내용을 프롬프트로 전달.

---

## 작업 순서 (실행 시)

1. **작업 2 먼저** — 우측 등대 이미지 삭제 (간단)
2. **작업 1** — 히어로 섹션 텍스트 박스 리디자인
3. **작업 3** — 워터마크 중앙 이동 + 아티팩트 애니메이션
4. **작업 4** — Lucide 픽토그램으로 전체 이모지 교체
5. **검증** — `python app.py` 실행, 모든 라우트 200 OK
6. **배포** — `git push`, Render 자동배포

---

## 영향받는 파일 (총괄)

| 파일 | 작업 |
|---|---|
| `templates/index.html` | 작업1,2,3,4 |
| `templates/watchlist.html` | 작업4 |
| `templates/dashboard.html` | 작업4 |
| `templates/calendar.html` | 작업4 |
| `static/style.css` | 작업1,2,3,4 |
