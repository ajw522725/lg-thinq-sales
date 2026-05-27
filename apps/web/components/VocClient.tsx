"use client";

import { useState } from "react";
import type { DashboardSummary, VocRecord } from "@/types/api";
import { BentoCard } from "./BentoCard";
import { DataTable } from "./DataTable";
import { StatusBadge } from "./StatusBadge";

type SentimentFilter = "all" | "positive" | "neutral" | "negative";
type IntentFilter = "all" | "high" | "medium" | "low";

interface Props {
  vocs: VocRecord[];
  summary: DashboardSummary;
}

export function VocClient({ vocs, summary }: Props) {
  const [sentiment, setSentiment] = useState<SentimentFilter>("all");
  const [intent, setIntent] = useState<IntentFilter>("all");
  const [source, setSource] = useState<string>("all");
  const [keyword, setKeyword] = useState("");

  const sources = ["all", ...Array.from(new Set(vocs.map((r) => r.voc.source)))];

  const filtered = vocs.filter((r) => {
    if (sentiment !== "all" && r.analysis.sentiment_label !== sentiment) return false;
    if (intent !== "all" && r.analysis.intent_label !== intent) return false;
    if (source !== "all" && r.voc.source !== source) return false;
    if (keyword && !r.voc.normalized_text.toLowerCase().includes(keyword.toLowerCase()) && !r.voc.title.toLowerCase().includes(keyword.toLowerCase())) return false;
    return true;
  });

  const selectClass = "rounded-lg border border-surface-high bg-white px-3 py-2 text-sm font-medium text-charcoal focus:border-primary focus:outline-none";

  return (
    <div className="space-y-6">
      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-surface-high bg-white p-4">
        <span className="text-sm font-semibold text-secondary">Filter:</span>

        <select value={sentiment} onChange={(e) => setSentiment(e.target.value as SentimentFilter)} className={selectClass}>
          <option value="all">감성: 전체</option>
          <option value="positive">긍정</option>
          <option value="neutral">중립</option>
          <option value="negative">부정</option>
        </select>

        <select value={intent} onChange={(e) => setIntent(e.target.value as IntentFilter)} className={selectClass}>
          <option value="all">구매의도: 전체</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <select value={source} onChange={(e) => setSource(e.target.value)} className={selectClass}>
          {sources.map((s) => (
            <option key={s} value={s}>{s === "all" ? "플랫폼: 전체" : s}</option>
          ))}
        </select>

        <input
          type="text"
          placeholder="키워드 검색..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="rounded-lg border border-surface-high bg-white px-3 py-2 text-sm focus:border-primary focus:outline-none"
        />

        <span className="ml-auto text-sm text-secondary">
          <strong className="text-charcoal">{filtered.length}</strong> / {vocs.length}건
        </span>

        {(sentiment !== "all" || intent !== "all" || source !== "all" || keyword) && (
          <button
            onClick={() => { setSentiment("all"); setIntent("all"); setSource("all"); setKeyword(""); }}
            className="rounded-lg bg-surface-low px-3 py-2 text-sm font-medium text-secondary hover:text-primary"
          >
            초기화
          </button>
        )}
      </div>

      {/* Urgency + Topic Side-by-side */}
      <section className="grid grid-cols-12 gap-6">
        <BentoCard className="col-span-12 lg:col-span-6">
          <h3 className="mb-5 text-xl font-semibold">Urgency Breakdown</h3>
          <div className="space-y-4">
            {Object.entries(summary.urgency_breakdown).map(([label, value]) => {
              const pct = Math.round((value / summary.total_voc_collected) * 100);
              return (
                <div key={label}>
                  <div className="mb-1 flex justify-between text-sm font-semibold">
                    <span className="capitalize">{label}</span>
                    <span>{value}건 <span className="font-normal text-secondary">({pct}%)</span></span>
                  </div>
                  <div className="h-2 rounded-full bg-surface-container">
                    <div
                      className={`h-full rounded-full ${label === "critical" ? "bg-error" : label === "medium" ? "bg-amber-400" : "bg-emerald-500"}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </BentoCard>

        <BentoCard className="col-span-12 lg:col-span-6" ai>
          <h3 className="mb-5 text-xl font-semibold">Topic Clusters</h3>
          <div className="space-y-3">
            {summary.topic_clusters.map((topic) => (
              <div key={topic.topic} className="flex items-center justify-between rounded-lg border border-primary/10 bg-white p-3">
                <div>
                  <p className="text-sm font-semibold">{topic.topic}</p>
                  <p className="text-xs text-secondary">{topic.count} mentions</p>
                </div>
                <StatusBadge
                  value={topic.status}
                  tone={topic.status === "critical" ? "danger" : topic.status === "rising" ? "primary" : topic.status === "stable" ? "positive" : "neutral"}
                />
              </div>
            ))}
          </div>
        </BentoCard>
      </section>

      {/* VOC Table */}
      <BentoCard>
        <h3 className="mb-6 text-xl font-semibold">
          VOC 목록
          {filtered.length === 0 && <span className="ml-3 text-sm font-normal text-secondary">검색 결과 없음</span>}
        </h3>
        {filtered.length > 0 ? (
          <DataTable
            headers={["VOC 내용", "감성", "구매의도", "플랫폼", "제품", "날짜"]}
            rows={filtered.map((record) => [
              <div key="text">
                <p className="font-semibold">{record.voc.title}</p>
                <p className="mt-0.5 line-clamp-1 text-xs text-secondary">{record.voc.normalized_text}</p>
              </div>,
              <StatusBadge
                key="sent"
                value={record.analysis.sentiment_label}
                tone={record.analysis.sentiment_label === "negative" ? "danger" : record.analysis.sentiment_label === "positive" ? "positive" : "neutral"}
              />,
              <StatusBadge
                key="intent"
                value={record.analysis.intent_label}
                tone={record.analysis.intent_label === "high" ? "primary" : "neutral"}
              />,
              record.voc.source,
              record.voc.product_category,
              new Date(record.voc.published_at).toLocaleDateString("ko-KR"),
            ])}
          />
        ) : (
          <div className="rounded-xl bg-surface-low py-12 text-center text-secondary">
            조건에 맞는 VOC가 없습니다. 필터를 변경해주세요.
          </div>
        )}
      </BentoCard>
    </div>
  );
}
