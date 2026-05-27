interface MetricCardProps {
  label: string;
  value: string | number;
  trend?: string;
  tone?: "primary" | "neutral" | "error";
}

export function MetricCard({ label, value, trend, tone = "neutral" }: MetricCardProps) {
  const valueColor = tone === "primary" ? "text-primary" : tone === "error" ? "text-error" : "text-charcoal";
  const barColor = tone === "error" ? "bg-error" : "bg-primary";
  const isUp = trend && !trend.startsWith("-");

  return (
    <div className="group rounded-xl bg-surface p-6 shadow-soft transition-shadow hover:shadow-md">
      <p className="text-xs font-semibold uppercase tracking-widest text-secondary">{label}</p>
      <div className="mt-3 flex items-end gap-2">
        <strong className={`text-5xl font-bold leading-none tabular-nums ${valueColor}`}>{value}</strong>
        {trend && (
          <span className={`mb-1 flex items-center gap-0.5 text-xs font-bold ${isUp ? "text-emerald-600" : "text-error"}`}>
            {isUp ? "↑" : "↓"} {trend}
          </span>
        )}
      </div>
      <div className="mt-5 h-1 rounded-full bg-surface-container overflow-hidden">
        <div className={`h-full rounded-full ${barColor} transition-all duration-700`} style={{ width: "72%" }} />
      </div>
    </div>
  );
}
