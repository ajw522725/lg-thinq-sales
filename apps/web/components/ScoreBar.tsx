interface ScoreBarProps {
  value: number;
}

export function ScoreBar({ value }: ScoreBarProps) {
  const color = value >= 80 ? "bg-primary" : value >= 50 ? "bg-amber-500" : "bg-slate-400";
  return (
    <div className="flex min-w-32 items-center gap-3">
      <div className="h-2 w-24 overflow-hidden rounded-full bg-surface-container">
        <div className={`h-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-sm font-bold">{value}</span>
    </div>
  );
}
