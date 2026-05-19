# CrossView
> **내 생각, 내가 지킨다**
# CrossView

> 내 생각, 내가 지킨다
> 유튜브 뉴스 시청 중 편향과 설득 구조를 감지하고,
> 다른 관점과 검증 질문을 제시해 사용자가 스스로 판단하도록 돕는 **크롬 확장 기반 미디어 리터러시 도구**
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

1. 

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