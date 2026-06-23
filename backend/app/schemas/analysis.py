from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class VideoContext(BaseModel):
    userId: str = "demo-user"
    videoId: str = ""
    url: str = ""
    title: str = ""
    channelName: str = ""
    description: str = ""
    transcript: str = ""
    commentsText: str = ""
    commentsCount: int = 0
    analysisSource: str = "metadata"
    collectedAt: Optional[str] = None
    forceRefresh: bool = False
    refreshResources: bool = False


class SignalDetail(BaseModel):
    score: int = Field(default=0, ge=0, le=5)
    label: str = "낮음"
    reasons: List[str] = Field(default_factory=list)


class BiasSignals(BaseModel):
    emotionalManipulation: SignalDetail = Field(default_factory=SignalDetail)
    evidenceSelection: SignalDetail = Field(default_factory=SignalDetail)
    viewpointOmission: SignalDetail = Field(default_factory=SignalDetail)
    sourceConcentration: SignalDetail = Field(default_factory=SignalDetail)


class CommentFlow(BaseModel):
    opinionConcentration: int = Field(default=0, ge=0, le=5)
    emotionIntensity: int = Field(default=0, ge=0, le=5)
    summary: str = "댓글 정보가 충분하지 않습니다."
    sampleSize: int = 0


class SearchQueries(BaseModel):
    neutral: str = ""
    supporting: str = ""
    opposing: str = ""
    factCheck: str = ""
    official: str = ""
    youtubeAlternative: str = ""


class Resource(BaseModel):
    id: int | None = None
    type: str = "article"
    category: str = "neutral"
    title: str
    source: str = "CrossView 추천"
    url: str = ""
    summary: str = ""
    icon: str = ""
    publishedAt: str = ""
    thumbnailUrl: str = ""
    stanceScore: int = Field(default=0, ge=-5, le=5)
    stanceLabel: str = "관점 미분류"
    relevanceScore: float = Field(default=0.0, ge=0.0, le=100.0)
    credibilityScore: float = Field(default=0.0, ge=0.0, le=100.0)
    recommendationReason: str = ""
    keyPoint: str = ""
    verifiedUrl: bool = False


class AnalysisResponse(BaseModel):
    summary: str = "영상 요약을 생성하지 못했습니다."
    mainClaims: List[str] = Field(default_factory=list)
    evidenceSummary: str = "근거 정보가 충분하지 않습니다."
    cautionPoints: List[str] = Field(default_factory=list)

    sourceUsed: str = "metadata"
    sourceLabel: str = "제목·채널 메타데이터"
    commentsIncluded: bool = False
    commentsCount: int = 0

    commentMood: str = "댓글 분석 정보 없음"
    commentIntensity: str = "알 수 없음"
    commentLeaning: str = "알 수 없음"
    commentWarningSignals: List[str] = Field(default_factory=list)
    commentFlow: CommentFlow = Field(default_factory=CommentFlow)

    isPolitical: bool = False
    biasScore: int = Field(default=0, ge=-5, le=5)
    biasLabel: str = "중립에 가까움"
    biasSummary: str = ""
    biasCriteria: List[str] = Field(default_factory=list)
    biasConfidence: float = Field(default=0.0, ge=0.0, le=1.0)
    biasSignals: BiasSignals = Field(default_factory=BiasSignals)

    aiRisk: str = "low"
    aiSummary: str = ""
    issue: str = "핵심 이슈"
    searchQueries: SearchQueries = Field(default_factory=SearchQueries)

    similarResources: List[Resource] = Field(default_factory=list)
    oppositeResources: List[Resource] = Field(default_factory=list)
    neutralResources: List[Resource] = Field(default_factory=list)
    verificationResources: List[Resource] = Field(default_factory=list)
    checklist: List[str] = Field(default_factory=list)

    cached: bool = False
    resourcesCached: bool = False
    analysisProvider: str = "mock"
    analysisModel: str = "mock"
    promptVersion: str = "crossview-bias-v2"
    warnings: List[str] = Field(default_factory=list)
