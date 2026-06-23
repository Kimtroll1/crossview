from __future__ import annotations

import asyncio
from collections import defaultdict
from urllib.parse import quote_plus
from typing import Any

from app.config import settings
from app.schemas.analysis import AnalysisResponse, Resource, VideoContext


class SearchService:
    """Build resource cards for the analysis UI.

    The stable path uses deterministic search links for web resources so we do
    not depend on Gemini Search grounding for every analysis.
    """

    async def enrich(self, video: VideoContext, analysis: AnalysisResponse) -> AnalysisResponse:
        tasks: dict[str, asyncio.Task[dict[str, list[Resource]]]] = {}

        tasks["web"] = asyncio.create_task(asyncio.to_thread(self._web_bundle, analysis))
        if settings.youtube_api_key:
            tasks["youtube"] = asyncio.create_task(asyncio.to_thread(self._youtube_bundle, analysis))

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        combined: dict[str, list[Resource]] = defaultdict(list)

        for name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                print(f"[CrossView] {name} search failed: {result}")
                continue
            for category, resources in result.items():
                combined[category].extend(resources)

        analysis.similarResources = self._select(combined.get("similar", []), 3)
        analysis.oppositeResources = self._select(combined.get("opposite", []), 4)
        analysis.neutralResources = self._select(combined.get("neutral", []), 4)
        analysis.verificationResources = self._select(combined.get("verification", []), 4)
        analysis.resourcesCached = True
        return analysis

    def _web_bundle(self, analysis: AnalysisResponse) -> dict[str, list[Resource]]:
        queries = self._query_map(analysis)
        output: dict[str, list[Resource]] = defaultdict(list)

        output["similar"].extend(
            [
                self._web_resource(
                    category="similar",
                    resource_type="youtube",
                    title="YouTube search for supporting context",
                    source="YouTube Search",
                    query=queries["supporting"],
                    summary="Open YouTube results related to the supporting view.",
                    stance_score=self._stance_for("similar", analysis.biasScore),
                ),
                self._web_resource(
                    category="similar",
                    resource_type="article",
                    title="Google search for supporting context",
                    source="Google Search",
                    query=queries["supporting"],
                    summary="Open web results related to the supporting view.",
                    stance_score=self._stance_for("similar", analysis.biasScore),
                ),
            ]
        )

        output["opposite"].extend(
            [
                self._web_resource(
                    category="opposite",
                    resource_type="youtube",
                    title="YouTube search for opposing context",
                    source="YouTube Search",
                    query=queries["opposing"],
                    summary="Open YouTube results that may challenge the main claim.",
                    stance_score=self._stance_for("opposite", analysis.biasScore),
                ),
                self._web_resource(
                    category="opposite",
                    resource_type="article",
                    title="Google search for opposing context",
                    source="Google Search",
                    query=queries["opposing"],
                    summary="Open web results that may challenge the main claim.",
                    stance_score=self._stance_for("opposite", analysis.biasScore),
                ),
            ]
        )

        output["neutral"].extend(
            [
                self._web_resource(
                    category="neutral",
                    resource_type="article",
                    title="Neutral web search",
                    source="Google Search",
                    query=queries["neutral"],
                    summary="Open neutral background information for the topic.",
                    stance_score=0,
                ),
                self._web_resource(
                    category="neutral",
                    resource_type="youtube",
                    title="Neutral YouTube search",
                    source="YouTube Search",
                    query=queries["neutral"],
                    summary="Open neutral YouTube results for additional context.",
                    stance_score=0,
                ),
            ]
        )

        output["verification"].extend(
            [
                self._web_resource(
                    category="verification",
                    resource_type="article",
                    title="Fact-check search",
                    source="Google Search",
                    query=queries["factCheck"],
                    summary="Search for fact-check coverage and independent verification.",
                    stance_score=0,
                ),
                self._web_resource(
                    category="verification",
                    resource_type="article",
                    title="Official sources search",
                    source="Google Search",
                    query=queries["official"],
                    summary="Search for official or primary-source references.",
                    stance_score=0,
                ),
            ]
        )

        return output

    def _youtube_bundle(self, analysis: AnalysisResponse) -> dict[str, list[Resource]]:
        from googleapiclient.discovery import build

        youtube = build("youtube", "v3", developerKey=settings.youtube_api_key, cache_discovery=False)
        queries = self._query_map(analysis)
        output: dict[str, list[Resource]] = defaultdict(list)

        for category, query in {
            "similar": queries["supporting"],
            "opposite": queries["opposing"],
            "neutral": queries["neutral"],
        }.items():
            if not query:
                continue

            response = youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=4,
                order="relevance",
                relevanceLanguage="ko",
                regionCode="KR",
                safeSearch="moderate",
            ).execute()

            for index, item in enumerate(response.get("items", [])):
                video_id = item.get("id", {}).get("videoId")
                if not video_id:
                    continue

                snippet = item.get("snippet", {})
                title = snippet.get("title") or "YouTube video"
                channel = snippet.get("channelTitle") or "YouTube"
                thumb = (
                    snippet.get("thumbnails", {}).get("medium")
                    or snippet.get("thumbnails", {}).get("default")
                    or {}
                ).get("url", "")

                output[category].append(
                    Resource(
                        type="youtube",
                        category=category,
                        title=title,
                        source=channel,
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        summary=(snippet.get("description") or "")[:220],
                        icon="YT",
                        publishedAt=snippet.get("publishedAt") or "",
                        thumbnailUrl=thumb,
                        stanceScore=self._stance_for(category, analysis.biasScore),
                        stanceLabel=self._stance_label(category, self._stance_for(category, analysis.biasScore)),
                        relevanceScore=max(60.0, 96.0 - index * 6),
                        credibilityScore=58.0,
                        recommendationReason=self._reason(category),
                        keyPoint=(snippet.get("description") or "")[:150],
                        verifiedUrl=True,
                    )
                )

        return output

    def _query_map(self, analysis: AnalysisResponse) -> dict[str, str]:
        issue = (analysis.issue or analysis.summary or "CrossView topic").strip()
        queries = analysis.searchQueries

        return {
            "neutral": queries.neutral or f"{issue} overview",
            "supporting": queries.supporting or f"{issue} supporting evidence",
            "opposing": queries.opposing or f"{issue} opposing view",
            "factCheck": queries.factCheck or f"{issue} fact check",
            "official": queries.official or f"{issue} official source",
        }

    def _web_resource(
        self,
        *,
        category: str,
        resource_type: str,
        title: str,
        source: str,
        query: str,
        summary: str,
        stance_score: int,
    ) -> Resource:
        url = self._search_url(query, resource_type)
        return Resource(
            type=resource_type,
            category=category,
            title=title,
            source=source,
            url=url,
            summary=summary,
            icon="YT" if resource_type == "youtube" else "WEB",
            stanceScore=stance_score,
            stanceLabel=self._stance_label(category, stance_score),
            relevanceScore=88.0 if category in {"similar", "opposite"} else 80.0,
            credibilityScore=65.0 if resource_type == "youtube" else 72.0,
            recommendationReason=self._reason(category),
            keyPoint=query[:150],
            verifiedUrl=True,
        )

    def _search_url(self, query: str, resource_type: str) -> str:
        encoded = quote_plus((query or "").strip() or "CrossView")
        if resource_type == "youtube":
            return f"https://www.youtube.com/results?search_query={encoded}"
        return f"https://www.google.com/search?q={encoded}"

    def _select(self, resources: list[Resource], limit: int) -> list[Resource]:
        result: list[Resource] = []
        seen_urls: set[str] = set()

        for item in sorted(resources, key=lambda x: (x.relevanceScore + x.credibilityScore), reverse=True):
            if not item.url or item.url in seen_urls:
                continue
            seen_urls.add(item.url)
            result.append(item)
            if len(result) >= limit:
                break

        return result

    def _stance_for(self, category: str, bias_score: int) -> int:
        if category == "similar":
            return max(-5, min(5, bias_score or 1))
        if category == "opposite":
            return max(-5, min(5, -(bias_score or 1)))
        return 0

    def _stance_label(self, category: str, score: int) -> str:
        if category == "neutral":
            return "neutral"
        if score <= -4:
            return "strong negative"
        if score <= -2:
            return "negative"
        if score >= 4:
            return "strong positive"
        if score >= 2:
            return "positive"
        return "balanced"

    def _reason(self, category: str) -> str:
        reasons = {
            "similar": "Helpful starting point for supporting evidence.",
            "opposite": "Useful for checking counterarguments and blind spots.",
            "neutral": "Background context without strong stance.",
            "verification": "Best used to verify claims with primary or official sources.",
        }
        return reasons.get(category, "Related resource.")
