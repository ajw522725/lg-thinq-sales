export type Sentiment = "positive" | "neutral" | "negative";
export type Intent = "high" | "medium" | "low";
export type Urgency = "critical" | "medium" | "low";
export type Priority = "high" | "medium" | "low";

export interface ProcessedDocument {
  id: string;
  source: string;
  title: string;
  normalized_text: string;
  product_category: string;
  competitor_mentions: string[];
  keywords: string[];
  region?: string | null;
  published_at: string;
  url: string;
}

export interface NLPResult {
  sentiment_label: Sentiment;
  sentiment_score: number;
  intent_label: Intent;
  purchase_intent_score: number;
  urgency_label: Urgency;
  urgency_score: number;
  complaint_type?: string | null;
  topic_label: string;
  confidence: number;
}

export interface LeadScore {
  id: string;
  lead_score: number;
  priority: Priority;
  score_reason: Record<string, number>;
}

export interface StrategyInsight {
  id: string;
  voc_id: string;
  lead_score_id: string;
  title: string;
  summary: string;
  recommended_action: string;
  reasoning: string;
  priority: Priority;
  target_segment: string;
  confidence: number;
  created_at: string;
}

export interface ContextMatch {
  context_type: string;
  region: string;
  match_reason: string;
  match_score: number;
}

export interface VocRecord {
  voc: ProcessedDocument;
  analysis: NLPResult;
  lead_score: LeadScore;
  insight: StrategyInsight;
  context: ContextMatch;
}

export interface DashboardSummary {
  total_voc_collected: number;
  high_priority_leads: number;
  negative_voc_rate: number;
  purchase_intent_detected: number;
  average_lead_score: number;
  sentiment_breakdown: Record<string, number>;
  urgency_breakdown: Record<string, number>;
  platform_distribution: Record<string, number>;
  top_keywords: string[];
  topic_clusters: Array<{ topic: string; count: number; status: string }>;
  high_priority_preview: VocRecord[];
  featured_insight: StrategyInsight | null;
}

export interface CollectionRunRequest {
  keywords: string[];
  sources: string[];
  max_per_source: number;
  live: boolean;
  reset: boolean;
  save: boolean;
}

export interface CollectionRunResponse {
  seeded: boolean;
  raw_documents: number;
  processed_documents: number;
  insights: number;
  mode: "demo" | "live";
  keywords: string[];
  sources: string[];
  collector_raw: number;
  ingestion_payload: number;
  source_stats: Record<string, number>;
}
