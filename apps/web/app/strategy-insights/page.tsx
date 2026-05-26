import { BentoCard } from "@/components/BentoCard";
import { DataTable } from "@/components/DataTable";
import { InsightCard } from "@/components/InsightCard";
import { StatusBadge } from "@/components/StatusBadge";
import { getInsights, getLeadScores } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function StrategyInsightsPage() {
  const [insights, records] = await Promise.all([getInsights(), getLeadScores()]);
  const featured = insights[0];
  const urgent = records.find((record) => record.analysis.urgency_label === "critical") ?? records[1];

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between">
        <div>
          <h2 className="text-4xl font-semibold">AI Strategy Recommendations</h2>
          <p className="mt-2 text-secondary">High-impact insights derived from multi-channel demo customer intelligence.</p>
        </div>
        <div className="flex gap-3">
          <button className="rounded-lg border border-primary/30 px-5 py-3 text-sm font-semibold">Filters</button>
          <button className="rounded-lg border border-primary/30 px-5 py-3 text-sm font-semibold">Export Report</button>
        </div>
      </header>

      <section className="grid grid-cols-12 gap-6">
        <div className="col-span-12 lg:col-span-8">{featured ? <InsightCard insight={featured} featured /> : null}</div>
        <BentoCard className="col-span-12 lg:col-span-4">
          <StatusBadge value="Urgent Follow-up" tone="danger" />
          <h3 className="mt-6 text-3xl font-semibold">{urgent?.insight.title}</h3>
          <p className="mt-5 leading-7 text-secondary">{urgent?.insight.reasoning}</p>
          <div className="mt-6 flex justify-between border-t border-surface-high pt-4 text-sm">
            <span>Confidence</span>
            <strong>{urgent ? Math.round(urgent.insight.confidence * 100) : 0}%</strong>
          </div>
          <button className="mt-6 w-full rounded-lg bg-primary py-3 text-sm font-bold text-white">Execute Strategy</button>
        </BentoCard>
      </section>

      <section className="grid grid-cols-12 gap-6">
        {insights.slice(1, 4).map((insight) => (
          <div key={insight.id} className="col-span-12 md:col-span-4">
            <InsightCard insight={insight} />
          </div>
        ))}
        <BentoCard className="col-span-12 bg-charcoal text-white md:col-span-4">
          <h3 className="text-3xl font-semibold">Market Sentiment Shift</h3>
          <p className="mt-4 leading-7 text-white/70">Demo mode detected rising demand for air quality, subscription care, and energy efficiency topics.</p>
          <div className="mt-8 flex gap-2">
            {["AQ", "SC", "EE"].map((label) => (
              <span key={label} className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-xs font-bold">
                {label}
              </span>
            ))}
          </div>
        </BentoCard>
      </section>

      <BentoCard>
        <h3 className="mb-6 text-2xl font-semibold">Live Intelligence Feed</h3>
        <DataTable
          headers={["Timestamp", "Category", "Insight Summary", "Sentiment", "Action"]}
          rows={records.slice(0, 8).map((record) => [
            new Date(record.voc.published_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            <StatusBadge key="topic" value={record.analysis.topic_label} />,
            record.insight.summary,
            <StatusBadge key="sentiment" value={record.analysis.sentiment_label} tone={record.analysis.sentiment_label === "negative" ? "danger" : record.analysis.sentiment_label === "positive" ? "positive" : "neutral"} />,
            <span key="action" className="font-semibold text-primary">Analyze Deeply</span>
          ])}
        />
      </BentoCard>
    </div>
  );
}
