# CrossView 2.0 Architecture

```text
YouTube watch page
  └─ Chrome Extension
      ├─ transcript / description / visible comments
      ├─ extension access token
      └─ FastAPI /api/analyze
            ├─ videoId analysis cache (PostgreSQL)
            ├─ Gemini bias analysis
            ├─ YouTube Data API search
            ├─ Gemini Google Search grounding
            ├─ Gemini URL Context page inspection
            └─ per-user watch history

Next.js Web
  ├─ local or Google login
  ├─ extension link code
  ├─ weekly/monthly personal report
  ├─ resource click tracking
  └─ report delivery settings

Hourly Cron
  └─ email / Slack / Discord delivery
```

## 공용 데이터와 개인 데이터 분리

공용 캐시:

- `videos`
- `analyses`
- `recommendations`

개인 데이터:

- `users`
- `watch_history`
- `resource_clicks`
- `extension_devices`
- `report_subscriptions`
- `report_deliveries`

같은 영상은 한 번 분석하고 여러 사용자가 결과를 공유합니다. 사용자의 시청 기록과 추천 자료 클릭만 별도로 저장합니다.

## 인증

- 웹 토큰: 기본 14일
- 확장 토큰: 기본 180일
- 확장 프로그램은 웹 설정 페이지에서 생성한 일회용 6자리 코드로 연결
- 코드는 해시로 저장되며 10분 후 만료되고 한 번만 사용할 수 있음
- 확장 토큰에는 device ID가 포함되며 서버의 활성 기기와 일치해야 함

## 검색 안전 원칙

- 모델이 직접 작성한 임의 URL을 사용하지 않음
- Google Search grounding metadata와 YouTube Data API에서 확인된 URL만 후보로 저장
- URL Context는 이미 확인된 URL의 내용만 요약하며 새로운 링크를 추가할 수 없음
- 같은 도메인은 최종 목록에서 한 번만 사용
- 광고·쇼핑 도메인 제외
- 실제 링크 여부와 AI가 추정한 관점·관련성은 별도 필드로 구분
