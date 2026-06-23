import type { BiasSignals } from "@/lib/api";

const labels: Array<[keyof BiasSignals, string, string]> = [
  ["emotionalManipulation", "감정·선동", "🔥"],
  ["evidenceSelection", "선택적 근거", "🔍"],
  ["viewpointOmission", "관점 누락", "👥"],
  ["sourceConcentration", "출처 편중", "📚"],
];

export function SignalBars({ signals, compact = false }: { signals: BiasSignals; compact?: boolean }) {
  return (
    <div className={`signal-list ${compact ? "compact" : ""}`}>
      {labels.map(([key, label, icon]) => {
        const item = signals[key];
        return (
          <div className="signal-row" key={key}>
            <div className="signal-label"><span>{icon}</span><strong>{label}</strong><em>{item.label}</em></div>
            <div className="signal-track"><i style={{ width: `${(item.score / 5) * 100}%` }} /></div>
            {!compact && item.reasons?.length > 0 && <p>{item.reasons.slice(0, 2).join(" · ")}</p>}
          </div>
        );
      })}
    </div>
  );
}
