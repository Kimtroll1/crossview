"""Call a running CrossView API repeatedly and compare Gemini results.

Run from backend/: python scripts/check_consistency.py
The script performs three forced analyses and then one cached request.
"""

import json
from statistics import mean
from urllib.request import Request, urlopen

API_URL = "http://localhost:8000/api/analyze"
RUNS = 3

payload = {
    "userId": "consistency-check",
    "videoId": "crossview-consistency-sample",
    "url": "https://www.youtube.com/watch?v=crossview-consistency-sample",
    "title": "대통령 정책 논란과 여야 반응 분석",
    "channelName": "CrossView Test",
    "description": "정부 정책에 대한 찬반 논거와 여야 반응을 설명하는 테스트 데이터입니다.",
    "transcript": "정책의 기대 효과를 설명한 뒤 야당의 비판과 전문가의 반론을 함께 소개합니다.",
    "commentsText": "1. 정책을 지지합니다.\n2. 반대 근거도 확인해야 합니다.\n3. 양쪽 자료가 더 필요합니다.",
    "commentsCount": 3,
    "analysisSource": "transcript+comments+description",
    "forceRefresh": True,
}


def post(data: dict) -> dict:
    request = Request(
        API_URL,
        data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


results = []
for index in range(RUNS):
    result = post(payload)
    results.append(result)
    print(
        f"run {index + 1}: score={result['biasScore']}, "
        f"confidence={result['biasConfidence']}, criteria={result['biasCriteria']}"
    )

scores = [item["biasScore"] for item in results]
confidences = [item["biasConfidence"] for item in results]
print(f"score range: {min(scores)} ~ {max(scores)}")
print(f"average confidence: {mean(confidences):.2f}")
print("consistent score:", len(set(scores)) == 1)

payload["forceRefresh"] = False
cached = post(payload)
print("cache check:", cached.get("cached") is True)
