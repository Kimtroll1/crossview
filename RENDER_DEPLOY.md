# CrossView Render 배포 가이드

## 1. GitHub에 올리기

이 폴더 전체를 GitHub repository로 올립니다.

```bash
git init
git add .
git commit -m "Deploy CrossView API to Render"
git branch -M main
git remote add origin https://github.com/YOUR_ID/crossview.git
git push -u origin main
```

## 2. Render Web Service 만들기

Render Dashboard에서 New → Web Service를 선택하고 GitHub repository를 연결합니다.

수동 설정을 쓸 경우:

```txt
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

`render.yaml` Blueprint를 사용할 경우 repository root의 `render.yaml`을 기준으로 생성하면 됩니다.

## 3. 환경변수 설정

Render 서비스의 Environment 메뉴에서 아래 값을 넣습니다.

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

## 4. 배포 확인

배포 URL이 아래와 같다고 가정합니다.

```txt
https://crossview-api.onrender.com
```

브라우저에서 확인:

```txt
https://crossview-api.onrender.com/api/health
```

정상 응답 예시:

```json
{"ok":true,"service":"CrossView API","version":"0.3.5"}
```

## 5. Chrome Extension API 주소 바꾸기

`extension/config.js` 파일을 열고 아래 줄을 Render URL로 바꿉니다.

```js
window.CROSSVIEW_BACKEND_URL = "https://crossview-api.onrender.com/api/analyze";
```

그 다음 Chrome 확장 페이지에서 CrossView를 새로고침합니다.

## 6. 주의

- API 키는 절대 extension 폴더에 넣지 마세요.
- Gemini 키는 Render Environment Variables에만 넣으세요.
- Free instance는 잠들 수 있어 첫 요청이 느릴 수 있습니다.
