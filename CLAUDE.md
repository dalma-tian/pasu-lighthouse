# 파수의 등대 — CLAUDE.md

> **⚠️ 폴더 = `C:\Users\USER\Desktop\pasu-platform` (NOT `파수의등대`)**
> **달마가 이 파일을 자동으로 읽음. 여기 적힌 컨텍스트로 바로 작업 시작.**

---

## 현재 상태 (2026-06-20)

| 항목 | 값 |
|---|---|
| URL | https://pasu-lighthouse.onrender.com |
| 스택 | Flask + Jinja2 + SQLite + Render Free (512MB) |
| 최근 커밋 | `06ee548` — 달수: 타이틀 CSS + 물결 + 워터마크 (2파일, +38/-18) |
| 직전 GPT | `f9d768e` — Lucide 픽토그램 + Pillow 타이틀 (사용자 불만족) |

---

## 1. Design Token 시스템 (`static/tokens.css`)

**모든 CSS는 이 변수만 사용. 하드코딩 색상 금지.**

```css
/* ── Core Palette ── */
--color-primary: #3b82f6;        /* 버튼, 링크 */
--color-primary-hover: #2563eb;
--color-primary-light: #eff6ff;  /* hover 배경 */
--color-trust: #1d4ed8;
--color-alert: #e53e3e;          /* 위험/하락 */
--color-alert-light: #fef2f2;
--color-positive: #059669;       /* 상승 */
--color-positive-light: #ecfdf5;
--color-warning: #f59e0b;        /* 주의 */
--color-warning-light: #fffbeb;

/* ── Backgrounds ── */
--color-bg: #ffffff;
--color-bg-secondary: #f8f9fc;
--color-bg-tertiary: #f1f5f9;
--color-bg-hover: #f3f5f8;

/* ── Text ── */
--color-text-primary: #1a1a2e;   /* 제목 */
--color-text-secondary: #6b7280; /* 본문 */
--color-text-tertiary: #9ca3af;  /* 캡션·시간 */

/* ── Spacing (4px 베이스) ── */
--space-xs: 4px;  --space-sm: 8px;  --space-md: 16px;
--space-lg: 24px; --space-xl: 32px;

/* ── Radius ── */
--radius-sm: 6px;  --radius-md: 10px;
--radius-lg: 16px; --radius-full: 9999px;

/* ── Shadows ── */
--shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
--shadow-md: 0 2px 8px rgba(0,0,0,0.06);
--shadow-lg: 0 4px 16px rgba(0,0,0,0.08);

/* ── Typography ── */
--font-sans: 'Inter', 'Noto Sans KR', -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;

/* ── Cards (Phase 2) ── */
--card-shadow: 0 1px 3px rgba(0,0,0,0.06);
--card-hover-shadow: 0 4px 16px rgba(248, 187, 208, 0.2); /* 핑크 그림자 */

/* ── Search & Filter ── */
--search-bg: #f1f3f5;
--filter-active-bg: #2d2d2d;
--filter-active-text: #ffffff;
--filter-inactive-bg: #f1f3f5;
--filter-inactive-text: #555555;
```

---

## 2. UX Writing 규칙 (Toss 스타일)

### 원칙
- **짧고 자연스럽게** — "~하세요" 금지, "~해보세요" 선호
- **빈 상태도 따뜻하게** — 오류·공백도 브랜드 톤 유지
- **행동 유도는 구체적으로** — "여기를 눌러" 대신 "어디로 가면 되는지" 알려주기
- **과장 금지** — "충격!" "초특급" 같은 클릭베이트 절대 안 됨 (신뢰 훼손)

### 실제 적용 예시

| ❌ 안 좋은 예 | ✅ 적용 |
|---|---|
| "새로고침" | "최신 뉴스 가져오기" |
| "데이터가 없습니다" | "첫 뉴스를 기다리고 있어요" |
| "오류 발생" | "잠시 뒤 자동으로 채워집니다" |
| "관심 종목 없음" | "관심 종목이 없거나 관련 뉴스가 없어요" |
| (버튼만) | "포트폴리오 페이지에서 종목을 추가해보세요" ← CTA 제안 |

