"use client";

import { useState } from "react";

interface PipelineResult {
  voc_id: string;
  source: string;
  product_category: string;
  nlp: {
    sentiment_label: string;
    sentiment_score: number;
    intent_label: string;
    purchase_intent_score: number;
    urgency_score: number;
    topic_label: string;
    keywords: string[];
    competitor_comparison_flag: boolean;
  };
  score: {
    lead_score: number;
    priority: string;
    score_reason: Record<string, unknown>;
  };
  insight: {
    title: string;
    summary: string;
    recommended_action: string;
    reasoning: string;
    confidence: number;
  };
  processing_time_ms: number;
}

const SOURCES = ["Danawa", "Reddit", "Naver Blog", "YouTube", "X/Twitter", "unknown"];
const CATEGORIES = [
  { value: "air_purifier",    label: "공기청정기" },
  { value: "air_conditioner", label: "에어컨" },
  { value: "refrigerator",    label: "냉장고" },
  { value: "washing_machine", label: "세탁기" },
  { value: "lg_styler",       label: "LG 스타일러" },
  { value: "subscription_care", label: "구독 케어" },
  { value: "general",         label: "기타" },
];

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function NewAnalysisModal({ onClose }: { onClose: () => void }) {
  const [text, setText] = useState("");
  const [source, setSource] = useState("unknown");
  const [category, setCategory] = useState("general");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [error, setError] = useState("");

  async function handleSubmit() {
    if (text.trim().length < 5) { setError("VOC 텍스트를 5자 이상 입력하세요."); return; }
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/pipeline/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, source, product_category: category, engagement: 0 }),
      });
      if (!res.ok) throw new Error(`API 오류 ${res.status}`);
      setResult(await res.json());
    } catch (e) {
      setError("백엔드에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.");
    } finally {
      setLoading(false);
    }
  }

  function reset() { setResult(null); setText(""); setError(""); }

  const priorityColor = result?.score.priority === "high"
    ? "text-error bg-red-50 border-red-200"
    : result?.score.priority === "medium"
    ? "text-amber-700 bg-amber-50 border-amber-200"
    : "text-emerald-700 bg-emerald-50 border-emerald-200";

  const sentimentIcon = result?.nlp.sentiment_label === "positive" ? "😊"
    : result?.nlp.sentiment_label === "negative" ? "😟" : "😐";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-charcoal/40 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="relative w-full max-w-xl rounded-2xl bg-white shadow-2xl shadow-black/20 mx-4">
        {/* 헤더 */}
        <div className="flex items-center justify-between border-b border-surface-high px-6 py-4">
          <div>
            <h2 className="text-base font-bold text-charcoal">New Analysis</h2>
            <p className="text-xs text-secondary mt-0.5">VOC 텍스트를 입력하면 AI가 즉시 분석합니다</p>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-secondary hover:bg-surface-low hover:text-charcoal transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="p-6">
          {!result ? (
            /* 입력 폼 */
            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-semibold uppercase tracking-widest text-secondary">
                  VOC 텍스트
                </label>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="고객 리뷰, SNS 게시물, 문의 내용 등을 붙여넣으세요..."
                  rows={4}
                  className="w-full resize-none rounded-xl border border-surface-high bg-surface-low px-4 py-3 text-sm text-charcoal placeholder:text-secondary/60 outline-none focus:border-primary/40 focus:ring-2 focus:ring-primary/10 transition-all"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1.5 block text-xs font-semibold uppercase tracking-widest text-secondary">플랫폼</label>
                  <select
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    className="w-full rounded-xl border border-surface-high bg-surface-low px-3 py-2.5 text-sm text-charcoal outline-none focus:border-primary/40 focus:ring-2 focus:ring-primary/10 transition-all"
                  >
                    {SOURCES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-semibold uppercase tracking-widest text-secondary">제품군</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full rounded-xl border border-surface-high bg-surface-low px-3 py-2.5 text-sm text-charcoal outline-none focus:border-primary/40 focus:ring-2 focus:ring-primary/10 transition-all"
                  >
                    {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>
              </div>

              {error && (
                <p className="rounded-lg bg-red-50 border border-red-200 px-4 py-2.5 text-xs font-medium text-error">{error}</p>
              )}

              <button
                onClick={handleSubmit}
                disabled={loading || text.trim().length < 5}
                className="w-full rounded-xl bg-primary py-3 text-sm font-bold text-white shadow-md shadow-primary/25 hover:bg-primary-strong disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="h-3.5 w-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                    분석 중...
                  </span>
                ) : "✦ AI 분석 실행"}
              </button>
            </div>
          ) : (
            /* 결과 */
            <div className="space-y-4">
              {/* 리드 점수 */}
              <div className="flex items-center gap-4 rounded-xl border border-surface-high bg-surface-low p-4">
                <div className="text-center">
                  <div className="text-4xl font-black text-primary tabular-nums">{result.score.lead_score}</div>
                  <div className="text-[10px] font-bold uppercase tracking-widest text-secondary">Lead Score</div>
                </div>
                <div className="flex-1 space-y-2">
                  <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-bold ${priorityColor}`}>
                    {result.score.priority.toUpperCase()} PRIORITY
                  </span>
                  <div className="flex gap-2 flex-wrap">
                    <span className="rounded-md bg-white border border-surface-high px-2 py-1 text-xs font-medium text-secondary">
                      {sentimentIcon} {result.nlp.sentiment_label}
                    </span>
                    <span className="rounded-md bg-white border border-surface-high px-2 py-1 text-xs font-medium text-secondary">
                      🎯 intent: {result.nlp.intent_label}
                    </span>
                    <span className="rounded-md bg-white border border-surface-high px-2 py-1 text-xs font-medium text-secondary">
                      📌 {result.nlp.topic_label}
                    </span>
                  </div>
                </div>
                <div className="text-right text-[10px] text-secondary">
                  {result.processing_time_ms.toFixed(0)}ms
                </div>
              </div>

              {/* 인사이트 */}
              <div className="rounded-xl border border-primary/15 bg-gradient-to-br from-white to-primary/[0.03] p-4">
                <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-primary">AI Insight</p>
                <p className="text-sm font-semibold leading-snug text-charcoal">{result.insight.title}</p>
                <p className="mt-2 text-xs leading-relaxed text-secondary">{result.insight.summary}</p>
              </div>

              {/* 권장 액션 */}
              <div className="rounded-xl bg-surface-low px-4 py-3">
                <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-secondary">Recommended Action</p>
                <p className="text-xs font-semibold leading-relaxed text-charcoal">{result.insight.recommended_action}</p>
              </div>

              {/* 키워드 */}
              {result.nlp.keywords.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {result.nlp.keywords.slice(0, 6).map((k) => (
                    <span key={k} className="rounded-full bg-surface-container px-2.5 py-1 text-[11px] font-medium text-secondary">
                      {k}
                    </span>
                  ))}
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={reset}
                  className="flex-1 rounded-xl border border-surface-high py-2.5 text-sm font-semibold text-secondary hover:bg-surface-low transition-colors"
                >
                  다시 분석
                </button>
                <button
                  onClick={onClose}
                  className="flex-1 rounded-xl bg-primary py-2.5 text-sm font-bold text-white hover:bg-primary-strong transition-colors"
                >
                  닫기
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
