# CrossView
> **내 생각, 내가 지킬까말까**

CrossView는 유튜브 뉴스 및 시사 시청 중 발생할 수 있는 편향과 설득 구조를 실시간으로 감지하고, AI 기반의 다각도 분석과 다른 관점의 정보를 제공하여 사용자의 미디어 리터러시를 돕는 **크롬 확장 프로그램**입니다.

---

## ✨ 핵심 기능

- 🔍 **실시간 편향성 분석**: 영상 스크립트와 댓글을 분석하여 감정 쏠림 및 정치적 편향도를 시각화합니다.
- 🤖 **AI 분석 및 요약**: Gemini AI를 활용해 영상의 핵심 내용을 요약하고 논리적 허점이나 의심 신호를 포착합니다.
- 💬 **댓글 흐름 분석**: 현재 로드된 댓글의 전반적인 반응과 여론의 쏠림 현상을 분석합니다.
- 🔄 **다른 관점 및 검증 제안**: 시청 중인 영상과 다른 시각의 기사, 유튜브 영상, 또는 비판적 사고를 위한 질문을 제시합니다.
- 🌓 **다크/라이트 모드 지원**: 유튜브 테마에 맞춘 자연스러운 UI를 제공합니다.

---

## 🛠 기술 스택

### Backend
- **Language**: Python 3.10+
- **Framework**: FastAPI
- **AI**: Google Gemini (GenAI SDK)
- **Deployment**: Render (준비됨)

### Extension
- **Manifest**: V3
- **Frontend**: Vanilla JS, CSS
- **API Communication**: Fetch API

---

## 🗂 프로젝트 구조

```
crossview/
├── backend/               # FastAPI 기반 분석 서버
│   ├── app/
│   │   ├── routes/        # API 엔드포인트 (analyze)
│   │   ├── schemas/       # Pydantic 데이터 모델
│   │   ├── services/      # AI 연동 및 비즈니스 로직
│   │   └── main.py        # 서버 진입점
│   └── requirements.txt   # 의존성 패키지 목록
├── extension/             # 크롬 확장 프로그램
│   ├── manifest.json      # 확장 프로그램 설정
│   ├── content.js         # 유튜브 페이지 삽입 로직
│   ├── background.js      # 백그라운드 서비스 워커
│   └── crossview.css      # 확장 프로그램 스타일
├── web/                   # 분석 리포트 웹 페이지
└── docs/                  # 기획 및 구현 계획 문서
```

---

## 🚀 시작하기

### 1. Backend 설정

```bash
cd backend
# 가상환경 생성 및 활성화
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

`backend/.env` 파일을 생성하고 설정을 추가합니다.
```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-lite
```

서버 실행:
```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Extension 설치

1. 브라우저에서 `chrome://extensions/` 접속
2. 우측 상단의 **개발자 모드** 활성화
3. **압축해제된 확장 프로그램을 로드합니다** 버튼 클릭
4. 프로젝트의 `extension` 폴더 선택

---

## 🔍 사용 방법

1. 유튜브에서 시사/뉴스 영상을 재생합니다.
2. 영상 우측(또는 하단)에 CrossView 패널이 나타납니다.
3. **[분석 시작]** 버튼을 누르면 AI가 현재 영상의 내용을 분석합니다.
4. 요약, 편향도, 댓글 반응, 그리고 다른 관점의 정보를 확인합니다.

---

## 🗺 로드맵

- [x] **v0.3.5**: Gemini API 연동 및 기본 UI 완성
- [ ] **v0.5.0**: YouTube Data API를 통한 공식 자막/댓글 수집 안정화
- [ ] **v0.7.0**: 검색 API(SerpApi 등) 연동을 통한 실시간 팩트체크 기사 연결
- [ ] **v1.0.0**: 정식 배포 및 개인별 미디어 리터러시 히스토리 제공

---

## 👥 팀
**CHUMMY**  
미디어 리터러시를 위한 AI 솔루션 프로젝트 (2026)

---

## 📄 라이선스
MIT License
