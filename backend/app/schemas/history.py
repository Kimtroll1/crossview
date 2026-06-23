from pydantic import BaseModel, Field
from app.schemas.analysis import BiasSignals, CommentFlow


class HistoryItem(BaseModel):
    watchedAt: str
    videoId: str
    title: str
    channelName: str = ""
    url: str
    isPolitical: bool = False
    biasScore: int = 0
    biasLabel: str = "중립에 가까움"
    biasConfidence: float = 0
    biasCriteria: list[str] = Field(default_factory=list)
    biasSignals: BiasSignals = Field(default_factory=BiasSignals)
    commentFlow: CommentFlow = Field(default_factory=CommentFlow)
    aiRisk: str = "low"
    issue: str = "핵심 이슈"
    summary: str = ""


class HistoryResponse(BaseModel):
    userId: str
    items: list[HistoryItem] = Field(default_factory=list)
