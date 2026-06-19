# 파수의 등대 — Flask 경제뉴스 플랫폼

## 기술 스택
- **백엔드**: Flask + Jinja2 (SSR), Python
- **DB**: SQLite (`data/pasu.db`)
- **배포**: Render Free (512MB RAM, Ohio), `pasu-lighthouse.onrender.com`
- **GitHub**: `dalma-tian/pasu-lighthouse` (main 브랜치)
- **JS**: Vanilla JS + Chart.js CDN

## 프로젝트 구조
```
pasu-platform/
├── app.py              ← Flask 라우트 (/, /watchlist, /dashboard, /calendar)
├── models.py           ← DB 스키마
├── news_crawler.py     ← 뉴스 수집 (Google RSS + 네이버)
├── indicator_fetcher.py ← 지표 수집 (FRED, ECOS, Yahoo, 환율)
├── scorer.py           ← 중요도 점수 엔진
├── static/
│   └── style.css       ← 현재 단일 CSS 파일 (전면 재작성 대상)
├── templates/
│   ├── index.html      ← 뉴스피드
│   ├── watchlist.html  ← 포트폴리오
│   ├── dashboard.html  ← 지표 대시보드 (Chart.js)
│   └── calendar.html   ← 경제 캘린더 (리스트/달력 토글)
└── data/
    ├── pasu.db         ← SQLite DB
    ├── stocks.csv      ← 3,004 종목 사전
    ├── calendar.csv    ← 캘린더 시드
    └── watchlist.csv   ← 관심종목 백업
```

## 디자인 철학 — Toss × saveticker 퓨전

### Toss Tech Design (132 아티클 기반)
- **신뢰 > 전환율** — 출처 명확, 과장된 표현 금지
- **인지부하 감소** — 선택지·입력 최소화, 필수 정보만
- **기능적 색상** — 예쁨보다 정보 전달, 상태별 컬러
- **액션 분해** — 큰 기능을 작은 단위로
- **UX Writing 8원칙**: Predictable hint, Weed cutting, Remove empty sentences, Focus on key message, Easy to speak, Suggest over force, Universal words, Find hidden emotion

### saveticker.com
- **데이터 밀도** — 스캔만으로 핵심 정보 파악
- **Design Token 시스템** — CSS Custom Properties
- **Noto Sans KR + Inter** 폰트 조합

### 파수의 등대 방향
- **라이트 테마 고정** (다크모드 사용 안 함)
- Toss의 신뢰·간결함 + saveticker의 데이터 밀도
- 4대 모듈: 뉴스 / 포트폴리오 / 캘린더 / 지표

## Design Token

```css
:root {
  --color-primary: #3b82f6;
  --color-primary-hover: #2563eb;
  --color-trust: #1d4ed8;
  --color-alert: #e53e3e;
  --color-positive: #059669;
  --color-warning: #f59e0b;
  --color-bg: #ffffff;
  --color-bg-secondary: #f8f9fc;
  --color-bg-tertiary: #f1f5f9;
  --color-text: #1a1a2e;
  --color-text-secondary: #6b7280;
  --color-text-tertiary: #9ca3af;
  --color-border: #e5e7eb;
  --color-border-light: #f3f4f6;
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 2px 8px rgba(0,0,0,0.06);
  --shadow-lg: 0 4px 16px rgba(0,0,0,0.08);
  --font-sans: 'Inter', 'Noto Sans KR', -apple-system, sans-serif;
}
```

## 작업 지시 — Phase 1 디자인 전면 개선

전체 사이트를 아래 순서로 재디자인한다. 모든 변경은 기존 기능을 유지하면서 순수 CSS + HTML 구조만 변경.

### Step 1: Design Token 시스템 구축
- `static/tokens.css` 신규 생성 (위 Token 전체)
- `static/style.css`에서 tokens.css를 `@import` 하도록 수정

### Step 2: 전역 레이아웃 재설계
- 상단 네비게이션바: 높이 56px, 흰색 배경, 하단 보더만 살짝, 로고 왼쪽 + 탭 오른쪽
- 탭: 활성 탭 하단 2px 블루 언더라인, 비활성 탭 text-secondary, 호버 시 primary
- 본문: max-width 768px, 가운데 정렬, padding 16px
- 전체 배경: `--color-bg-secondary`

### Step 3: 뉴스 카드 컴포넌트 재설계 (`index.html` + `style.css`)
- 카드: 흰색 배경, radius-md, shadow-sm, padding 16px, 카드 간격 10px
- 출처 뱃지: 작은 컬러 태그 (이데일리=파랑, 한국경제=빨강, 연합뉴스=초록 등) 좌측 상단
- 제목: 15px, font-weight 600, color-text, line-height 1.5
- 메타정보: 출처 뱃지 + 상대시간("3시간 전") + 중요도 별, 한 줄에
- 중요도 ★★★: 카드 왼쪽에 3px 컬러 바 (금색)
- "오늘 주요뉴스" 섹션: ★★★ 뉴스만 상단에 분리, 살짝 다른 배경

### Step 4: UX Writing 전면 개선
- "🔄 새로고침" → "최신 뉴스 가져오기"
- "📭 아직 수집된 뉴스가 없습니다" → "첫 뉴스를 기다리고 있어요"
- "뉴스 수집기가 곧 첫 데이터를 가져올 예정입니다" → "잠시 후 자동으로 채워집니다"
- 포트폴리오 빈 상태: "관심 종목을 추가하면 관련 뉴스가 여기에 표시됩니다"
- 대시보드 빈 상태: "잠시만 기다리면 경제 지표가 표시됩니다"
- 모든 버튼: 명확한 액션 동사 사용 (Suggest over force)

### Step 5: 포트폴리오 페이지 개선
- 자동완성 드롭다운: radius-md, 그림자, 최대 높이 제한
- 추가된 종목: 카드 스타일 (티커 + 종목명 + 삭제버튼)
- ETF 뱃지: 작은 태그로 표시

### Step 6: 대시보드 + 캘린더 통일성
- 대시보드 지표 카드: 현재 디자인 유지하되 토큰 적용
- 캘린더: 토큰 적용, 리스트/달력 토글 버튼 스타일 통일

## 기술 제약
- 순수 CSS만 사용 (Tailwind 불가)
- Jinja2 템플릿 유지
- Chart.js CDN은 유지
- 기존 JavaScript 기능 변경 금지
- 반응형: 모바일 480px 브레이크포인트
- 모든 변경 후 `python -c "from app import app; app.test_client().get('/')"` 으로 검증
