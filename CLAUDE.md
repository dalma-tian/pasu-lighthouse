# 파수의 등대 — Phase 1.6: 전체 페이지 파스텔 핑크 물결 배경

## 수정사항

### 현재 문제
- 히어로 섹션(220px)에만 그라데이션 있음
- 그 아래는 그냥 흰색 배경 → 단절된 느낌

### 변경 방향
- **body 전체 배경**을 파스텔 핑크 물결 패턴으로 교체
- 여러 개의 부드러운 radial-gradient 타원이 페이지 전체에 은은하게 퍼짐
- 히어로 섹션 배경은 투명하게 → body 배경이 자연스럽게 비침
- 뉴스 카드, 필터바, 탭바는 흰색 배경 유지 (가독성)
- 카드 hover 시 살짝 핑크빛 그림자

### CSS 스펙

```css
body {
  background-color: #fef5f7;
  background-image: 
    radial-gradient(ellipse at 15% 30%, rgba(252, 228, 236, 0.7) 0%, transparent 55%),
    radial-gradient(ellipse at 85% 15%, rgba(248, 187, 208, 0.4) 0%, transparent 50%),
    radial-gradient(ellipse at 60% 70%, rgba(232, 234, 246, 0.5) 0%, transparent 55%),
    radial-gradient(ellipse at 10% 85%, rgba(252, 228, 236, 0.5) 0%, transparent 45%),
    radial-gradient(ellipse at 90% 55%, rgba(248, 187, 208, 0.3) 0%, transparent 45%),
    radial-gradient(ellipse at 40% 50%, rgba(255, 255, 255, 0.8) 0%, transparent 60%);
  background-attachment: fixed;
}
```

### 히어로 섹션
- 배경을 `transparent`로 변경 → body 물결이 그대로 비침
- 텍스트 + 일러스트는 그대로

### 카드
- 배경은 흰색 유지
- hover 그림자에 살짝 핑크빛: `box-shadow: 0 4px 20px rgba(248, 187, 208, 0.25);`

## 수정 파일
1. `static/style.css` — body 배경 교체, 히어로 배경 transparent, 카드 hover 그림자
2. 변경 최소화. 나머지 전부 그대로.
