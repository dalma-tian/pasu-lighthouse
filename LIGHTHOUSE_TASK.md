# 파수의 등대 — 등대 워터마크 (Opus 작업)

## 목표
`static/lighthouse-hero.png` (3D 등대 일러스트 - 핑크 등대 + 금화 + 화살표)를 배경 없는 워터마크로 만들어 뉴스피드 배경에 은은하게 띄우기.
주변 아티팩트(금화, 화살표)가 두둥실 떠다니는 CSS 애니메이션 추가.

## 작업 단계

### Step 1: 이미지 배경 제거
- `static/lighthouse-hero.png`에서 흰색/연한 배경 제거 → 투명 PNG로 저장
- 저장 경로: `static/lighthouse-watermark.png`
- **중요**: 원본 `lighthouse-hero.png`는 히어로 섹션에 쓰이므로 건드리지 말 것

### Step 2: CSS로 워터마크 + 플로팅 애니메이션
`static/style.css`에 추가:

```css
/* 등대 워터마크 */
.watermark-lighthouse {
  position: fixed;
  bottom: 60px;
  right: 40px;
  width: 280px;
  height: 280px;
  background: url('/static/lighthouse-watermark.png') no-repeat center/contain;
  opacity: 0.12;
  pointer-events: none;
  z-index: 0;
  animation: floatLighthouse 8s ease-in-out infinite;
}

/* 등대 주변 아티팩트(금화, 화살표) */
.watermark-artifacts {
  position: fixed;
  pointer-events: none;
  z-index: 0;
  opacity: 0.08;
}

.watermark-artifacts::before {
  content: '';
  position: fixed;
  bottom: 100px;
  right: 80px;
  width: 40px;
  height: 40px;
  background: radial-gradient(circle, #fbbf24 0%, transparent 70%);
  border-radius: 50%;
  animation: floatArtifact1 6s ease-in-out infinite;
}

.watermark-artifacts::after {
  content: '';
  position: fixed;
  bottom: 160px;
  right: 200px;
  width: 30px;
  height: 30px;
  background: radial-gradient(circle, #f472b6 0%, transparent 70%);
  border-radius: 50%;
  animation: floatArtifact2 7s ease-in-out infinite;
}

@keyframes floatLighthouse {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  25% { transform: translateY(-8px) rotate(0.5deg); }
  50% { transform: translateY(-4px) rotate(0deg); }
  75% { transform: translateY(-12px) rotate(-0.5deg); }
}

@keyframes floatArtifact1 {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.6; }
  33% { transform: translate(15px, -20px) scale(1.3); opacity: 0.3; }
  66% { transform: translate(-10px, -10px) scale(0.8); opacity: 0.5; }
}

@keyframes floatArtifact2 {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.5; }
  50% { transform: translate(-20px, -25px) scale(1.4); opacity: 0.2; }
}
```

### Step 3: HTML에 워터마크 요소 추가
`templates/index.html`, `templates/watchlist.html`, `templates/dashboard.html`, `templates/calendar.html` — `<body>` 바로 안쪽에:

```html
<div class="watermark-lighthouse"></div>
<div class="watermark-artifacts"></div>
```

---

## 중요
1. **속도/토큰 아껴라** — 배경 제거는 Python PIL로 처리 (rembg 라이브러리 사용)
2. 원본 이미지 `lighthouse-hero.png` 절대 손대지 말 것
3. 워터마크 opacity 0.10~0.15 수준으로 매우 은은하게
4. 애니메이션은 느리고 부드럽게 (8s 주기)
5. z-index 0으로 본문 콘텐츠 아래에 깔리게
6. **완료 후 `python app.py` 구동해서 200 OK 확인할 것**

## 수정 파일
1. `static/lighthouse-watermark.png` — 신규 생성
2. `static/style.css` — 워터마크 CSS 추가
3. `templates/index.html`, `watchlist.html`, `dashboard.html`, `calendar.html` — div 추가
