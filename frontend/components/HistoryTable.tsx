import type { HistoryItem } from "@/lib/api";
import { SignalBars } from "./SignalBars";

function riskLabel(risk: HistoryItem["aiRisk"]) {
  if (risk === "high") return "AI 의심 높음";
  if (risk === "medium") return "AI 의심 일부";
  return "AI 의심 낮음";
}

export function HistoryTable({ items, compact = false }: { items: HistoryItem[]; compact?: boolean }) {
  const visible = compact ? items.slice(0, 5) : items;
  if (!visible.length) return <div className="empty-state">아직 분석 기록이 없습니다. 유튜브 영상에서 CrossView 분석을 실행해보세요.</div>;
  return (
    <div className="history-list">
      {visible.map((item) => (
        <article className="history-row" key={item.videoId}>
          <div className="history-main">
            <div className="history-topline"><span className="topic-chip">{item.issue || "기타"}</span><time>{new Date(item.watchedAt).toLocaleDateString("ko-KR")}</time></div>
            <a href={item.url} target="_blank" rel="noreferrer"><h3>{item.title}</h3></a>
            <p className="channel">{item.channelName || "채널 정보 없음"}</p>
            <p className="history-summary">{item.summary}</p>
            {!compact && <SignalBars signals={item.biasSignals} compact />}
            {!compact && item.commentFlow?.summary && <p className="criteria-preview">댓글: {item.commentFlow.summary}</p>}
          </div>
          <div className="history-badges">
            <span className={`bias-pill ${item.biasScore < -1 ? "left" : item.biasScore > 1 ? "right" : "neutral"}`}>{item.biasLabel}</span>
            <span className={`risk-pill ${item.aiRisk}`}>{riskLabel(item.aiRisk)}</span>
            {item.isPolitical && <span className="confidence-pill">신뢰도 {Math.round(item.biasConfidence * 100)}%</span>}
          </div>
        </article>
      ))}
    </div>
  );
}
