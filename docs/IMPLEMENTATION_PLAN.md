# CrossView 2.0 구현 상태

## 이번 버전 완료

- 확장 UI 순서 개편: 정치 방향 → 편향 신호 → 댓글 → 다관점 자료 → 요약
- 편향 신호 4종과 판단 근거
- 댓글 의견 쏠림·감정 강도
- YouTube Data API 실제 영상 검색
- Gemini Search grounding 실제 웹 출처 검색
- Gemini URL Context 공개 문서 내용 확인
- `videoId` 분석 캐시와 24시간 검색 캐시
- 로컬 계정 및 Google 로그인 구조
- 웹·확장 프로그램 6자리 연결 코드
- 사용자별 시청 기록과 추천 자료 클릭 기록
- 주간·월간 개인 리포트
- 이메일·Slack·Discord 전송 설정
- 시간별 Cron 전송 작업
- Backend 통합 테스트와 Frontend production build

## 운영 전 필요한 외부 설정

- Gemini API 키
- YouTube Data API 키
- Google OAuth Client ID(선택)
- Resend API 키와 인증된 발신 도메인(이메일 사용 시)
- Slack/Discord Incoming Webhook(각 사용자 설정)
- 운영용 PostgreSQL
- HTTPS 배포 주소와 Chrome Extension host permission

## 후속 고도화

1. 전문가가 라벨링한 편향 평가 데이터셋
2. 모델별 반복 결과와 사람 평가 비교 대시보드
3. Alembic 정식 마이그레이션
4. 계정 삭제·데이터 내보내기·보존 정책
5. 영상 프레임·음성 기반 합성 미디어 탐지 모델
6. 검색 품질 A/B 테스트와 출처별 신뢰 정책
7. 다국어 분석