### 톤 앤 매너
- 신뢰감 있는 금융 플랫폼 — 지나치게 캐주얼하지 않게
- 사용자를 "당신"이라고 부르지 않음 — 직접 호칭보다 정보 중심
- **타이틀 태그라인**: "당신의 자산, 당신의 정보, 당신의 항해" (현재 사용 중)

---

## 3. 뉴스 카드 Priority 강조 방식

### 중요도 체계 (stars: 1~3)

| stars | 의미 | 시각 처리 |
|---|---|---|
| ★★★ (3) | 필수·긴급 | `.card-featured` — 왼쪽 보더 하이라이트, 최상단 배치 |
| ★★☆ (2) | 주요 | `.top-news-v2` → `.top-news-grid` 2열로 상단 고정 |
| ★☆☆ (1) | 일반 | `.feed` 하단 일반 리스트 |

### 섹션 구조

```
┌─ 필터바 ─────────────────────────────────┐
│ [전체] [★★★] [★★☆] [★☆☆] | 종합 속보 분석 │
│ [전체] [🇰🇷 국내] [🌐 글로벌] [📋 내 포트폴리오] │
└──────────────────────────────────────────┘

┌─ 오늘 주요뉴스 (stars ≥ 2) ──────────────┐
│  ┌──────────┐  ┌──────────┐              │
│  │ ★★★ 카드  │  │ ★★☆ 카드  │   (2열 그리드) │
│  └──────────┘  └──────────┘              │
│  ┌──────────┐  ┌──────────┐              │
│  │ ★★☆ 카드  │  │ ★★☆ 카드  │              │
│  └──────────┘  └──────────┘              │
└──────────────────────────────────────────┘

┌─ 뉴스 (일반 피드) ────────────────────────┐
│  ★☆☆ 카드                               │
│  ★☆☆ 카드                               │
│  ★☆☆ 카드                               │
└──────────────────────────────────────────┘
```

### 카드 컴포넌트 구조
```
┌─ card (.card-featured if stars=3) ────────┐
│ [출처 뱃지] · 구분선 · 3시간 전  ★★★      │  ← card-meta
│ 뉴스 제목 (링크)                          │  ← card-title
│ 👁 1,234                                  │  ← card-footer
└───────────────────────────────────────────┘
```

### 출처 뱃지 컬러 (기능적 색상)
```css
.src-blue   → 이데일리
.src-red    → 한국경제
.src-green  → 연합뉴스
.src-purple → 뉴스1, 뉴시스
.src-orange → 조선, 매일경제
```

---

## 전체 디자인 컨벤션

| 항목 | 값 |
|---|---|
| 테마 | **라이트 전용** (다크모드 없음) |
| 배경 | `#fef5f7` + 6개 radial-gradient + `bgWave` 20s 애니메이션 |
| 본문 폰트 | Inter + Noto Sans KR (Google Fonts CDN) |
| 아이콘 | Lucide (CDN: `unpkg.com/lucide@latest`) — Windows 이모지 금지 |
| 제목 폰트 | Inter 700, charcoal |
| 카드 hover | 핑크 그림자 (`--card-hover-shadow`) |
| 워터마크 | 등대 PNG (정지) + 6개 아티팩트 float 애니메이션 |
| CSS 방법론 | 순수 CSS, Tailwind 불가 |
| 템플릿 | Jinja2 (SSR 위주) |

---

## 검증 프로토콜 (필수)

수정 후 반드시:
```bash
cd C:\Users\USER\Desktop\pasu-platform
python app.py  # → 모든 라우트 200 OK 확인
```

## Git 커밋 후 Render 자동 배포됨

---

## 남은 피드백 (더블배럴님)

1. **제목 "파수의 등대"** — 핑크 컨셉 + 고급 타이포그래피 ("투자와 더 가까워지는 순간" 스타일 참고)
2. **배경 물결** — Toss 스타일의 은은한 그라데이션. 현재 있으나 더 눈에 띄게.
3. **등대 워터마크** — opacity 0.14, 580px. 더 진하게.
4. **폰트 통일** — 산세리프 전체 적용
