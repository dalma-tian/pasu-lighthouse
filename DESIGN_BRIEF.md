# 🏗️ 파수의 등대 — 디자인 전면 개선 지시

> **To: 달마**
> **From: 달수**
> **병행 작업: Claude Code도 동시에 같은 작업 수행 중 → 결과 비교 예정**

---

## 📍 현재 운영 상태

| 항목 | 값 |
|---|---|
| **사이트명** | 파수의 등대 |
| **URL** | https://pasu-lighthouse.onrender.com |
| **GitHub** | `dalma-tian/pasu-lighthouse` |
| **배포** | Render Free (Ohio), Python Flask + SQLite |
| **뉴스 수집** | Google RSS + 네이버 금융 5개 섹션 HTML 파싱 (30분 크론) |
| **뉴스 현황** | 실시간 50건↑, 실제 언론사명 표시, 중요도 ★★☆ |
| **지표** | 6종 (미국 기준금리, S&P500, WTI, 한국 기준금리, KOSPI, 환율) — 각 20~60건 히스토리 |
| **캘린더** | FOMC 8회 + 금통위 8회 + CPI·고용·GDP·수출입 (22건), 리스트/달력 뷰 토글 |
| **포트폴리오** | 3,004종목 자동완성, 관심종목 뉴스 탭, CSV 백업/복원 |

---

## 🎨 디자인 레퍼런스 (필수 숙지)

### 1. Toss Tech Design 132 아티클 요약
- Hermes 스킬: `toss-design` (skill_view로 로드 가능)
- GitHub: https://github.com/Ilbie/Toss-Design-Skill
- 핵심: **신뢰 > 전환율, 인지부하 감소, 액션 분해, UX Writing 시스템, 기능적 색상**

### 2. saveticker.com 역분석
- 위키: `위키/concepts/saveticker-analysis.md`
- 핵심: **데이터 밀도, 스캔 용이성, Design Token 시스템, 무한스크롤**

### 3. 퓨전 전략
- 위키: `위키/concepts/toss-saveticker-design-fusion.md`
- 방향: Toss의 신뢰·간결함 + saveticker의 데이터 밀도
- **라이트 테마 고정** (다크모드 제외)

---

## 🎯 디자인 작업 범위

### Phase 1 — 지금 당장 (우선순위 ★★★)

#### 1. Design Token 시스템 구축
- `static/tokens.css` 신규 생성
- CSS Custom Properties로 일관된 팔레트 구축
- Primary Blue `#3b82f6`, Trust `#1d4ed8`, Alert `#e53e3e`, Positive `#059669`
- 4px 베이스 Spacing 시스템, 일관된 Radius

#### 2. 뉴스 카드 컴포넌트 재설계
- 출처 → 컬러 뱃지로 (기능적 색상)
- 시간 → 상대 표기 ("3시간 전")
- 제목 + 출처 + 시간 → 한 줄에 스캔 최적화
- 중요도 ★★★ 상단 고정 "오늘 주요뉴스" 섹션
- 카드 간 여백 조정 (밀도 ↑)

#### 3. UX Writing 전면 개선
- "🔄 새로고침" → "🔄 최신 뉴스 가져오기"
- 빈 상태 메시지 자연스럽게
- 모든 버튼·라벨 Toss 8원칙 적용

#### 4. 전체 레이아웃 정비
- 상단바 높이·그림자·타이포 최적화
- 탭바 선택 상태 시각화 개선
- 폰트: Noto Sans KR + Inter (saveticker 레퍼런스)

### Phase 2 — 후속 (선택)
- 무한스크롤 (Intersection Observer)
- 상단 검색바
- 티커 태그

---

## 🛠️ 기술 제약

- **Flask + Jinja2** 템플릿, SSR 위주
- **순수 CSS** (Tailwind 불가)
- **Chart.js CDN** (지표 그래프용)
- **Render Free 512MB** 메모리 제한
- **SQLite** (Render sleep 시 데이터 증발, 크론이 복구)

---

## 📂 수정 대상 파일

```
pasu-platform/
├── static/
│   ├── style.css          ← 메인 타겟 (전면 재작성)
│   ├── tokens.css         ← 신규 (Design Token)
│   └── components/        ← 신규 (카드·뱃지·모달 분리)
├── templates/
│   ├── index.html         ← 뉴스피드
│   ├── watchlist.html     ← 포트폴리오
│   ├── dashboard.html     ← 지표 대시보드
│   ├── calendar.html      ← 캘린더
```

---

## 📏 평가 기준

1. **신뢰감** — 출처·시간 명확, 과장된 표현 없음
2. **인지 속도** — 스캔만으로 핵심 정보 파악 가능
3. **일관성** — 모든 페이지 동일한 Design Token 사용
4. **기능적 아름다움** — 예쁨보다 정보 전달력
5. **UX Writing** — 자연스럽고 압박 없는 문구

---

## 🔗 참고 링크

- Toss Tech Design: https://toss.tech/category/design
- Toss Design Skill: https://github.com/Ilbie/Toss-Design-Skill
- saveticker: https://saveticker.com
- 디자인 퓨전 전략: `위키/concepts/toss-saveticker-design-fusion.md`
