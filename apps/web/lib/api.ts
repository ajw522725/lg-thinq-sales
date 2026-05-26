import type { DashboardSummary, StrategyInsight, VocRecord } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API request failed: ${path}`);
  }
  return response.json() as Promise<T>;
}

export function getDashboardSummary() {
  return apiGet<DashboardSummary>("/api/v1/dashboard/summary");
}

export function getVocs() {
  return apiGet<VocRecord[]>("/api/v1/vocs");
}

export function getLeadScores() {
  return apiGet<VocRecord[]>("/api/v1/lead-scores");
}

export function getInsights() {
  return apiGet<StrategyInsight[]>("/api/v1/insights");
}
