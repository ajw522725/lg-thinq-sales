import { BentoCard } from "@/components/BentoCard";
import { DataTable } from "@/components/DataTable";
import { InsightCard } from "@/components/InsightCard";
import { StatusBadge } from "@/components/StatusBadge";
import { getInsights, getLeadScores } from "@/lib/api";

export const dynamic = "force-dynamic";

const CONTEXT_META: Record<string, { icon: string; label: string; color: string }> = {
  air_quality:  { icon: "🌫️", label: "대기질",     color: "border-emerald-200 bg-emerald-50" },
  weather:      { icon: "🌤️", label: "기상",        color: "border-sky-200 bg-sky-50" },
  energy:       { icon: "⚡",  label: "전기요금",    color: "border-amber-200 bg-amber-50" },
  housing:      { icon: "🏠",  label: "입주물량",    color: "border-violet-200 bg-violet-50" },
};

export default async function StrategyInsightsPage() {
  const [insights, records] = await Promise.all([getInsights(), getLeadScores()]);

  const featured = insights[0];
  const urgentRecord = records.find((r) => r.analysis.urgency_label === "critical") ?? records[0];
  const highRecords = records.filter((r) => r.lead_score.priority === "high");

  /* 컨텍스트 — context_type별로 고유하게 */
  const contextMap = new Map<string, (typeof records)[0]>();
  for (const r of records) {
    if (!contextMap.has(r.context.context_type)) contextMap.set(r.context.context_type, r);
  }
  const contextEntries = Array.from(contextMap.values());

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between">
        <div>
          <h2 className="text-4xl font-semibold">AI Strategy Recommendations</h2>
          <p className="mt-2 text-secondary">High-impact insights derived from multi-channel demo customer intelligence.</p>
        </div>
        <div className="flex gap-3">
          <button className="rounded-lg border border-primary/30 px-5 py-3 text-sm font-semibold hover:bg-surface-low">Filters</button>
          <button className="rounded-lg bg-primary px-5 py-3 text-sm font-bold text-white">Export Report</button>
        </div>
      </header>

      {/* Featured + Urgent */}
      <section className="grid grid-cols-12 gap-6">
        <div className="col-span-12 lg:col-span-8">
          {featured ? <InsightCard insight={featured} featured /> : null}
        </div>
        <BentoCard className="col-span-12 lg:col-span-4">
          <StatusBadge value="Urgent Follow-up" tone="danger" />
          <h3 className="mt-5 text-2xl font-semibold leading-snug">{urgentRecord?.insight.title}</h3>
          <p className="mt-4 text-sm leading-7 text-secondary">{urgentRecord?.insight.reasoning}</p>
          <div className="mt-5 rounded-lg bg-surface-low p-4 text-xs font-medium leading-5 text-charcoal">
            {urgentRecord?.insight.recommended_action}
          </div>
          <div className="mt-5 flex justify-between border-t border-surface-high pt-4 text-sm">
            <span className="text-secondary">Target</span>
            <strong className="text-right text-xs">{urgentRecord?.insight.target_segment}</strong>
          </div>
          <div className="mt-3 flex justify-between text-sm">
            <span className="text-secondary">Confidence</span>
            <strong className="text-primary">{urgentRecord ? Math.round(urgentRecord.insight.confidence * 100) : 0}%</strong>
          </div>
          <button className="mt-6 w-full rounded-lg bg-primary py-3 text-sm font-bold text-white hover:bg-primary-strong transition-colors">
            Execute Strategy
          </button>
        </BentoCard>
      </section>

      {/* External Context Signals */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-semibold">External Context Signals</h2>
          <span className="rounded-full bg-surface-low px-3 py-1 text-xs font-semibold text-secondary">Demo data</span>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {contextEntries.map((record) => {
            const meta = CONTEXT_META[record.context.context_type] ?? { icon: "📊", label: record.context.context_type, color: "border-surface-high bg-surface-low" };
            return (
              <div key={record.context.context_type} className={`rounded-xl border p-5 ${meta.color}`}>
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-2xl">{meta.icon}</span>
                  <span className="rounded-full bg-white/70 px-2 py-0.5 text-xs font-bold text-charcoal">
                    {Math.round(record.context.match_score * 100)}% match
                  </span>
                </div>
                <p className="font-bold">{meta.label}</p>
                <p className="mt-1 text-xs text-secondary">{record.context.region}</p>
                <p className="mt-2 text-xs leading-relaxed text-charcoal">{record.context.match_reason}</p>
                <div className="mt-3 text-xs font-semibold text-primary">
                  → {record.voc.product_category}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* High Priority Insight Cards */}
      <section>
        <h2 className="mb-4 text-2xl font-semibold">High Priority Recommendations</h2>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
          {highRecords.slice(0, 3).map((record) => (
            <InsightCard key={record.insight.id} insight={record.insight} />
          ))}
        </div>
      </section>

      {/* All Insights — remaining */}
      <section className="grid grid-cols-12 gap-6">
        {insights.slice(1, 4).map((insight) => (
          <div key={insight.id} className="col-span-12 md:col-span-4">
            <InsightCard insight={insight} />
          </div>
        ))}
        <BentoCard className="col-span-12 bg-charcoal text-white md:col-span-4">
          <p className="text-xs font-bold uppercase tracking-widest text-white/50">Market Signal</p>
          <h3 className="mt-3 text-2xl font-semibold">Sentiment Shift</h3>
          <p className="mt-3 text-sm leading-7 text-white/70">
            Demo mode detected rising demand for air quality, subscription care, and energy efficiency topics.
          </p>
          <div className="mt-6 flex gap-2">
            {[["AQ", "대기질"], ["SC", "구독케어"], ["EE", "에너지효율"]].map(([abbr, label]) => (
              <div key={abbr} className="text-center">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-xs font-bold">
                  {abbr}
                </span>
                <p className="mt-1 text-xs text-white/50">{label}</p>
              </div>
            ))}
          </div>
        </BentoCard>
      </section>

      {/* Live Intelligence Feed */}
      <BentoCard>
        <h3 className="mb-6 text-2xl font-semibold">Live Intelligence Feed</h3>
        <DataTable
          headers={["시간", "토픽", "인사이트 요약", "감성", "우선순위"]}
          rows={records.slice(0, 8).map((record) => [
            new Date(record.voc.published_at).toLocaleDateString("ko-KR"),
            <StatusBadge key="topic" value={record.analysis.topic_label} />,
            <span key="summary" className="line-clamp-2 text-sm">{record.insight.summary}</span>,
            <StatusBadge key="sent" value={record.analysis.sentiment_label} tone={record.analysis.sentiment_label === "negative" ? "danger" : record.analysis.sentiment_label === "positive" ? "positive" : "neutral"} />,
            <StatusBadge key="priority" value={record.lead_score.priority} tone={record.lead_score.priority === "high" ? "danger" : record.lead_score.priority === "medium" ? "neutral" : "positive"} />,
          ])}
        />
      </BentoCard>
    </div>
  );
}
