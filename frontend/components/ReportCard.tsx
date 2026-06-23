type Props = {
  eyebrow: string;
  value: string;
  description: string;
  tone?: "default" | "blue" | "red" | "amber";
};

export function ReportCard({ eyebrow, value, description, tone = "default" }: Props) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <p className="metric-eyebrow">{eyebrow}</p>
      <strong className="metric-value">{value}</strong>
      <p className="metric-description">{description}</p>
    </article>
  );
}
