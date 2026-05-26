import { BentoCard } from "@/components/BentoCard";
import { DataTable } from "@/components/DataTable";
import { SentimentChart } from "@/components/SentimentChart";
import { StatusBadge } from "@/components/StatusBadge";
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

      <section className="grid grid-cols-12 gap-6">
        <BentoCard className="col-span-12 lg:col-span-8">
          <h3 className="text-2xl font-semibold">Sentiment Analysis Trends</h3>
          <p className="mb-4 text-secondary">Aggregate sentiment across demo sources</p>
          <SentimentChart data={summary.sentiment_breakdown} />
        </BentoCard>
        <BentoCard className="col-span-12 lg:col-span-4">
          <h3 className="mb-6 text-2xl font-semibold">Urgency Levels</h3>
          <div className="space-y-4">
            {Object.entries(summary.urgency_breakdown).map(([label, value]) => (
              <div key={label}>
                <div className="mb-1 flex justify-between text-sm font-semibold">
                  <span>{label}</span>
                  <span>{value}</span>
                </div>
                <div className="h-2 rounded-full bg-surface-container">
                  <div className="h-full rounded-full bg-primary" style={{ width: `${(value / summary.total_voc_collected) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </BentoCard>
      </section>

      <section className="grid grid-cols-12 gap-6">
        <BentoCard className="col-span-12 lg:col-span-6" ai>
          <h3 className="mb-6 text-2xl font-semibold">Strategic Topic Clusters</h3>
          <div className="space-y-3">
            {summary.topic_clusters.map((topic) => (
              <div key={topic.topic} className="flex items-center justify-between rounded-lg border border-primary/10 bg-white p-4">
                <div>
                  <p className="font-semibold">{topic.topic}</p>
                  <p className="text-xs text-secondary">{topic.count} mentions</p>
                </div>
                <StatusBadge value={topic.status} tone={topic.status === "critical" ? "danger" : topic.status === "opportunity" ? "positive" : "neutral"} />
              </div>
            ))}
          </div>
        </BentoCard>
        <BentoCard className="col-span-12 lg:col-span-6">
          <h3 className="mb-6 text-2xl font-semibold">NLP Keyword Extraction</h3>
          <div className="flex flex-wrap gap-3">
            {summary.top_keywords.map((keyword) => (
              <span key={keyword} className="rounded-full bg-primary/10 px-4 py-2 text-sm font-bold text-primary">
                {keyword}
              </span>
            ))}
          </div>
        </BentoCard>
      </section>

      <BentoCard>
        <h3 className="mb-6 text-2xl font-semibold">Recent Voice of Customer Snippets</h3>
        <DataTable
          headers={["Feedback Snippet", "NLP Sentiment", "Extracted Intent", "Source", "Time"]}
          rows={vocs.slice(0, 8).map((record) => [
            <span key="snippet" className="line-clamp-2">{record.voc.normalized_text}</span>,
            <StatusBadge key="sentiment" value={record.analysis.sentiment_label} tone={record.analysis.sentiment_label === "negative" ? "danger" : record.analysis.sentiment_label === "positive" ? "positive" : "neutral"} />,
            <StatusBadge key="intent" value={record.analysis.intent_label} tone={record.analysis.intent_label === "high" ? "primary" : "neutral"} />,
            record.voc.source,
            new Date(record.voc.published_at).toLocaleDateString()
          ])}
        />
      </BentoCard>
    </div>
  );
}
