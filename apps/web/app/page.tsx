import { BentoCard } from "@/components/BentoCard";
import { DataTable } from "@/components/DataTable";
import { InsightCard } from "@/components/InsightCard";
import { MetricCard } from "@/components/MetricCard";
import { PlatformChart } from "@/components/PlatformChart";
import { ScoreBar } from "@/components/ScoreBar";
import { SentimentChart } from "@/components/SentimentChart";
import { StatusBadge } from "@/components/StatusBadge";
import { getDashboardSummary } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const summary = await getDashboardSummary();
  const negativeRate = `${summary.negative_voc_rate}%`;
  const totalTopics = summary.topic_clusters.reduce((s, t) => s + t.count, 0);

  return (
    <div className="space-y-8">
      {/* KPI Row */}
      <section className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Total VOC Collected" value={summary.total_voc_collected} trend="+demo" tone="primary" />
        <MetricCard label="High Priority Leads" value={summary.high_priority_leads} trend="+rule" />
        <MetricCard label="Negative VOC Rate" value={negativeRate} tone="error" />
        <MetricCard label="Purchase Intent Detected" value={summary.purchase_intent_detected} />
      </section>

      {/* VOC Analysis + AI Insight */}
      <section className="grid grid-cols-12 gap-6">
        <BentoCard className="col-span-12 lg:col-span-8">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-semibold">VOC Analysis Panel</h2>
            <a className="text-sm font-semibold text-primary" href="/voc">View Deep Dive →</a>
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
          {summary.featured_insight ? <InsightCard insight={summary.featured_insight} /> : <p className="text-secondary">No insight yet.</p>}
        </BentoCard>
      </section>

      {/* Platform Distribution + Topic Clusters */}
      <section className="grid grid-cols-12 gap-6">
        <BentoCard className="col-span-12 lg:col-span-7">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-semibold">Data Source Distribution</h2>
            <span className="rounded-full bg-surface-low px-3 py-1 text-xs font-semibold text-secondary">
              {summary.total_voc_collected} VOC total
            </span>
          </div>
          <PlatformChart data={summary.platform_distribution} />
          <div className="mt-4 flex flex-wrap gap-3">
            {Object.entries(summary.platform_distribution).map(([name, count]) => (
              <span key={name} className="text-xs text-secondary">
                <strong className="text-charcoal">{name}</strong> {count}건
              </span>
            ))}
          </div>
        </BentoCard>

        <BentoCard className="col-span-12 lg:col-span-5" ai>
          <h2 className="mb-6 text-2xl font-semibold">Strategic Topic Clusters</h2>
          <div className="space-y-3">
            {summary.topic_clusters.map((topic) => {
              const pct = Math.round((topic.count / totalTopics) * 100);
              return (
                <div key={topic.topic}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="font-semibold">{topic.topic}</span>
                    <div className="flex items-center gap-2">
                      <StatusBadge
                        value={topic.status}
                        tone={topic.status === "critical" ? "danger" : topic.status === "rising" ? "primary" : topic.status === "stable" ? "positive" : "neutral"}
                      />
                      <span className="text-xs font-bold text-secondary">{topic.count}건</span>
                    </div>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-container">
                    <div className="h-full rounded-full bg-primary transition-all duration-500" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </BentoCard>
      </section>

      {/* High Priority Leads + Intelligence Pipeline */}
      <section className="grid grid-cols-12 gap-6">
        <BentoCard className="col-span-12 lg:col-span-8">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-semibold">High Priority Lead Scoring</h2>
            <a className="text-sm font-semibold text-primary" href="/lead-scoring">View All →</a>
          </div>
          <DataTable
            headers={["VOC", "Product", "Score", "Risk", "Action"]}
            rows={summary.high_priority_preview.map((record) => [
              <span key="title" className="font-semibold">{record.voc.title}</span>,
              record.voc.product_category,
              <ScoreBar key="score" value={record.lead_score.lead_score} />,
              <StatusBadge key="risk" value={record.lead_score.priority} tone={record.lead_score.priority === "high" ? "danger" : "positive"} />,
              <span key="action" className="font-semibold text-primary">{record.insight.recommended_action.slice(0, 40)}…</span>,
            ])}
          />
        </BentoCard>

        <BentoCard className="col-span-12 lg:col-span-4">
          <h2 className="mb-6 text-center text-2xl font-semibold">Intelligence Pipeline</h2>
          <div className="space-y-2">
            {[
              { step: "VOC 수집", sub: "Danawa · Reddit · Naver · YouTube · X", done: true },
              { step: "텍스트 전처리", sub: "정규화 · 키워드 추출", done: true },
              { step: "NLP 분석", sub: "감성 · 구매의도 · 토픽", done: true },
              { step: "Lead Score 산출", sub: "XGBoost 기반 7요소 점수화", done: true },
              { step: "외부 컨텍스트 결합", sub: "기상청 · AirKorea · 입주물량", done: false },
              { step: "LLM 전략 인사이트", sub: "GPT/Gemini 기반 추천", done: false },
            ].map(({ step, sub, done }, i) => (
              <div key={step} className="flex items-start gap-3">
                <div className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${done ? "bg-primary text-white" : "bg-surface-container text-secondary"}`}>
                  {done ? "✓" : i + 1}
                </div>
                <div className={`flex-1 rounded-lg px-3 py-2 ${done ? "border border-primary/10 bg-primary/5" : "bg-surface-low"}`}>
                  <p className={`text-sm font-semibold ${done ? "text-primary" : "text-secondary"}`}>{step}</p>
                  <p className="text-xs text-secondary">{sub}</p>
                </div>
              </div>
            ))}
          </div>
        </BentoCard>
      </section>
    </div>
  );
}
