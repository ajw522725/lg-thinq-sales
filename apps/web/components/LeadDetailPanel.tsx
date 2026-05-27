"use client";

import { useState } from "react";
import type { VocRecord } from "@/types/api";
import { BentoCard } from "./BentoCard";
import { ScoreBar } from "./ScoreBar";
import { StatusBadge } from "./StatusBadge";

const SCORE_MAX: Record<string, number> = {
  purchase_intent: 35,
  urgency: 15,
  competitor_comparison: 10,
  product_category: 10,
  external_context: 10,
  sentiment_adjustment: 10,
  engagement: 10,
};

const FACTOR_LABEL: Record<string, string> = {
  purchase_intent: "Purchase Intent",
  urgency: "Urgency",
  competitor_comparison: "Competitor Signal",
  product_category: "Product Category",
  external_context: "External Context",
  sentiment_adjustment: "Sentiment",
  engagement: "Engagement",
};

interface Props {
  leads: VocRecord[];
}

export function LeadDetailPanel({ leads }: Props) {
  const [selectedId, setSelectedId] = useState<string>(leads[0]?.voc.id ?? "");
  const selected = leads.find((r) => r.voc.id === selectedId) ?? leads[0];

  return (
    <section className="grid grid-cols-12 gap-6">
      {/* Lead Table */}
      <BentoCard className="col-span-12 xl:col-span-7">
        <h3 className="mb-5 text-xl font-semibold">All Leads</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-container">
                {["VOC", "Category", "Score", "Priority", "Intent"].map((h) => (
                  <th key={h} className="pb-3 pr-4 text-left text-xs font-semibold uppercase tracking-widest text-secondary">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {leads.map((record) => {
                const isSelected = record.voc.id === selectedId;
                return (
                  <tr
                    key={record.voc.id}
                    onClick={() => setSelectedId(record.voc.id)}
                    className={`cursor-pointer border-b border-surface-container/60 transition-colors last:border-0 hover:bg-primary/5 ${
                      isSelected ? "bg-primary/10 ring-1 ring-inset ring-primary/20" : ""
                    }`}
                  >
                    <td className="py-4 pr-4">
                      <span className={`font-semibold ${isSelected ? "text-primary" : ""}`}>
                        {record.voc.title}
                      </span>
                      <p className="mt-0.5 max-w-[200px] truncate text-xs text-secondary">
                        {record.voc.source} · {record.voc.region ?? "전국"}
                      </p>
                    </td>
                    <td className="py-4 pr-4 text-secondary">{record.voc.product_category}</td>
                    <td className="py-4 pr-4">
                      <ScoreBar value={record.lead_score.lead_score} />
                    </td>
                    <td className="py-4 pr-4">
                      <StatusBadge
                        value={record.lead_score.priority}
                        tone={record.lead_score.priority === "high" ? "danger" : record.lead_score.priority === "medium" ? "neutral" : "positive"}
                      />
                    </td>
                    <td className="py-4">
                      <StatusBadge
                        value={record.analysis.intent_label}
                        tone={record.analysis.intent_label === "high" ? "primary" : "neutral"}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </BentoCard>

      {/* Detail Panel */}
      <div className="col-span-12 xl:col-span-5 space-y-4">
        {selected && (
          <>
            {/* Score Header */}
            <BentoCard ai>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-widest text-primary">Selected Lead</p>
                  <h3 className="mt-2 text-lg font-semibold leading-tight">{selected.voc.title}</h3>
                  <p className="mt-1 text-sm text-secondary">{selected.voc.product_category} · {selected.voc.source}</p>
                </div>
                <div className="text-right">
                  <span className="text-5xl font-bold text-primary">{selected.lead_score.lead_score}</span>
                  <p className="text-xs text-secondary">/ 100</p>
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <StatusBadge
                  value={selected.lead_score.priority}
                  tone={selected.lead_score.priority === "high" ? "danger" : selected.lead_score.priority === "medium" ? "neutral" : "positive"}
                />
                <StatusBadge value={selected.analysis.sentiment_label} tone={selected.analysis.sentiment_label === "negative" ? "danger" : selected.analysis.sentiment_label === "positive" ? "positive" : "neutral"} />
                <StatusBadge value={selected.analysis.topic_label} />
              </div>
            </BentoCard>

            {/* Score Breakdown */}
            <BentoCard>
              <h4 className="mb-5 text-sm font-bold uppercase tracking-widest text-secondary">Score Breakdown</h4>
              <div className="space-y-3">
                {Object.entries(selected.lead_score.score_reason).map(([key, val]) => {
                  const max = SCORE_MAX[key] ?? 10;
                  const pct = Math.round((val / max) * 100);
                  const label = FACTOR_LABEL[key] ?? key.replaceAll("_", " ");
                  return (
                    <div key={key}>
                      <div className="mb-1 flex justify-between text-xs font-semibold">
                        <span>{label}</span>
                        <span className="text-primary">+{val} <span className="font-normal text-secondary">/ {max}</span></span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-surface-container">
                        <div
                          className="h-full rounded-full bg-primary transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </BentoCard>

            {/* Recommended Action */}
            <BentoCard>
              <p className="mb-2 text-xs font-bold uppercase tracking-widest text-primary">AI Recommended Action</p>
              <p className="text-sm font-semibold leading-relaxed">{selected.insight.recommended_action}</p>
              <div className="mt-4 rounded-lg bg-surface-low p-3 text-xs leading-relaxed text-secondary">
                {selected.insight.reasoning}
              </div>
              <div className="mt-4 flex items-center justify-between text-xs text-secondary">
                <span>Target: <strong className="text-charcoal">{selected.insight.target_segment}</strong></span>
                <span>Confidence: <strong className="text-primary">{Math.round(selected.insight.confidence * 100)}%</strong></span>
              </div>
            </BentoCard>
          </>
        )}
      </div>
    </section>
  );
}
