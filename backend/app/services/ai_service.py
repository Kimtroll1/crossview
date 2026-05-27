\
import json
import os
import re
from urllib.parse import quote_plus

from app.schemas.analysis import VideoContext, AnalysisResponse, Resource


POLITICAL_KEYWORDS = [
    "정치", "대통령", "국회", "정부", "여당", "야당", "보수", "진보", "좌파", "우파",
    "선거", "정당", "의원", "민주당", "국민의힘", "정책", "탄핵", "외교", "안보"
]


class AIService:
    def __init__(self, provider: str = "mock"):
        self.provider = provider

    async def _fetch_transcript_backend(self, video_id: str) -> str:
        import asyncio
        def get_transcript():
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                api = YouTubeTranscriptApi()
                transcript_list = api.fetch(video_id, languages=['ko', 'en'])
                return "\n".join([item.text for item in transcript_list])
            except Exception:
                try:
                    from youtube_transcript_api import YouTubeTranscriptApi
                    api = YouTubeTranscriptApi()
                    transcript_list_obj = api.list(video_id)
                    for t in transcript_list_obj:
                        transcript_list = t.fetch()
                        return "\n".join([item.text for item in transcript_list])
                except Exception:
                    pass
            return ""
        return await asyncio.to_thread(get_transcript)

    async def _fetch_comments_backend(self, video_id: str, api_key: str) -> str:
        import asyncio
        def get_comments():
            try:
                from googleapiclient.discovery import build
                youtube = build('youtube', 'v3', developerKey=api_key)
                request = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=50,
                    textFormat='plainText',
                    order='relevance'
                )
                response = request.execute()
                comments = []
                for item in response.get('items', []):
                    snippet = item.get('snippet', {})
                    top_comment = snippet.get('topLevelComment', {})
                    comment_text = top_comment.get('snippet', {}).get('textDisplay', '').strip()
                    if comment_text:
                        comments.append(comment_text)
                return "\n".join([f"{i + 1}. {c}" for i, c in enumerate(comments)])
            except Exception as e:
                print(f"[CrossView] YouTube Data API failed to fetch comments: {e}")
            return ""
        return await asyncio.to_thread(get_comments)

    async def analyze_video(self, video: VideoContext) -> AnalysisResponse:
        # Try fetching transcript on the backend if missing
        if not video.transcript and video.videoId:
            try:
                fetched_transcript = await self._fetch_transcript_backend(video.videoId)
                if fetched_transcript:
                    video.transcript = fetched_transcript
                    print(f"[CrossView] Backend successfully fetched transcript for video {video.videoId}")
            except Exception as e:
                print(f"[CrossView] Backend failed to fetch transcript: {e}")

        # Try fetching comments via official API if YOUTUBE_API_KEY is configured
        youtube_api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
        if youtube_api_key and video.videoId:
            try:
                fetched_comments = await self._fetch_comments_backend(video.videoId, youtube_api_key)
                if fetched_comments:
                    video.commentsText = fetched_comments
                    video.commentsCount = len(fetched_comments.split("\n"))
                    print(f"[CrossView] Backend successfully fetched {video.commentsCount} comments via YouTube API")
            except Exception as e:
                print(f"[CrossView] Backend failed to fetch comments via YouTube API: {e}")

        # Update analysis source based on actual contents used
        video.analysisSource = self._source_used(video)

        if self.provider == "gemini":
            try:
                return self._analyze_with_gemini(video)
            except Exception as error:
                print(f"[CrossView] Gemini failed. Falling back to mock. Error: {error}")
                return self._mock_analyze(video)

        return self._mock_analyze(video)

    def _is_political(self, video: VideoContext) -> bool:
        text = f"{video.title} {video.description} {video.transcript} {video.commentsText}".lower()
        return any(keyword.lower() in text for keyword in POLITICAL_KEYWORDS)

    def _source_used(self, video: VideoContext) -> str:
        parts = []
        if video.transcript:
            parts.append("transcript")
        if video.commentsText:
            parts.append("comments")
        if video.description:
            parts.append("description")
        if not parts:
            parts.append("metadata")
        return "+".join(parts)

    def _source_label(self, source_used: str, comments_count: int = 0) -> str:
        labels = []
        if "transcript" in source_used:
            labels.append("스크립트")
        if "comments" in source_used:
            labels.append(f"댓글 {comments_count}개")
        if "description" in source_used:
            labels.append("영상 설명")
        if not labels:
            labels.append("제목·채널 메타데이터")
        return " + ".join(labels)

    def _analyze_with_gemini(self, video: VideoContext) -> AnalysisResponse:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing")

        from google import genai

        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite").strip()
        client = genai.Client(api_key=api_key)

        prompt = self._build_prompt(video)

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.2,
            },
        )

        raw_text = getattr(response, "text", "") or ""
        data = self._parse_json(raw_text)

        return self._normalize_gemini_response(data, video)

    def _build_prompt(self, video: VideoContext) -> str:
        transcript = (video.transcript or "").strip()
        description = (video.description or "").strip()
        comments_text = (video.commentsText or "").strip()

        source_used = self._source_used(video)
        source_label = self._source_label(source_used, video.commentsCount)

        transcript_part = transcript[:14000] if transcript else ""
        description_part = description[:7000] if description else ""
        comments_part = comments_text[:7000] if comments_text else ""

        return f"""
너는 CrossView라는 미디어 리터러시 도구의 분석 엔진이다.

목표:
- 유튜브 영상의 스크립트, 설명, 댓글을 바탕으로 사용자가 스스로 판단하도록 돕는다.
- 가장 먼저 영상 요약을 제공한다.
- 댓글이 있으면 댓글 흐름을 분석한다.
- 정치/시사 영상이면 좌우 정치 편향도를 -5부터 +5까지 추정한다.
- 정치/시사 영상이 아니면 isPolitical=false, biasScore=0으로 둔다.
- AI 생성 영상 또는 AI 음성/합성 가능성을 low/medium/high 중 하나로 추정한다.
- 유튜브 영상뿐 아니라 기사/웹 자료도 함께 확인할 수 있도록 검색 자료를 제안한다.
- 확정적으로 단정하지 말고 "가능성", "추정", "추가 확인 필요" 표현을 사용한다.

편향도 기준:
- -5: 강한 좌측 성향
- -3: 비교적 좌측 성향
- 0: 중립에 가까움
- +3: 비교적 우측 성향
- +5: 강한 우측 성향

댓글 흐름 분석 기준:
- commentMood: 동조적 / 비판적 / 분열됨 / 조롱·공격적 / 정보 부족 중 하나 또는 자연어
- commentIntensity: 낮음 / 보통 / 높음
- commentLeaning: 한쪽으로 강함 / 약간 쏠림 / 다양함 / 정보 부족
- commentWarningSignals: 비난성 표현, 단정적 표현, 음모론적 표현, 출처 없는 주장, 집단 조롱 등

중요:
- 반드시 JSON만 출력한다.
- 마크다운 코드블록을 쓰지 않는다.
- 모르는 내용은 지어내지 말고 "정보 부족"이라고 쓴다.
- biasScore는 반드시 -5~5 정수다.
- aiRisk는 반드시 low, medium, high 중 하나다.

현재 영상:
title: {video.title}
channelName: {video.channelName}
url: {video.url}
videoId: {video.videoId}
analysisSource: {source_label}

영상 설명:
{description_part}

스크립트:
{transcript_part}

댓글 텍스트:
{comments_part}

출력 JSON 형식:
{{
  "summary": "이 영상이 무엇을 주장하는지 2~3문장으로 요약",
  "mainClaims": ["주요 주장 1", "주요 주장 2", "주요 주장 3"],
  "evidenceSummary": "영상이 제시하는 근거 또는 근거 부족 여부",
  "cautionPoints": ["주의해서 봐야 할 표현/구조 1", "주의점 2"],

  "sourceUsed": "{source_used}",
  "sourceLabel": "{source_label}",
  "commentsIncluded": {str(bool(comments_text)).lower()},
  "commentsCount": {video.commentsCount},

  "commentMood": "댓글 전체 분위기",
  "commentIntensity": "낮음/보통/높음",
  "commentLeaning": "의견 쏠림 정도",
  "commentWarningSignals": ["주의 신호 1", "주의 신호 2"],

  "isPolitical": true,
  "biasScore": 0,
  "biasLabel": "중립에 가까움",
  "biasSummary": "왜 그렇게 추정했는지 1~2문장",

  "aiRisk": "low",
  "aiSummary": "AI 생성 가능성에 대한 설명 1문장",
  "issue": "핵심 이슈",

  "similarResources": [
    {{
      "type": "youtube",
      "title": "비슷한 관점으로 비교해볼 영상 검색",
      "source": "YouTube",
      "url": "https://www.youtube.com/results?search_query=검색어",
      "summary": ""
    }},
    {{
      "type": "article",
      "title": "비슷한 관점의 기사/웹 자료 검색",
      "source": "Google Search",
      "url": "https://www.google.com/search?q=검색어",
      "summary": "짧은 설명"
    }}
  ],
  "oppositeResources": [
    {{
      "type": "youtube",
      "title": "다른 관점에서 비교해볼 영상 검색",
      "source": "YouTube",
      "url": "https://www.youtube.com/results?search_query=검색어",
      "summary": ""
    }},
    {{
      "type": "article",
      "title": "다른 관점의 기사/웹 자료 검색",
      "source": "Google Search",
      "url": "https://www.google.com/search?q=검색어",
      "summary": "짧은 설명"
    }}
  ],
  "verificationResources": [
    {{
      "type": "article",
      "title": "팩트체크 또는 공식 자료 검색",
      "source": "Google Search",
      "url": "https://www.google.com/search?q=검색어",
      "summary": "짧은 설명"
    }},
    {{
      "type": "ai_answer",
      "title": "자료가 부족할 때 확인할 질문",
      "source": "CrossView AI",
      "url": "",
      "summary": "사용자가 직접 확인할 질문"
    }}
  ],
  "checklist": [
    "질문 1",
    "질문 2",
    "질문 3",
    "질문 4"
  ]
}}
""".strip()

    def _parse_json(self, text: str) -> dict:
        cleaned = text.strip()
        cleaned = re.sub(r"^```json\\s*", "", cleaned)
        cleaned = re.sub(r"^```\\s*", "", cleaned)
        cleaned = re.sub(r"\\s*```$", "", cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\\{.*\\}", cleaned, re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _normalize_gemini_response(self, data: dict, video: VideoContext) -> AnalysisResponse:
        title = video.title or "뉴스 이슈"
        source_used = data.get("sourceUsed") or self._source_used(video)
        source_label = data.get("sourceLabel") or self._source_label(source_used, video.commentsCount)

        is_political = bool(data.get("isPolitical", False))
        bias_score = data.get("biasScore", 0)
        try:
            bias_score = int(bias_score)
        except Exception:
            bias_score = 0
        bias_score = max(-5, min(5, bias_score))

        if not is_political:
            bias_score = 0

        def normalize_list(value, fallback):
            if isinstance(value, list):
                cleaned = [str(item) for item in value if str(item).strip()]
                return cleaned or fallback
            return fallback

        def normalize_resources(items, default_kind):
            if not isinstance(items, list) or not items:
                return self._default_resources(title, default_kind)

            normalized = []
            for item in items[:3]:
                if not isinstance(item, dict):
                    continue

                resource_type = item.get("type") or "article"
                if resource_type not in ["youtube", "article", "ai_answer"]:
                    resource_type = "article"

                url = item.get("url") or ""
                if resource_type != "ai_answer" and not url:
                    url = self._default_url(title, default_kind, resource_type)

                normalized.append(
                    Resource(
                        type=resource_type,
                        title=item.get("title") or "비교해볼 자료",
                        source=item.get("source") or "CrossView 추천",
                        url=url,
                        summary=item.get("summary") or "",
                    )
                )

            return normalized or self._default_resources(title, default_kind)

        return AnalysisResponse(
            summary=data.get("summary") or "영상 내용을 요약할 정보가 충분하지 않습니다.",
            mainClaims=normalize_list(data.get("mainClaims"), ["핵심 주장을 추출할 정보가 충분하지 않습니다."]),
            evidenceSummary=data.get("evidenceSummary") or "근거 정보가 충분하지 않습니다.",
            cautionPoints=normalize_list(data.get("cautionPoints"), ["추가 출처와 반대 관점을 함께 확인해보세요."]),

            sourceUsed=source_used,
            sourceLabel=source_label,
            commentsIncluded=bool(data.get("commentsIncluded", bool(video.commentsText))),
            commentsCount=int(data.get("commentsCount", video.commentsCount or 0)),

            commentMood=data.get("commentMood") or "댓글 분석 정보 부족",
            commentIntensity=data.get("commentIntensity") or "정보 부족",
            commentLeaning=data.get("commentLeaning") or "정보 부족",
            commentWarningSignals=normalize_list(data.get("commentWarningSignals"), ["댓글 정보가 부족하거나 아직 수집되지 않았습니다."]),

            isPolitical=is_political,
            biasScore=bias_score,
            biasLabel=data.get("biasLabel") or "중립에 가까움",
            biasSummary=data.get("biasSummary") or (
                "정치·시사 영상으로 강하게 판단되지 않아 정치 성향도 바를 기본 표시하지 않습니다."
                if not is_political
                else "스크립트/설명/댓글 기반으로 편향도를 추정했습니다."
            ),

            aiRisk=data.get("aiRisk") if data.get("aiRisk") in ["low", "medium", "high"] else "low",
            aiSummary=data.get("aiSummary") or "현재 기준 AI 생성 가능성을 추가 확인해야 합니다.",
            issue=data.get("issue") or "현재 영상의 핵심 이슈",

            similarResources=normalize_resources(data.get("similarResources"), "similar"),
            oppositeResources=normalize_resources(data.get("oppositeResources"), "opposite"),
            verificationResources=normalize_resources(data.get("verificationResources"), "verify"),
            checklist=normalize_list(data.get("checklist"), [
                "스크립트에서 핵심 주장의 근거가 직접 제시되었는가?",
                "다른 출처도 같은 내용을 말하는가?",
                "반대 관점에서는 이 이슈를 어떻게 설명하는가?",
                "AI 음성·합성 콘텐츠 가능성을 확인했는가?",
            ]),
        )

    def _default_url(self, title: str, kind: str, resource_type: str) -> str:
        base_query = quote_plus(title or "뉴스 이슈")
        suffix = {
            "similar": "관련 분석",
            "opposite": "다른 관점",
            "verify": "팩트체크 공식자료",
        }.get(kind, "관련 자료")

        if resource_type == "youtube":
            return f"https://www.youtube.com/results?search_query={base_query}+{quote_plus(suffix)}"

        return f"https://www.google.com/search?q={base_query}+{quote_plus(suffix)}"

    def _default_resources(self, title: str, kind: str):
        if kind == "similar":
            return [
                Resource(
                    type="youtube",
                    title="비슷한 관점으로 이슈를 다룬 영상 검색",
                    source="YouTube",
                    url=self._default_url(title, "similar", "youtube"),
                ),
                Resource(
                    type="article",
                    title="비슷한 관점의 기사/웹 자료 검색",
                    source="Google Search",
                    url=self._default_url(title, "similar", "article"),
                ),
            ]

        if kind == "opposite":
            return [
                Resource(
                    type="youtube",
                    title="다른 관점에서 비교해볼 영상 검색",
                    source="YouTube",
                    url=self._default_url(title, "opposite", "youtube"),
                ),
                Resource(
                    type="article",
                    title="다른 관점의 기사/웹 자료 검색",
                    source="Google Search",
                    url=self._default_url(title, "opposite", "article"),
                ),
            ]

        return [
            Resource(
                type="article",
                title="팩트체크 또는 공식 자료 검색",
                source="Google Search",
                url=self._default_url(title, "verify", "article"),
            ),
            Resource(
                type="ai_answer",
                title="자료가 부족할 때 확인할 질문",
                source="CrossView AI",
                summary="출처, 원문 자료, 통계, 반대 관점이 있는지 확인해보세요.",
            ),
        ]

    def _mock_analyze(self, video: VideoContext) -> AnalysisResponse:
        seed = sum(ord(ch) for ch in video.title or "CrossView")
        is_political = self._is_political(video)
        bias_score = (seed % 11) - 5 if is_political else 0

        if bias_score < 0:
            bias_label = f"좌측 성향 {abs(bias_score)}"
        elif bias_score > 0:
            bias_label = f"우측 성향 {bias_score}"
        else:
            bias_label = "중립에 가까움"

        ai_risk = ["low", "medium", "high"][seed % 3]
        ai_summary_map = {
            "low": "현재 기준 뚜렷한 AI 생성 징후는 낮습니다.",
            "medium": "일부 자동 생성 콘텐츠 패턴이 의심됩니다. 추가 확인이 필요합니다.",
            "high": "AI 음성 또는 합성 영상일 가능성을 주의해서 확인해야 합니다.",
        }

        source_used = self._source_used(video)
        source_label = self._source_label(source_used, video.commentsCount)
        comments_included = bool(video.commentsText)

        if is_political:
            bias_summary = (
                "현재는 mock 분석입니다. 실제 연결 후 스크립트, 설명, 댓글을 기반으로 "
                "좌우 편향도와 근거를 추정합니다."
            )
        else:
            bias_summary = (
                "정치·시사 영상으로 강하게 판단되지 않아 정치 성향도 바를 기본 표시하지 않습니다."
            )

        title = video.title or "현재 영상"

        return AnalysisResponse(
            summary=(
                f"이 영상은 '{title}'을 중심으로 특정 이슈를 설명하거나 해석하는 콘텐츠입니다. "
                "현재 mock 분석에서는 제목, 설명, 화면에서 감지된 스크립트/댓글 정보를 기준으로 요약합니다."
            ),
            mainClaims=[
                "영상의 핵심 주장과 메시지를 파악해야 합니다.",
                "제시된 근거가 충분한지 확인해야 합니다.",
                "반대 관점이나 추가 출처가 함께 제시되는지 확인해야 합니다.",
            ],
            evidenceSummary="현재 mock 분석에서는 실제 근거 문장 추출 대신, 추후 Gemini 분석으로 근거 요약을 대체합니다.",
            cautionPoints=[
                "감정적 표현이 판단에 영향을 줄 수 있습니다.",
                "출처가 불명확한 주장은 추가 확인이 필요합니다.",
                "댓글 분위기만으로 사실 여부를 판단하면 안 됩니다.",
            ],

            sourceUsed=source_used,
            sourceLabel=source_label,
            commentsIncluded=comments_included,
            commentsCount=video.commentsCount,

            commentMood="댓글이 수집된 경우 전체 분위기를 추정합니다." if comments_included else "댓글 정보 부족",
            commentIntensity="보통" if comments_included else "정보 부족",
            commentLeaning="댓글 일부만으로는 단정하기 어렵습니다." if comments_included else "정보 부족",
            commentWarningSignals=[
                "비난성 표현 또는 단정적 표현 여부 확인 필요",
                "동조 댓글이 과도하게 반복되는지 확인 필요",
            ] if comments_included else ["댓글이 아직 충분히 수집되지 않았습니다."],

            isPolitical=is_political,
            biasScore=bias_score,
            biasLabel=bias_label,
            biasSummary=bias_summary,
            aiRisk=ai_risk,
            aiSummary=ai_summary_map[ai_risk],
            issue="현재 영상의 핵심 이슈",

            similarResources=self._default_resources(title, "similar"),
            oppositeResources=self._default_resources(title, "opposite"),
            verificationResources=self._default_resources(title, "verify"),
            checklist=[
                "스크립트에서 핵심 주장의 근거가 직접 제시되었는가?",
                "다른 출처도 같은 내용을 말하는가?",
                "반대 관점에서는 이 이슈를 어떻게 설명하는가?",
                "댓글 분위기가 판단에 영향을 주고 있지 않은가?",
                "AI 음성·합성 콘텐츠 가능성을 확인했는가?",
            ],
        )
