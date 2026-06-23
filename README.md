# CrossView 2.0

> 유튜브 영상의 정치 방향과 편향 신호를 시청 중 보여주고, 실제 다른 관점 자료와 개인 미디어 소비 리포트까지 연결하는 서비스

CrossView 2.0은 **Chrome Extension + FastAPI + PostgreSQL + Next.js**로 구성됩니다.

## 핵심 기능

### 유튜브 확장 프로그램

화면 순서는 긴 요약보다 시각 정보를 먼저 보여주도록 바뀌었습니다.

1. 정치 성향 스펙트럼 `진보 -5 ~ 보수 +5`
2. 편향 신호 4종
   - 감정·선동
   - 선택적 근거
   - 관점 누락
   - 출처 편중
3. 댓글 흐름
   - 의견 쏠림
   - 감정 강도
   - 짧은 서술형 요약
4. 실제 다른 관점 영상·기사·공식 자료
5. 영상 요약과 주요 주장
6. AI 생성 의심 신호와 판단 체크리스트

### 실제 다관점 탐색

- YouTube Data API로 실제 영상 후보 검색
- Gemini Google Search grounding으로 실제 웹 출처 검색
- Gemini URL Context로 공개 기사·공식 자료 본문을 다시 확인
- 검색 결과에서 확인된 URL만 저장
- 다른 관점·중립 해설·검증 자료·비슷한 관점으로 분류
- 동일 도메인 결과 중복 제한
- 영상별 검색 결과 24시간 캐싱

### 사용자 계정과 개인 데이터

- 이메일·비밀번호 회원가입/로그인
- Google Identity Services 로그인 선택 지원
- 웹에서 6자리 연결 코드를 생성해 Chrome Extension과 연결
- 영상 분석 결과는 `videoId` 기준으로 공용 캐시
- 시청 기록과 추천 자료 클릭은 사용자별 저장
- 기존 `demo-user` 게스트 분석도 유지

### 웹 리포트

- 최근 7일/30일 전환
- 진보·중립·보수 시청 분포
- 편향 신호 누적 프로필
- AI 생성 의심 콘텐츠 비율
- 댓글 의견 쏠림·감정 강도 평균
- 다른 관점 자료 탐색률
- 최근 분석 기록과 실제 추천 자료

### 정기 리포트 전송

사용자 설정에 따라 주간 또는 월간 리포트를 전송할 수 있습니다.

- 이메일: Resend
- Slack: Incoming Webhook
- Discord: Incoming Webhook
- 사용자 시간대, 전송 시각, 요일 또는 날짜 설정
- Webhook URL 암호화 저장
- 시간별 Cron 작업에서 전송 대상만 계산

---

## 프로젝트 구조

```text
crossview-complete/
├─ backend/          FastAPI, Gemini, YouTube API, 인증, DB, 정기 전송
├─ extension/        Chrome Manifest V3 확장 프로그램
├─ frontend/         Next.js 로그인·리포트·설정 화면
├─ docs/             설계·편향 기준·배포 문서
├─ docker-compose.yml
└─ render.yaml
```

## 로컬 실행

### 1. PostgreSQL

Docker Desktop을 실행한 뒤 프로젝트 최상위 폴더에서:

```powershell
docker compose up -d
docker ps
```

`crossview-postgres`가 `Up`이면 정상입니다.

### 2. Backend

새 PowerShell:

```powershell
cd backend
python -m venv .venv
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

확인:

```text
http://localhost:8000/api/health
```

처음에는 `.env`의 `AI_PROVIDER=mock`으로도 전체 흐름을 테스트할 수 있습니다.

### 3. Frontend

새 PowerShell:

```powershell
cd frontend
Copy-Item .env.local.example .env.local
npm.cmd install
npm.cmd run dev
```

- 로그인: `http://localhost:3000/login`
- 리포트: `http://localhost:3000/dashboard`
- 기록: `http://localhost:3000/history`
- 다관점 탐색: `http://localhost:3000/explore`
- 계정·전송 설정: `http://localhost:3000/settings`

