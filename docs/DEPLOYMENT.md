# 배포 체크리스트

## Backend

- `AI_PROVIDER=gemini`
- Gemini API 키와 실제 사용 가능한 모델 ID
- YouTube Data API 키
- Render Postgres 연결 문자열
- 강한 `JWT_SECRET`
- 고정 `SECRETS_ENCRYPTION_KEY`
- 프론트엔드 도메인을 `CORS_ORIGINS`에 추가
- Google OAuth를 사용할 경우 `GOOGLE_CLIENT_ID`
- 이메일을 사용할 경우 Resend API 키와 인증된 발신 주소

## Frontend

- `NEXT_PUBLIC_API_BASE_URL=https://배포된-api`
- `NEXT_PUBLIC_GOOGLE_CLIENT_ID`를 Backend와 동일하게 설정

## Extension

`extension/config.js`의 두 주소를 배포 주소로 변경합니다.

```js
window.CROSSVIEW_API_BASE_URL = "https://배포된-api";
window.CROSSVIEW_REPORT_URL = "https://배포된-web";
```

`manifest.json`의 `host_permissions`에 API 도메인을 추가하고 확장 프로그램을 다시 로드합니다.

## Cron

`python scripts/send_due_reports.py`를 매시간 실행합니다. 스크립트는 UTC 실행 시각을 사용자 시간대로 변환해 주간·월간 조건을 확인합니다.

## 운영 전 테스트

1. 회원가입/로그인
2. 확장 연결 코드 1회 사용 및 재사용 차단
3. 유튜브 영상 분석과 DB 캐시
4. 실제 YouTube/웹 검색 결과 URL
5. 웹에서 추천 자료 클릭 후 탐색률 증가
6. 주간/월간 리포트 전환
7. 이메일/Slack/Discord 테스트 전송
8. 서버 재시작 후 캐시와 사용자 기록 유지
