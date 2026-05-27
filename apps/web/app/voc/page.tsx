import { BentoCard } from "@/components/BentoCard";
import { SentimentChart } from "@/components/SentimentChart";
import { VocClient } from "@/components/VocClient";
import { getDashboardSummary, getVocs } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function VocPage() {
  const [summary, vocs] = await Promise.all([getDashboardSummary(), getVocs()]);

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between">
        <div>
          <h2 className="text-4xl font-semibold">VOC Detail Analysis</h2>
          <p className="mt-2 text-secondary">Rule-based NLP insights extracted from demo customer interactions.</p>
        </div>
        <button className="rounded-lg bg-primary px-6 py-3 text-sm font-bold text-white">Export Insights</button>
      </header>

      <BentoCard>
        <h3 className="mb-1 text-2xl font-semibold">Sentiment Analysis</h3>
        <p className="mb-6 text-secondary">Aggregate sentiment across demo sources</p>
        <SentimentChart data={summary.sentiment_breakdown} />
      </BentoCard>

      <VocClient vocs={vocs} summary={summary} />
    </div>
  );
}
