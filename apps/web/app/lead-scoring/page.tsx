import { BentoCard } from "@/components/BentoCard";
import { DataTable } from "@/components/DataTable";
import { FilterBar } from "@/components/FilterBar";
import { MetricCard } from "@/components/MetricCard";
import { ScoreBar } from "@/components/ScoreBar";
import { StatusBadge } from "@/components/StatusBadge";
import { getDashboardSummary, getLeadScores } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function LeadScoringPage() {
  const [summary, leads] = await Promise.all([getDashboardSummary(), getLeadScores()]);
  const selected = leads[0];

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between">
        <div>
          <h2 className="text-4xl font-semibold">Lead Scoring Management</h2>
          <p className="mt-2 text-secondary">Predictive intent scoring powered by demo rule-based analysis.</p>
        </div>
        <button className="rounded-lg bg-primary px-6 py-3 text-sm font-bold text-white">Refresh AI Scores</button>
      </header>

      <section className="grid grid-cols-12 gap-6">
        <div className="col-span-12 md:col-span-3">
          <MetricCard label="High-Intent Leads" value={summary.high_priority_leads} tone="primary" />
        </div>
        <div className="col-span-12 md:col-span-3">
          <MetricCard label="Avg. Lead Score" value={summary.average_lead_score} />
        </div>
        <BentoCard className="col-span-12 md:col-span-6" ai>
          <p className="mb-2 text-sm font-bold text-primary">AI Strategy Insight</p>
          <p className="text-lg leading-8">
            Demo analysis found recurring demand around subscription pricing, air quality, and ThinQ connectivity. High-score VOC should be routed to sales/CX review.
          </p>
        </BentoCard>
      </section>

      <FilterBar />

      <section className="grid grid-cols-12 gap-6">
        <BentoCard className="col-span-12 xl:col-span-8">
          <DataTable
            headers={["VOC", "Category", "Lead Score", "Risk Level", "Intent", "Action"]}
            rows={leads.map((record) => [
              <span key="title" className="font-semibold">{record.voc.title}</span>,
              record.voc.product_category,
              <ScoreBar key="score" value={record.lead_score.lead_score} />,
              <StatusBadge key="risk" value={record.lead_score.priority} tone={record.lead_score.priority === "high" ? "danger" : "positive"} />,
              <StatusBadge key="intent" value={record.analysis.intent_label} tone={record.analysis.intent_label === "high" ? "primary" : "neutral"} />,
              <span key="action" className="font-semibold text-primary">Review</span>
            ])}
          />
        </BentoCard>
        <BentoCard className="col-span-12 xl:col-span-4" ai>
          <h3 className="mb-6 text-3xl font-semibold">AI Breakdown</h3>
          {selected ? (
            <div className="space-y-5">
              <div className="flex items-center justify-between rounded-xl border border-primary/15 bg-white p-4">
                <span className="font-bold">{selected.voc.title}</span>
                <span className="text-3xl font-bold text-primary">{selected.lead_score.lead_score}</span>
              </div>
              {Object.entries(selected.lead_score.score_reason).map(([key, value]) => (
                <div key={key} className="rounded-lg bg-surface-container p-4">
                  <div className="flex justify-between text-sm font-semibold">
                    <span>{key.replaceAll("_", " ")}</span>
                    <span className="text-emerald-700">+{value}</span>
                  </div>
                </div>
              ))}
              <div className="rounded-xl bg-primary p-4 text-white">{selected.insight.recommended_action}</div>
            </div>
          ) : null}
        </BentoCard>
      </section>
    </div>
  );
}
