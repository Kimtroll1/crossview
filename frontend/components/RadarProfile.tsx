export function RadarProfile({ values }: { values: Array<{ label: string; value: number }> }) {
  const center = 120;
  const radius = 88;
  const count = values.length;
  const point = (index: number, factor: number) => {
    const angle = -Math.PI / 2 + (Math.PI * 2 * index) / count;
    return [center + Math.cos(angle) * radius * factor, center + Math.sin(angle) * radius * factor];
  };
  const polygon = values.map((item, index) => point(index, Math.max(0, Math.min(5, item.value)) / 5).join(",")).join(" ");
  const grid = [0.25, 0.5, 0.75, 1].map((factor) => values.map((_, index) => point(index, factor).join(",")).join(" "));
  return (
    <div className="radar-wrap">
      <svg viewBox="0 0 240 240" role="img" aria-label="편향 신호 레이더 차트">
        {grid.map((points, index) => <polygon key={index} points={points} className="radar-grid" />)}
        {values.map((_, index) => { const [x, y] = point(index, 1); return <line key={index} x1={center} y1={center} x2={x} y2={y} className="radar-axis" />; })}
        <polygon points={polygon} className="radar-data" />
        {values.map((item, index) => {
          const [x, y] = point(index, 1.16);
          return <text key={item.label} x={x} y={y} textAnchor="middle" dominantBaseline="middle">{item.label}</text>;
        })}
      </svg>
    </div>
  );
}
