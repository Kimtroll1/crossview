from pydantic import BaseModel, Field
from app.schemas.analysis import Resource


class SignalAverages(BaseModel):
    emotionalManipulation: float = 0
    evidenceSelection: float = 0
    viewpointOmission: float = 0
    sourceConcentration: float = 0
    opinionConcentration: float = 0
    commentEmotionIntensity: float = 0


class ReportResponse(BaseModel):
    userId: str
    period: str
    periodStart: str
    periodEnd: str
    totalVideos: int = 0
    politicalVideos: int = 0
    averageBiasScore: float = 0
    averageBiasConfidence: float = 0
    leftRatio: float = 0
    neutralRatio: float = 0
    rightRatio: float = 0
    aiRiskCount: int = 0
    aiRiskRatio: float = 0
    topTopics: list[str] = Field(default_factory=list)
    suggestion: str = ""
    biasDistribution: dict[str, int] = Field(default_factory=dict)
    signalAverages: SignalAverages = Field(default_factory=SignalAverages)
    resourceClicks: int = 0
    alternativeResourceClicks: int = 0
    alternativeExplorationRate: float = 0
    recommendedResources: list[Resource] = Field(default_factory=list)
