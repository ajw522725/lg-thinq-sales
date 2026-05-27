import { BentoCard } from "@/components/BentoCard";
import { LeadDetailPanel } from "@/components/LeadDetailPanel";
import { MetricCard } from "@/components/MetricCard";
import { getDashboardSummary, getLeadScores } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function LeadScoringPage() {
  const [summary, leads] = await Promise.all([getDashboardSummary(), getLeadScores()]);

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

      <LeadDetailPanel leads={leads} />
    </div>
  );
}
