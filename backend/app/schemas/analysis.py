from pydantic import BaseModel, Field
from typing import List, Optional


class VideoContext(BaseModel):
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


class Resource(BaseModel):
    type: str = "youtube"  # youtube | article | ai_answer
    title: str
    source: str = "CrossView 추천"
    url: str = ""
    summary: str = ""
    icon: str = ""


class AnalysisResponse(BaseModel):
    summary: str = "영상 요약을 생성하지 못했습니다."
    mainClaims: List[str] = []
    evidenceSummary: str = "근거 정보가 충분하지 않습니다."
    cautionPoints: List[str] = []

    sourceUsed: str = "metadata"
    sourceLabel: str = "제목·채널 메타데이터"
    commentsIncluded: bool = False
    commentsCount: int = 0

    commentMood: str = "댓글 분석 정보 없음"
    commentIntensity: str = "알 수 없음"
    commentLeaning: str = "알 수 없음"
    commentWarningSignals: List[str] = []

    isPolitical: bool = False
    biasScore: int = Field(default=0, ge=-5, le=5)
    biasLabel: str = "중립에 가까움"
    biasSummary: str

    aiRisk: str = "low"
    aiSummary: str
    issue: str = "핵심 이슈"

    similarResources: List[Resource]
    oppositeResources: List[Resource]
    verificationResources: List[Resource]
    checklist: List[str]
