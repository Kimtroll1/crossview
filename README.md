# CrossView

> **내 생각, 내가 지킨다**  
> 유튜브 뉴스·시사 영상 시청 중 스크립트 기반으로 편향도, AI 생성 의심 여부, 다른 관점 자료를 보여주고  
> 사용자의 시청 기록을 기반으로 개인 미디어 소비 리포트를 제공하는 AI 미디어 리터러시 서비스

---

## v3에서 반영된 기능

### Chrome Extension

- 유튜브 영상 페이지 접속 시 오른쪽 추천 영역에 CrossView 패널 자동 삽입
- 영상이 바뀌면 URL 변화를 감지해 자동으로 새 영상 정보 인식
- 현재 영상 제목, 채널명, URL, videoId, 설명, 가능한 경우 화면 내 스크립트 텍스트 수집
- 분석은 기본적으로 **스크립트/설명 기반**
- 정치·시사 영상으로 판단될 때만 정치 성향도 바 표시
- 정치 영상이 아니어도 사용자가 원하면 `정치 성향도 참고로 보기` 버튼으로 바 표시 가능
- AI 생성 의심 여부 경고
- 비슷한 관점 / 다른 관점 / 검증용 자료 표시
  - 유튜브 영상뿐 아니라 기사/웹 자료/AI 요약 답변까지 표시 가능
- CrossView 패널 접기/펼치기
- YouTube 다크모드/라이트모드 자동 감지
- 사용자가 CrossView 자체 테마를 직접 전환 가능
- 백엔드가 꺼져 있으면 mock 분석으로 자동 대체
- FastAPI 백엔드에 Gemini API 실제 연동 추가
- `.env`에서 `AI_PROVIDER=gemini`로 설정하면 Gemini 분석 사용

### Backend

- FastAPI 기반 mock 분석 서버
- `/api/analyze`
- 스크립트/설명 기반 분석을 받는 형태로 스키마 확장
- 나중에 Gemini, Groq, OpenAI 등 AI Provider 교체 가능

---

## 폴더 구조

```txt
crossview_mvp_v2/
├── extension/
│   ├── manifest.json
│   ├── content.js
│   ├── background.js
│   └── crossview.css
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── routes/
│       │   └── analyze.py
│       ├── schemas/
│       │   └── analysis.py
│       └── services/
│           └── ai_service.py
├── web/
│   ├── index.html
│   ├── style.css
│   └── report.js
├── .env.example
└── README.md
```

---

## Chrome Extension 실행 방법

1. Chrome 주소창에 `chrome://extensions` 입력
2. 오른쪽 위 **개발자 모드** 활성화
3. **압축해제된 확장 프로그램 로드** 클릭
4. 반드시 `crossview_mvp_v2/extension` 폴더 선택
5. 유튜브 영상 페이지 접속
6. 오른쪽 추천 영역 상단에 CrossView 패널 확인

---

## Backend 실행 방법

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# backend/.env 파일 생성 후 Gemini 키 입력
# AI_PROVIDER=gemini
# GEMINI_API_KEY=your_key_here
# GEMINI_MODEL=gemini-2.5-flash-lite

uvicorn app.main:app --reload --port 8000
```

백엔드가 꺼져 있어도 확장 프로그램은 mock 분석으로 작동합니다.

---

## 다음 구현 순서

1. YouTube Transcript 수집 로직 강화
2. YouTube Data API로 댓글/설명/검색 결과 연결
3. Gemini 분석 프롬프트 고도화
4. SerpApi 또는 검색 API로 기사/웹 자료 검색 연결
5. PostgreSQL에 사용자별 분석 기록 저장
6. Web Report에서 실제 사용자 리포트 표시

---

## 표현 원칙

CrossView는 AI 결과를 확정 판정처럼 보여주지 않습니다.

- `추정 편향도`
- `AI 생성 가능성`
- `다른 관점일 수 있는 자료`
- `검증용 자료`
- `추가 확인 필요`

처럼 사용자가 직접 판단하도록 돕는 표현을 사용합니다.

---

## Gemini API 사용 방법

1. Google AI Studio에서 Gemini API 키를 발급받습니다.
2. `backend/.env` 파일을 생성합니다.
3. 아래 내용을 입력합니다.

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

4. 백엔드를 실행합니다.

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

5. 유튜브 영상 페이지에서 CrossView가 자동 분석을 실행합니다.

API 키가 없거나 Gemini 호출에 실패하면 자동으로 mock 분석 결과를 사용합니다.


---

## v3.1 Fix

- `content.js` 첫 줄에 들어간 불필요한 문자로 인한 `Invalid or unexpected token` 오류 수정
- `ai_service.py` 첫 줄 불필요 문자 수정


---

## v3.2 Fix

- `다시 분석하기` 버튼을 누를 때 현재 유튜브 영상의 제목, 제작자, 분석 기준을 다시 읽도록 수정
- YouTube SPA 이동 후 이전 영상 제목/채널명이 남는 문제 완화
- 새 영상 페이지 진입 직후 DOM 렌더링이 늦을 때를 대비해 최신 정보 재확인 로직 추가


---

## v3.3 Update

- CrossView 패널 구조를 `영상 요약 → 분석 기준 → 댓글 흐름 → 편향도 → AI 의심 → 추천 자료 → 체크리스트` 순서로 재정리
- 영상 요약 카드 최상단 추가
- 주요 주장, 근거 요약, 주의해서 볼 표현/구조 추가
- 댓글 흐름 분석 카드 추가
- 화면에 로드된 댓글 일부를 수집해 백엔드로 전달
- Gemini 프롬프트에 `summary`, `mainClaims`, `evidenceSummary`, `cautionPoints`, `commentAnalysis` 관련 필드 추가
- 백엔드 응답 스키마 확장


---

## v3.4 Fix

- v3.3에서 누락된 `getFreshYouTubeContextWithRetry()` 함수 복구
- v3.3에서 누락된 `updateCurrentVideoCard()` 함수 복구
- 영상 이동 후 다시 분석 시 현재 영상 제목/채널/분석 기준 갱신 유지
- `transcript+comments` 같은 복합 분석 기준에서도 완료 문구가 정상 표시되도록 수정

---

## v3.5 Render Ready

- Render 배포용 `render.yaml` 추가
- `backend/runtime.txt` 추가
- `extension/config.js` 추가
- Render URL만 바꾸면 확장이 외부 서버를 호출할 수 있도록 수정
- `https://*.onrender.com/*` host permission 추가

Render 배포 후 `extension/config.js`에서 아래 줄만 수정하세요.

```js
window.CROSSVIEW_BACKEND_URL = "https://YOUR_RENDER_SERVICE.onrender.com/api/analyze";
```
