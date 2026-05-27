import { BentoCard } from "@/components/BentoCard";
import { DataTable } from "@/components/DataTable";
import { InsightCard } from "@/components/InsightCard";
import { MetricCard } from "@/components/MetricCard";
import { ScoreBar } from "@/components/ScoreBar";
import { SentimentChart } from "@/components/SentimentChart";
import { StatusBadge } from "@/components/StatusBadge";
import { getDashboardSummary } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const summary = await getDashboardSummary();
  const negativeRate = `${summary.negative_voc_rate}%`;

  return (
    <div className="space-y-8">
      <section className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Total VOC Collected" value={summary.total_voc_collected} trend="+demo" tone="primary" />
        <MetricCard label="High Priority Leads" value={summary.high_priority_leads} trend="+rule" />
        <MetricCard label="Negative VOC Rate" value={negativeRate} tone="error" />
        <MetricCard label="Purchase Intent Detected" value={summary.purchase_intent_detected} />
      </section>

      <section className="grid grid-cols-12 gap-6">
        <BentoCard className="col-span-12 lg:col-span-8">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-semibold">VOC Analysis Panel</h2>
            <a className="text-sm font-semibold text-primary" href="/voc">
              View Deep Dive
            </a>
          </div>
          <div className="grid gap-8 lg:grid-cols-2">
            <div>
              <p className="mb-4 text-xs font-bold uppercase tracking-widest text-secondary">Sentiment Breakdown</p>
              <SentimentChart data={summary.sentiment_breakdown} />
            </div>
            <div>
              <p className="mb-4 text-xs font-bold uppercase tracking-widest text-secondary">Top Keyword Tags</p>
              <div className="flex flex-wrap gap-2">
                {summary.top_keywords.map((keyword) => (
                  <StatusBadge key={keyword} value={keyword} tone={keyword.toLowerCase().includes("subscription") ? "primary" : "neutral"} />
                ))}
              </div>
            </div>
          </div>
        </BentoCard>

        <BentoCard className="col-span-12 lg:col-span-4" ai>
          <h2 className="mb-6 text-2xl font-semibold">AI Strategy Insight</h2>
          {summary.featured_insight ? <InsightCard insight={summary.featured_insight} /> : <p>No insight yet.</p>}
        </BentoCard>
      </section>

      <section className="grid grid-cols-12 gap-6">
        <BentoCard className="col-span-12 lg:col-span-8">
          <h2 className="mb-6 text-2xl font-semibold">High Priority Lead Scoring</h2>
          <DataTable
            headers={["VOC", "Product", "Score", "Risk", "Action"]}
            rows={summary.high_priority_preview.map((record) => [
              <span key="title" className="font-semibold">{record.voc.title}</span>,
              record.voc.product_category,
              <ScoreBar key="score" value={record.lead_score.lead_score} />,
              <StatusBadge key="risk" value={record.lead_score.priority} tone={record.lead_score.priority === "high" ? "danger" : "positive"} />,
              <span key="action" className="font-semibold text-primary">{record.insight.recommended_action}</span>
            ])}
          />
        </BentoCard>
        <BentoCard className="col-span-12 lg:col-span-4">
          <h2 className="mb-6 text-center text-2xl font-semibold">Intelligence Pipeline</h2>
          <div className="space-y-4">
            {["VOC", "NLP Analysis", "Lead Score", "Context Match", "Strategy Insight"].map((step) => (
              <div key={step} className="rounded-lg border border-primary/10 bg-surface-low px-4 py-3 text-center font-semibold text-primary">
                {step}
              </div>
            ))}
          </div>
        </BentoCard>
      </section>
    </div>
  );
}
