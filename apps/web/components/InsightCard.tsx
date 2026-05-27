import type { StrategyInsight } from "@/types/api";
import { StatusBadge } from "./StatusBadge";

interface InsightCardProps {
  insight: StrategyInsight;
  featured?: boolean;
}

export function InsightCard({ insight, featured = false }: InsightCardProps) {
  return (
    <article className={`${featured ? "ai-glow p-8" : "rounded-xl border border-primary/15 bg-white p-6"} rounded-xl`}>
      <div className="mb-4 flex items-center justify-between gap-4">
        <StatusBadge value={insight.priority} tone={insight.priority === "high" ? "primary" : "neutral"} />
        <div className="text-right">
          <div className="text-3xl font-bold text-primary">{Math.round(insight.confidence * 100)}%</div>
          <div className="text-xs font-semibold uppercase text-secondary">Confidence</div>
        </div>
      </div>
      <h3 className="text-2xl font-semibold leading-tight">{insight.title}</h3>
      <p className="mt-4 text-sm leading-6 text-secondary">{insight.summary}</p>
      <div className="mt-5 rounded-lg bg-surface-low p-4 text-sm text-charcoal">{insight.recommended_action}</div>
    </article>
  );
}
