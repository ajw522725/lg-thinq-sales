import type { CollectionRunRequest, CollectionRunResponse, DashboardSummary, StrategyInsight, VocRecord } from "@/types/api";
import { DEMO_DASHBOARD_SUMMARY, DEMO_INSIGHTS, DEMO_VOC_RECORDS } from "./demo-data";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function apiGet<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    if (!response.ok) throw new Error(`API ${path} ${response.status}`);
    return response.json() as Promise<T>;
  } catch {
    return fallback;
  }
}

async function apiPost<TResponse, TPayload>(path: string, payload: TPayload): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`API ${path} ${response.status}`);
  }
  return response.json() as Promise<TResponse>;
}

export function getDashboardSummary() {
  return apiGet<DashboardSummary>("/api/v1/dashboard/summary", DEMO_DASHBOARD_SUMMARY);
}

export function getVocs() {
  return apiGet<VocRecord[]>("/api/v1/vocs", DEMO_VOC_RECORDS);
}

export function getLeadScores() {
  return apiGet<VocRecord[]>("/api/v1/lead-scores", DEMO_VOC_RECORDS);
}

export function getInsights() {
  return apiGet<StrategyInsight[]>("/api/v1/insights", DEMO_INSIGHTS);
}

export function runCollection(payload: CollectionRunRequest) {
  return apiPost<CollectionRunResponse, CollectionRunRequest>("/api/v1/collection/run", payload);
}
