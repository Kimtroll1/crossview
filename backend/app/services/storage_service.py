from __future__ import annotations

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.recommendation import Recommendation
from app.models.user import User
from app.models.video import Video
from app.models.watch_history import WatchHistory
from app.schemas.analysis import AnalysisResponse, Resource, VideoContext


class StorageService:
    def get_or_create_demo_user(self, db: Session, external_id: str = "demo-user") -> User:
        user = db.query(User).filter(User.external_id == external_id).first()
        if user:
            return user
        user = User(external_id=external_id, name="Demo User", auth_provider="demo")
        db.add(user)
        db.flush()
        return user

    def get_cached_analysis(self, db: Session, youtube_video_id: str) -> AnalysisResponse | None:
        row = (
            db.query(Analysis)
            .join(Video, Analysis.video_id == Video.id)
            .filter(Video.youtube_video_id == youtube_video_id)
            .order_by(Analysis.updated_at.desc(), Analysis.created_at.desc())
            .first()
        )
        if not row:
            return None
        return self._to_response(db, row, cached=True)


    def resources_stale(self, db: Session, youtube_video_id: str, max_age_hours: int = 24) -> bool:
        analysis = (
            db.query(Analysis)
            .join(Video, Analysis.video_id == Video.id)
            .filter(Video.youtube_video_id == youtube_video_id)
            .order_by(Analysis.updated_at.desc())
            .first()
        )
        if not analysis or not analysis.resources_updated_at:
            return True
        updated = analysis.resources_updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - updated > timedelta(hours=max_age_hours)

    def record_cached_view(self, db: Session, context: VideoContext, analysis_response: AnalysisResponse, user: User | None = None) -> None:
        video = db.query(Video).filter(Video.youtube_video_id == context.videoId).first()
        if not video:
            return
        analysis = db.query(Analysis).filter(Analysis.video_id == video.id).order_by(Analysis.updated_at.desc()).first()
        if not analysis:
            return
        user = user or self.get_or_create_demo_user(db, context.userId or "demo-user")
        self._upsert_watch_history(db, user.id, video.id, analysis.id)
        db.commit()

    def save_analysis(self, db: Session, context: VideoContext, result: AnalysisResponse, user: User | None = None) -> AnalysisResponse:
        user = user or self.get_or_create_demo_user(db, context.userId or "demo-user")
        video = db.query(Video).filter(Video.youtube_video_id == context.videoId).first()
        if not video:
            video = Video(
                youtube_video_id=context.videoId or context.url or f"manual-{int(datetime.now().timestamp())}",
                title=context.title or "제목 없음",
                channel_name=context.channelName,
                url=context.url,
                description=context.description,
            )
            db.add(video)
            db.flush()
        else:
            video.title = context.title or video.title
            video.channel_name = context.channelName or video.channel_name
            video.url = context.url or video.url
            video.description = context.description or video.description

        analysis = db.query(Analysis).filter(Analysis.video_id == video.id).order_by(Analysis.updated_at.desc()).first()
        if not analysis:
            analysis = Analysis(video_id=video.id, summary=result.summary)
            db.add(analysis)
            db.flush()

        analysis.summary = result.summary
        analysis.main_claims = result.mainClaims
        analysis.evidence_summary = result.evidenceSummary
        analysis.caution_points = result.cautionPoints
        analysis.is_political = result.isPolitical
        analysis.bias_score = result.biasScore
        analysis.bias_label = result.biasLabel
        analysis.bias_summary = result.biasSummary
        analysis.bias_criteria = result.biasCriteria
        analysis.bias_confidence = result.biasConfidence
        analysis.bias_signals = result.biasSignals.model_dump()
        analysis.ai_risk = result.aiRisk
        analysis.ai_summary = result.aiSummary
        analysis.comment_flow = result.commentFlow.model_dump()
        analysis.comment_mood = result.commentMood
        analysis.comment_intensity = result.commentIntensity
        analysis.comment_leaning = result.commentLeaning
        analysis.comment_warning_signals = result.commentWarningSignals
        analysis.source_used = result.sourceUsed
        analysis.source_label = result.sourceLabel
        analysis.comments_count = result.commentsCount
        analysis.issue = result.issue
        analysis.search_queries = result.searchQueries.model_dump()
        analysis.provider = result.analysisProvider
        analysis.model_name = result.analysisModel
        analysis.prompt_version = result.promptVersion
        analysis.raw_result = result.model_dump(exclude={"similarResources", "oppositeResources", "neutralResources", "verificationResources"})
        analysis.updated_at = datetime.now(timezone.utc)
        db.flush()

        self._replace_recommendations(db, analysis.id, result)
        self._upsert_watch_history(db, user.id, video.id, analysis.id)
        db.commit()
        db.refresh(analysis)
        return self._to_response(db, analysis, cached=False)

    def replace_resources(self, db: Session, youtube_video_id: str, result: AnalysisResponse) -> AnalysisResponse:
        analysis = (
            db.query(Analysis)
            .join(Video, Analysis.video_id == Video.id)
            .filter(Video.youtube_video_id == youtube_video_id)
            .order_by(Analysis.updated_at.desc())
            .first()
        )
        if not analysis:
            return result
        self._replace_recommendations(db, analysis.id, result)
        db.commit()
        return self._to_response(db, analysis, cached=True)

    def _replace_recommendations(self, db: Session, analysis_id: int, result: AnalysisResponse) -> None:
        db.query(Recommendation).filter(Recommendation.analysis_id == analysis_id).delete(synchronize_session=False)
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis is not None:
            analysis.resources_updated_at = datetime.now(timezone.utc)
        categories = (
            ("similar", result.similarResources),
            ("opposite", result.oppositeResources),
            ("neutral", result.neutralResources),
            ("verification", result.verificationResources),
        )
        for category, resources in categories:
            for resource in resources:
                db.add(Recommendation(
                    analysis_id=analysis_id,
                    category=category,
                    resource_type=resource.type,
                    title=resource.title,
                    url=resource.url,
                    source=resource.source,
                    summary=resource.summary,
                    published_at=resource.publishedAt,
                    thumbnail_url=resource.thumbnailUrl,
                    stance_score=resource.stanceScore,
                    stance_label=resource.stanceLabel,
                    relevance_score=resource.relevanceScore,
                    credibility_score=resource.credibilityScore,
                    recommendation_reason=resource.recommendationReason,
                    key_point=resource.keyPoint,
                    domain=self._domain(resource.url),
                    verified_url=resource.verifiedUrl,
                ))

    def _to_response(self, db: Session, analysis: Analysis, cached: bool) -> AnalysisResponse:
        raw = dict(analysis.raw_result or {})
        raw.update({
            "summary": analysis.summary,
            "mainClaims": analysis.main_claims or [],
            "evidenceSummary": analysis.evidence_summary or "",
            "cautionPoints": analysis.caution_points or [],
            "sourceUsed": analysis.source_used or "metadata",
            "sourceLabel": analysis.source_label or "제목·채널 메타데이터",
            "commentsIncluded": bool(analysis.comments_count),
            "commentsCount": analysis.comments_count or 0,
            "commentMood": analysis.comment_mood or "댓글 분석 정보 없음",
            "commentIntensity": analysis.comment_intensity or "정보 부족",
            "commentLeaning": analysis.comment_leaning or "정보 부족",
            "commentWarningSignals": analysis.comment_warning_signals or [],
            "commentFlow": analysis.comment_flow or {},
            "isPolitical": bool(analysis.is_political),
            "biasScore": analysis.bias_score or 0,
            "biasLabel": analysis.bias_label or "중립에 가까움",
            "biasSummary": analysis.bias_summary or "",
            "biasCriteria": analysis.bias_criteria or [],
            "biasConfidence": float(analysis.bias_confidence or 0),
            "biasSignals": analysis.bias_signals or {},
            "aiRisk": analysis.ai_risk or "low",
            "aiSummary": analysis.ai_summary or "",
            "issue": analysis.issue or "핵심 이슈",
            "searchQueries": analysis.search_queries or {},
            "cached": cached,
            "resourcesCached": True,
            "analysisProvider": analysis.provider or "mock",
            "analysisModel": analysis.model_name or "mock",
            "promptVersion": analysis.prompt_version or "crossview-bias-v2",
        })
        resources = db.query(Recommendation).filter(Recommendation.analysis_id == analysis.id).order_by(Recommendation.id.asc()).all()
        grouped: dict[str, list[Resource]] = {"similar": [], "opposite": [], "neutral": [], "verification": []}
        for item in resources:
            grouped.setdefault(item.category, []).append(self._resource(item))
        raw["similarResources"] = grouped.get("similar", [])
        raw["oppositeResources"] = grouped.get("opposite", [])
        raw["neutralResources"] = grouped.get("neutral", [])
        raw["verificationResources"] = grouped.get("verification", [])
        return AnalysisResponse.model_validate(raw)

    @staticmethod
    def _resource(item: Recommendation) -> Resource:
        return Resource(
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
        )

    @staticmethod
    def _upsert_watch_history(db: Session, user_id: int, video_id: int, analysis_id: int) -> None:
        history = db.query(WatchHistory).filter(WatchHistory.user_id == user_id, WatchHistory.video_id == video_id).first()
        if history:
            history.analysis_id = analysis_id
            history.watched_at = datetime.now(timezone.utc)
        else:
            db.add(WatchHistory(user_id=user_id, video_id=video_id, analysis_id=analysis_id))

    @staticmethod
    def _domain(url: str) -> str:
        from urllib.parse import urlparse
        try:
            return urlparse(url).netloc.lower().removeprefix("www.")
        except Exception:
            return ""
