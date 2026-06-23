from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.recommendation import Recommendation
from app.models.resource_click import ResourceClick
from app.models.user import User
from app.models.watch_history import WatchHistory
from app.schemas.analysis import Resource
from app.schemas.report import ReportResponse, SignalAverages


class ReportService:
    def build_report(self, db: Session, user: User, period: str = "weekly") -> ReportResponse:
        now = datetime.now(timezone.utc)
        days = 30 if period == "monthly" else 7
        start = now - timedelta(days=days)
        rows = (
            db.query(WatchHistory, Analysis)
            .join(Analysis, WatchHistory.analysis_id == Analysis.id)
            .filter(WatchHistory.user_id == user.id, WatchHistory.watched_at >= start)
            .order_by(WatchHistory.watched_at.desc())
            .all()
        )
        unique_rows: list[tuple[WatchHistory, Analysis]] = []
        seen_video_ids: set[int] = set()
        for watch, analysis in rows:
            if watch.video_id in seen_video_ids:
                continue
            seen_video_ids.add(watch.video_id)
            unique_rows.append((watch, analysis))
        if not unique_rows:
            return self._empty(user.external_id, period, start, now)

        analyses = [analysis for _, analysis in unique_rows]
        political = [analysis for analysis in analyses if analysis.is_political]
        total = len(analyses)
        political_total = len(political)
        left = sum(1 for item in political if (item.bias_score or 0) < -1)
        right = sum(1 for item in political if (item.bias_score or 0) > 1)
        neutral = political_total - left - right
        average_bias = sum(item.bias_score or 0 for item in political) / political_total if political_total else 0
        average_confidence = sum(float(item.bias_confidence or 0) for item in political) / political_total if political_total else 0
        ai_risk_count = sum(1 for item in analyses if item.ai_risk in {"medium", "high"})
        topic_counts = Counter((item.issue or "기타").strip() for item in analyses if (item.issue or "").strip())
        top_topics = [topic for topic, _ in topic_counts.most_common(5)]
        signals = self._average_signals(analyses)

        clicks = (
            db.query(ResourceClick)
            .filter(ResourceClick.user_id == user.id, ResourceClick.clicked_at >= start)
            .all()
        )
        alternative_clicks = sum(1 for click in clicks if click.category in {"opposite", "neutral", "verification"})
        exploration_rate = min(100.0, alternative_clicks / max(total, 1) * 100)
        recommended = self._recommended_resources(db, [analysis.id for analysis in analyses], political, limit=5)

        denominator = political_total or 1
        suggestion = self._suggestion(average_bias, political_total, signals, exploration_rate)
        return ReportResponse(
            userId=user.external_id,
            period=period,
            periodStart=start.isoformat(),
            periodEnd=now.isoformat(),
            totalVideos=total,
            politicalVideos=political_total,
            averageBiasScore=round(average_bias, 2),
            averageBiasConfidence=round(average_confidence, 2),
            leftRatio=round(left / denominator * 100, 1) if political_total else 0,
            neutralRatio=round(neutral / denominator * 100, 1) if political_total else 0,
            rightRatio=round(right / denominator * 100, 1) if political_total else 0,
            aiRiskCount=ai_risk_count,
            aiRiskRatio=round(ai_risk_count / total * 100, 1),
            topTopics=top_topics,
            suggestion=suggestion,
            biasDistribution={"left": left, "neutral": neutral, "right": right},
            signalAverages=signals,
            resourceClicks=len(clicks),
            alternativeResourceClicks=alternative_clicks,
            alternativeExplorationRate=round(exploration_rate, 1),
            recommendedResources=recommended,
        )

    def build_for_external_id(self, db: Session, user_id: str, period: str = "weekly") -> ReportResponse:
        user = db.query(User).filter(User.external_id == user_id).first()
        if not user:
            now = datetime.now(timezone.utc)
            return self._empty(user_id, period, now - timedelta(days=30 if period == "monthly" else 7), now)
        return self.build_report(db, user, period)

    def _average_signals(self, analyses: list[Analysis]) -> SignalAverages:
        if not analyses:
            return SignalAverages()
        sums = {
            "emotionalManipulation": 0.0,
            "evidenceSelection": 0.0,
            "viewpointOmission": 0.0,
            "sourceConcentration": 0.0,
            "opinionConcentration": 0.0,
            "commentEmotionIntensity": 0.0,
        }
        for analysis in analyses:
            bias = analysis.bias_signals or {}
            flow = analysis.comment_flow or {}
            for key in ("emotionalManipulation", "evidenceSelection", "viewpointOmission", "sourceConcentration"):
                item = bias.get(key) if isinstance(bias.get(key), dict) else {}
                sums[key] += float(item.get("score") or 0)
            sums["opinionConcentration"] += float(flow.get("opinionConcentration") or 0)
            sums["commentEmotionIntensity"] += float(flow.get("emotionIntensity") or 0)
        count = len(analyses)
        return SignalAverages(**{key: round(value / count, 2) for key, value in sums.items()})

    def _recommended_resources(self, db: Session, analysis_ids: list[int], political: list[Analysis], limit: int) -> list[Resource]:
        if not analysis_ids:
            return []
        preferred = "opposite"
        average_bias = sum(item.bias_score or 0 for item in political) / len(political) if political else 0
        rows = (
            db.query(Recommendation)
            .filter(Recommendation.analysis_id.in_(analysis_ids), Recommendation.category.in_([preferred, "neutral", "verification"]))
            .order_by(Recommendation.relevance_score.desc(), Recommendation.credibility_score.desc())
            .all()
        )
        output: list[Resource] = []
        seen_urls: set[str] = set()
        for item in rows:
            if not item.url or item.url in seen_urls:
                continue
            if average_bias > 1 and item.stance_score > 1:
                continue
            if average_bias < -1 and item.stance_score < -1:
                continue
            seen_urls.add(item.url)
            output.append(Resource(
                id=item.id,
                type=item.resource_type,
                category=item.category,
                title=item.title,
                source=item.source or "",
                url=item.url or "",
                summary=item.summary or "",
                publishedAt=item.published_at or "",
                thumbnailUrl=item.thumbnail_url or "",
                stanceScore=item.stance_score or 0,
                stanceLabel=item.stance_label or "관점 미분류",
                relevanceScore=float(item.relevance_score or 0),
                credibilityScore=float(item.credibility_score or 0),
                recommendationReason=item.recommendation_reason or "",
                keyPoint=item.key_point or "",
                verifiedUrl=bool(item.verified_url),
            ))
            if len(output) >= limit:
                break
        return output

    @staticmethod
    def _suggestion(average_bias: float, political_total: int, signals: SignalAverages, exploration_rate: float) -> str:
        parts: list[str] = []
        if not political_total:
            parts.append("정치·시사 영상 기록이 적어 정치 방향보다는 근거와 출처를 중심으로 확인할 수 있습니다.")
        elif average_bias > 1:
            parts.append("최근 보수 성향으로 추정된 영상 비중이 높았습니다.")
        elif average_bias < -1:
            parts.append("최근 진보 성향으로 추정된 영상 비중이 높았습니다.")
        else:
            parts.append("최근 정치·시사 시청 방향은 비교적 중립에 가까웠습니다.")
        if signals.viewpointOmission >= 3.5:
            parts.append("반대 관점이 누락된 영상 노출이 높아, 같은 이슈의 중립 해설과 반론 자료를 함께 확인해보세요.")
        elif signals.emotionalManipulation >= 3.5:
            parts.append("감정 자극 신호가 높은 영상에서는 주장보다 원문과 수치를 먼저 확인해보세요.")
        elif exploration_rate < 20:
            parts.append("CrossView가 제안한 다른 관점 자료를 한두 개 열어 비교하면 리포트의 균형 탐색률이 올라갑니다.")
        else:
            parts.append("다른 관점 자료를 꾸준히 확인하고 있습니다. 점수보다 각 자료의 근거 차이를 비교해보세요.")
        return " ".join(parts)

    @staticmethod
    def _empty(user_id: str, period: str, start: datetime, end: datetime) -> ReportResponse:
        return ReportResponse(
            userId=user_id,
            period=period,
            periodStart=start.isoformat(),
            periodEnd=end.isoformat(),
            suggestion="아직 해당 기간의 분석 기록이 없습니다. 유튜브에서 CrossView 분석을 실행해보세요.",
            biasDistribution={"left": 0, "neutral": 0, "right": 0},
        )
