interface MetricCardProps {
  label: string;
  value: string | number;
  trend?: string;
  tone?: "primary" | "neutral" | "error";
}

export function MetricCard({ label, value, trend, tone = "neutral" }: MetricCardProps) {
  const valueColor = tone === "primary" ? "text-primary" : tone === "error" ? "text-error" : "text-charcoal";
  return (
    <div className="rounded-xl bg-surface p-6 shadow-soft">
      <p className="text-sm font-medium text-secondary">{label}</p>
      <div className="mt-2 flex items-end gap-2">
        <strong className={`text-5xl font-bold leading-none ${valueColor}`}>{value}</strong>
        {trend ? <span className="mb-1 text-sm font-semibold text-emerald-600">{trend}</span> : null}
      </div>
      <div className="mt-5 h-1.5 rounded-full bg-surface-container">
        <div className={`h-full rounded-full ${tone === "error" ? "bg-error" : "bg-primary"}`} style={{ width: "72%" }} />
      </div>
    </div>
  );
}
