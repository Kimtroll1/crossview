# CrossView — GEMINI.md

> 이 파일은 Gemini CLI가 프로젝트 컨텍스트를 이해하기 위한 파일입니다.

---

## 프로젝트 개요

- **서비스명:** CrossView
- **슬로건:** 내 생각, 내가 지킨다
- **한 줄 정의:** 유튜브 뉴스 영상의 편향과 설득 구조를 즉시 시각화해, 사용자가 주체적으로 미디어를 소비하도록 돕는 도구
- **형태:** 웹 데모(MVP) → 크롬 확장 프로그램(다음 버전)
- **성격:** 해커톤 프로젝트 / 수익 모델 없음 / 빠른 프로토타이핑 우선

---

## 타겟 사용자 (페르소나)

- **이름:** 김지현
- **나이/직업:** 23세, 대학교 3학년
- **행동 패턴:** 유튜브로 시사 뉴스를 매일 소비하지만 깊이 공부하기보다 가볍게 흐름을 파악하는 편
- **핵심 불편함:** "이 영상 너무 몰아가는 거 아니야?", "댓글이 여론 전체인 것처럼 느껴지는데" 라는 찝찝함을 느끼지만, 해소 방법을 몰라 그냥 넘김
- **행동 장벽:** 팩트체크 사이트를 찾아가는 순간 소비 흐름이 끊기기 때문에 실제로 확인 행동을 하지 않음

---

## 핵심 기능 (MVP 범위)

| # | 기능 | 설명 |
|---|---|---|
| 1 | 유튜브 URL 입력 | 분석할 영상 링크를 입력해 분석 시작 (데모 방식) |
| 2 | 핵심 주장 요약 | 제목·설명·자막 기반으로 영상의 주장을 2~3줄로 요약 |
| 3 | 설득 방식 진단 | 감정 자극 / 단정적 언어 / 반복 강조 / 선택적 사례 등 설득 기법 라벨 표시 |
| 4 | 댓글 여론 분석 | 상위 댓글 감성 분류 및 찬반 분포 시각화 |
| 5 | 다른 관점 제시 | 같은 이슈를 반대 시각에서 보는 2~3문장 요약 |
| 6 | 웹 단일 페이지 | 로그인 없이 URL 입력만으로 사용 가능 |

---

## 기술 스택 (예정)

- **Frontend:** 웹 단일 페이지 (HTML/CSS/JS 또는 React)
- **AI 분석:** Gemini API (영상 요약, 설득 기법 분류, 다른 관점 생성)
- **댓글 수집:** YouTube Data API v3
- **자막 추출:** YouTube Transcript API 또는 영상 메타데이터
- **다음 버전:** 크롬 확장 프로그램 (Manifest V3)

---

## 디렉토리 구조 (예상)

```
crossview/
├── GEMINI.md              # 이 파일
├── README.md
├── index.html             # 웹 데모 진입점
├── src/
│   ├── api/
│   │   ├── gemini.js      # Gemini API 호출
│   │   └── youtube.js     # YouTube Data API / 자막 추출
│   ├── components/
│   │   ├── SummaryCard.js     # 핵심 주장 요약 UI
│   │   ├── PersuasionTags.js  # 설득 기법 라벨
│   │   ├── CommentChart.js    # 댓글 찬반 분포 시각화
│   │   └── OtherPerspective.js # 다른 관점 제시
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

## Gemini API 활용 포인트

### 1. 핵심 주장 요약
```
영상 제목, 설명, 자막 텍스트를 입력으로 받아
이 영상이 주장하는 핵심 내용을 2~3줄로 요약해줘.
중립적인 언어를 사용하고, 영상의 프레임을 그대로 반영할 것.
```

### 2. 설득 기법 진단
```
아래 텍스트에서 사용된 설득 기법을 분류해줘.
분류 기준: 감정 자극 / 단정적 언어 / 반복 강조 / 선택적 사례 / 책임 전가 / 맥락 생략
각 기법이 사용된 근거 문장도 함께 표시해줘.
```

### 3. 다른 관점 제시
```
아래 영상의 주제에 대해, 영상과 반대되는 시각에서
어떻게 볼 수 있는지 2~3문장으로 요약해줘.
특정 입장을 지지하지 말고, 논리적 반론 구조로 작성할 것.
```

---

## 코딩 컨벤션 및 주의사항

- **언어:** JavaScript (또는 TypeScript)
- **API 키:** 환경변수로 관리 (`.env`), 절대 하드코딩 금지
- **에러 처리:** YouTube 자막 없는 영상, 댓글 비활성화 영상 케이스 반드시 처리
- **YouTube API 할당량:** Data API v3 일일 할당량(10,000 units) 주의, 댓글 수집은 최대 상위 50개로 제한
- **응답 언어:** Gemini 프롬프트에 항상 "한국어로 응답해줘" 명시

---

## 현재 상태 및 우선순위

- [ ] YouTube URL 파싱 및 메타데이터 추출
- [ ] Gemini API 연동 및 요약 프롬프트 테스트
- [ ] 댓글 감성 분류 로직 구현
- [ ] UI 컴포넌트 개발 (SummaryCard → PersuasionTags → CommentChart → OtherPerspective 순)
- [ ] 웹 데모 통합 테스트
- [ ] 크롬 확장 포팅 (다음 버전)

---

## 참고 문서

- 기획서: `docs/crossview_onepager.html`
- 발표자료: `docs/CrossView_Deck.pptx`
- YouTube Data API: https://developers.google.com/youtube/v3
- Gemini API: https://ai.google.dev/docs
- Chrome Extension Manifest V3: https://developer.chrome.com/docs/extensions/mv3
