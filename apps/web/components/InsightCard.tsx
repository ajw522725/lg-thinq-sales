import type { StrategyInsight } from "@/types/api";
import { StatusBadge } from "./StatusBadge";

interface InsightCardProps {
  insight: StrategyInsight;
  featured?: boolean;
}

export function InsightCard({ insight, featured = false }: InsightCardProps) {
  const confidencePct = Math.round(insight.confidence * 100);

  if (featured) {
    return (
      <article className="ai-glow rounded-xl p-8">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div className="flex gap-2">
            <StatusBadge value={insight.priority} tone={insight.priority === "high" ? "danger" : insight.priority === "medium" ? "neutral" : "positive"} />
            <StatusBadge value="AI Generated" tone="primary" />
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-primary">{confidencePct}%</div>
            <div className="text-xs font-semibold uppercase tracking-widest text-secondary">Confidence</div>
          </div>
        </div>

        <h3 className="text-3xl font-semibold leading-tight">{insight.title}</h3>
        <p className="mt-4 text-base leading-7 text-secondary">{insight.summary}</p>

        <div className="mt-6 rounded-xl border border-primary/15 bg-white p-5">
          <p className="mb-2 text-xs font-bold uppercase tracking-widest text-primary">Recommended Action</p>
          <p className="text-sm font-semibold leading-relaxed">{insight.recommended_action}</p>
        </div>

        <div className="mt-4 rounded-xl bg-surface-low p-5">
          <p className="mb-2 text-xs font-bold uppercase tracking-widest text-secondary">Analysis Reasoning</p>
          <p className="text-sm leading-relaxed text-charcoal">{insight.reasoning}</p>
        </div>

        <div className="mt-6 flex items-center justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-secondary">Target Segment</p>
            <p className="mt-1 text-sm font-semibold">{insight.target_segment}</p>
          </div>
          <div className="w-32">
            <p className="mb-1.5 text-right text-xs font-bold text-secondary">Confidence</p>
            <div className="h-2 overflow-hidden rounded-full bg-surface-container">
              <div className="h-full rounded-full bg-primary" style={{ width: `${confidencePct}%` }} />
            </div>
          </div>
        </div>
      </article>
    );
  }

  return (
    <article className="h-full rounded-xl border border-primary/10 bg-white p-6 transition-shadow hover:shadow-soft">
      <div className="mb-4 flex items-center justify-between">
        <StatusBadge value={insight.priority} tone={insight.priority === "high" ? "danger" : insight.priority === "medium" ? "neutral" : "positive"} />
        <span className="text-sm font-bold text-primary">{confidencePct}%</span>
      </div>

      <h3 className="text-lg font-semibold leading-snug">{insight.title}</h3>
      <p className="mt-3 text-sm leading-6 text-secondary line-clamp-3">{insight.summary}</p>

      <div className="mt-4 rounded-lg bg-surface-low px-4 py-3 text-xs font-medium leading-5 text-charcoal">
        {insight.recommended_action}
      </div>

      <div className="mt-4 flex items-center justify-between text-xs text-secondary">
        <span className="truncate max-w-[60%]">🎯 {insight.target_segment}</span>
        <div className="flex items-center gap-1.5">
          <div className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-container">
            <div className="h-full rounded-full bg-primary" style={{ width: `${confidencePct}%` }} />
          </div>
        </div>
      </div>
    </article>
  );
}
