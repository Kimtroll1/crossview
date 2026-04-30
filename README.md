# CrossView
> **내 생각, 내가 지킨다**
> 유튜브 뉴스 영상의 편향과 설득 구조를 즉시 시각화해, 사용자가 주체적으로 미디어를 소비하도록 돕는 도구

---

## 🧩 프로젝트 소개

유튜브에서 시사 영상을 보다 보면, 어느 순간 영상의 프레임에 끌려가고 있다는 느낌을 받는다.  
자극적인 제목, 한쪽으로 기운 편집, 댓글 분위기가 조용히 판단을 흔든다.  
그 과정이 너무 자연스러워서, **내가 설득당하고 있다는 사실조차 인식하기 어렵다.**

CrossView는 그 "넘기는 순간"을 포착해, 시청 흐름을 깨지 않고 즉시 작동한다.  
AI가 정답을 대신 말하는 것이 아니라, 사용자가 **스스로 판단하도록** 실시간으로 돕는다.

---

## ✨ 핵심 기능

| 기능 | 설명 |
|---|---|
| 🔴 **가짜정보 의심 신호 감지** | 출처 불명, 과장 표현, 검증 부족 표현을 실시간으로 표시 |
| 📊 **편향성 분석** | 감정 쏠림, 진영 편향, 댓글 흐름의 극단적 쏠림 감지 |
| 🔄 **다른 관점 제안** | 반대 시각, 추가 확인 질문, 관련 키워드 제공 |
| ✅ **판단 체크리스트** | 누가 말했는가 / 근거가 있는가 / 다른 출처도 같은가 확인 유도 |

---

## 🗂 프로젝트 구조

```
crossview/
├── GEMINI.md              # Gemini CLI 컨텍스트 파일
├── README.md              # 이 파일
├── index.html             # 웹 데모 진입점
├── src/
│   ├── api/
│   │   ├── gemini.js      # Gemini API 호출 (요약·분석·관점 생성)
│   │   └── youtube.js     # YouTube Data API / 자막 추출
│   ├── components/
│   │   ├── SignalCard.js       # 가짜정보 의심 신호 UI
│   │   ├── BiasChart.js        # 편향성 분석 시각화
│   │   ├── PerspectiveCard.js  # 다른 관점 제시
│   │   └── CheckList.js        # 판단 체크리스트
│   └── utils/
│       └── parser.js      # URL 파싱, 데이터 정제
├── extension/             # 크롬 확장 (다음 버전)
│   ├── manifest.json
│   └── content.js
└── docs/
    ├── crossview_onepager.html
    └── CrossView_Deck.pptx
```

---

## 🚀 시작하기

### 요구 사항

- Node.js 18 이상
- Gemini API 키 ([Google AI Studio](https://aistudio.google.com)에서 발급)
- YouTube Data API v3 키 ([Google Cloud Console](https://console.cloud.google.com)에서 발급)

### 설치

```bash
git clone https://github.com/your-team/crossview.git
cd crossview
npm install
```

### 환경 변수 설정

`.env` 파일을 루트에 생성한다.

```env
GEMINI_API_KEY=your_gemini_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

> ⚠️ API 키는 절대 코드에 직접 넣지 말 것. `.env`는 `.gitignore`에 포함되어 있다.

### 실행

```bash
npm run dev
```

브라우저에서 `http://localhost:3000` 접속 후 유튜브 URL을 입력하면 분석이 시작된다.

---

## 🔍 사용 방법

1. 분석하고 싶은 유튜브 영상의 URL을 복사한다
2. CrossView 입력창에 붙여넣는다
3. 분석 결과 확인
   - 🔴 의심 신호가 감지된 표현 하이라이트
   - 📊 편향 유형 및 강도 시각화
   - 🔄 같은 이슈를 다른 시각으로 보는 2~3문장 요약
   - ✅ 스스로 확인할 수 있는 체크리스트

---

## 🛠 기술 스택

| 구분 | 기술 |
|---|---|
| Frontend | HTML / CSS / JavaScript (또는 React) |
| AI 분석 | Gemini API (`gemini-2.0-flash`) |
| 영상 데이터 | YouTube Data API v3 |
| 자막 추출 | YouTube Transcript API |
| 다음 버전 | Chrome Extension Manifest V3 |

---

## 📋 MVP 구현 범위

- [x] YouTube URL 파싱 및 메타데이터 추출
- [ ] Gemini API 연동 — 의심 신호 감지 프롬프트
- [ ] Gemini API 연동 — 편향성 분석 프롬프트
- [ ] Gemini API 연동 — 다른 관점 생성 프롬프트
- [ ] 판단 체크리스트 UI
- [ ] 웹 데모 통합 테스트
- [ ] 크롬 확장 포팅 (다음 버전)

---

## 🗺 로드맵

| 단계 | 내용 |
|---|---|
| **데모 (현재)** | URL 입력 기반 웹 페이지, 핵심 4기능 검증 |
| **v1.0** | 크롬 확장 프로그램, 유튜브 자막·댓글 자동 수집 |
| **v1.5** | 같은 이슈 다른 관점 영상 추천 |
| **v2.0** | 모바일 유튜브 공유 연동 |

---

## 👥 팀

**CHUMMY**  
해커톤 프로젝트 · 2026

---

## 📄 라이선스

MIT License
