type Props = { leftRatio: number; neutralRatio: number; rightRatio: number };

export function BiasChart({ leftRatio, neutralRatio, rightRatio }: Props) {
  const empty = leftRatio + neutralRatio + rightRatio === 0;
  if (empty) return <div className="empty-inline">정치·시사 영상 기록이 아직 없습니다.</div>;

  return (
    <div>
      <div className="stacked-bar" aria-label="좌 중립 우 시청 비율">
        {leftRatio > 0 && <div className="bar-left" style={{ width: `${leftRatio}%` }}>좌 {leftRatio}%</div>}
        {neutralRatio > 0 && <div className="bar-neutral" style={{ width: `${neutralRatio}%` }}>중립 {neutralRatio}%</div>}
        {rightRatio > 0 && <div className="bar-right" style={{ width: `${rightRatio}%` }}>우 {rightRatio}%</div>}
      </div>
      <div className="chart-legend">
        <span><i className="dot left-dot" />좌측 추정</span>
        <span><i className="dot neutral-dot" />중립 범위</span>
        <span><i className="dot right-dot" />우측 추정</span>
      </div>
    </div>
  );
}
