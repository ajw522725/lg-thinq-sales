interface StatusBadgeProps {
  value: string;
  tone?: "positive" | "neutral" | "warning" | "danger" | "primary";
}

export function StatusBadge({ value, tone = "neutral" }: StatusBadgeProps) {
  const className = {
    positive: "bg-emerald-100 text-emerald-800",
    neutral: "bg-surface-container text-secondary",
    warning: "bg-amber-100 text-amber-800",
    danger: "bg-red-100 text-red-800",
    primary: "bg-primary/10 text-primary"
  }[tone];

  return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-bold uppercase ${className}`}>{value}</span>;
}
