# AGENTS.md — Codex(GPT) Obsidian 연동 지시사항

## Obsidian Vault (Second Brain)
- Vault 루트: `/mnt/c/Users/USER/Documents/Obsidian Vault`
- 위키 구조: `위키/index.md` → `위키/concepts/`, `위키/entities/`, `위키/comparisons/`
- 프로젝트 문서: `시스템/`, `프로젝트/` 폴더 내 Markdown
- 이 파일은 Claude Code의 `CLAUDE.md`와 동일한 역할. Obsidian Vault가 Second Brain.

## 위키 접근 방식 (토큰 효율)
1. **`위키/index.md` 먼저 읽기** — 전체 위키 구조 파악 (2KB)
2. **필요한 페이지만 선택적 로딩** — 관련 concepts/entities/comparisons
3. **Wikilink `[[문서명]]`** 으로 상호 참조

## 프로젝트 컨텍스트

### 현재 프로젝트: 파수의 등대 (pasu-platform)
- Flask 기반 경제·금융 뉴스 플랫폼
- Render 배포: `https://pasu-lighthouse.onrender.com`
- 디자인: Toss/Saveticker 융합 라이트 테마
- 파스텔 핑크 물결 배경 + 등대 워터마크

### 현재 Phase: 2.5 고급화 리디자인
- 작업 계획서: `DESIGN_PLAN.md` 참조
- 4개 작업: 텍스트박스, 이미지삭제, 중앙워터마크, Lucide 픽토그램

### 컨벤션
- 한국어 응답, 전문적·주인친화적 톤
- 디자인 작업 시: 변경 최소화, 기존 테마 유지
- 수정 후 `python app.py` 검증 필수

### 협업 체계
- Claude Code(Opus) = 디자인 생성
- Hermes(달수) = 데이터 수집·검증·배포
- Codex(GPT) = Claude Code와 동일한 역할 수행 시 사용
