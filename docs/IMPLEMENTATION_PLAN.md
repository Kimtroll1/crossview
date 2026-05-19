# CrossView v3 구현 계획

## 이번 버전에 반영된 요구사항

- Gemini API 실제 연동
- `.env`에서 `AI_PROVIDER=gemini`로 바꾸면 Gemini 분석 사용
- API 키가 없거나 호출 실패 시 mock 분석으로 자동 fallback
- 분석 결과는 JSON으로 받아 Extension UI에 그대로 표시
- 정치 영상이 아니면 정치 편향도 바를 기본으로 숨김
- 사용자가 원하면 정치 편향도 바를 강제로 볼 수 있음
- 비슷한 관점, 다른 관점, 검증용 자료는 유튜브뿐 아니라 기사/웹 자료도 포함
- 자료가 없을 경우 AI 답변/확인 질문 제공

## 실행 순서

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`backend/.env` 생성:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

서버 실행:

```bash
uvicorn app.main:app --reload --port 8000
```

## 다음 해야 할 일

1. 실제 YouTube Transcript 수집 강화
2. YouTube Data API로 댓글 수집
3. Gemini 프롬프트 평가 및 개선
4. SerpApi/검색 API로 기사 검색 연결
5. 사용자별 기록 저장
6. 웹 리포트 실제 데이터 연결


## v3.3 반영 사항

- 영상 요약을 패널 최상단에 표시한다.
- 댓글 흐름 분석을 별도 카드로 표시한다.
- 분석 기준에 스크립트/댓글/설명 포함 여부를 표시한다.
- 현재 버전의 댓글 수집은 YouTube 페이지에 화면상 로드된 댓글만 감지한다.
- 다음 단계에서는 YouTube Data API `commentThreads.list`로 댓글 수집을 안정화해야 한다.