### 4. Chrome Extension

1. Chrome에서 `chrome://extensions` 접속
2. 개발자 모드 활성화
3. **압축해제된 확장 프로그램을 로드합니다** 선택
4. 프로젝트의 `extension` 폴더 선택
5. 유튜브 영상 페이지 새로고침

웹에서 로그인한 뒤 `/settings`에서 6자리 코드를 만들고, 확장 패널에 입력하면 개인 계정과 연결됩니다.

---

## 실제 API 설정

`backend/.env`:

```env
APP_VERSION=2.0.0
FRONTEND_URL=http://localhost:3000

AI_PROVIDER=gemini
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_SEARCH_MODEL=gemini-3.1-flash-lite
ENABLE_GEMINI_SEARCH=true
ENABLE_URL_CONTEXT=true
RESOURCE_CACHE_HOURS=24
YOUTUBE_API_KEY=YOUR_YOUTUBE_DATA_API_KEY

DATABASE_URL=postgresql+psycopg2://crossview:crossview@localhost:5432/crossview
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://www.youtube.com,https://youtube.com

JWT_SECRET=충분히_긴_랜덤_문자열
GOOGLE_CLIENT_ID=
SECRETS_ENCRYPTION_KEY=

RESEND_API_KEY=
REPORT_FROM_EMAIL=CrossView <report@your-domain.com>
```

`frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=
```

Google 로그인을 사용하려면 프론트엔드와 백엔드에 같은 OAuth Web Client ID를 넣습니다. 로컬 계정 로그인은 별도 키 없이 동작합니다.

`SECRETS_ENCRYPTION_KEY`가 비어 있으면 개발 편의를 위해 `JWT_SECRET`에서 암호화 키를 유도합니다. 운영 환경에서는 별도 랜덤 값을 고정해서 사용하세요.

## 정기 리포트 테스트

설정 화면에서 이메일, Slack 또는 Discord 채널을 켠 뒤 **테스트 전송**을 누릅니다.

수동으로 예약 작업을 실행하려면:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts/send_due_reports.py
```

운영 환경에서는 이 명령을 매시간 실행하도록 Cron을 설정합니다. 스크립트가 각 사용자의 시간대와 전송 설정을 확인합니다.

## 테스트

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

프론트엔드 빌드:

```powershell
cd frontend
npm.cmd run build
```

확장 프로그램 JavaScript 문법 확인:

```powershell
node --check extension/background.js
node --check extension/config.js
node --check extension/content.js
```

## 데이터·비용 제어

- AI 분석 결과는 `videoId` 기준 PostgreSQL 영구 캐시
- 사용자가 **다시 분석**을 누를 때만 Gemini 분석 갱신
- 실제 다관점 검색 결과는 기본 24시간 캐시
- 동일 사용자의 동일 영상 기록은 중복 행 대신 최근 시청 시각 갱신
- Gemini Search/URL Context와 YouTube 검색은 API 키가 있을 때만 실행

## 정확한 표현

- 정치 성향 **판정**이 아니라 정치 편향도 **추정**
- AI 생성 영상 **탐지**가 아니라 텍스트 기반 **AI 생성 의심 신호 분석**
- 댓글 동의·반대 비율이 아니라 **의견 쏠림과 감정 강도**
- 추천 자료의 점수도 확정적인 매체 신뢰도 판정이 아니라 검색 관련성과 출처 신호에 기반한 보조 지표

## 보안 주의

- `.env`, API 키, JWT 비밀키, Slack/Discord Webhook을 GitHub에 커밋하지 마세요.
- 운영 환경에서는 HTTPS API 주소를 `extension/config.js`에 설정하세요.
- Webhook URL은 서버에서 암호화해 저장하며 브라우저에는 마스킹된 값만 반환합니다.

## 팀

CHUMMY · CrossView · 2026
