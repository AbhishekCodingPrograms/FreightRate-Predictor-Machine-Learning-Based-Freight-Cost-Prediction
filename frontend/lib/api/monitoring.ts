import { fetchAPI } from "./client";
import {
  MonitoringSummaryResponse,
  DriftMetricItem,
  DataQualityMetricItem,
  PerformanceMetricItem,
} from "../types/api";

export async function getMonitoringSummary(): Promise<MonitoringSummaryResponse> {
  return fetchAPI<MonitoringSummaryResponse>("/monitoring/summary");
}

export async function getDriftMetrics(): Promise<{ total: number; items: DriftMetricItem[] }> {
  return fetchAPI<{ total: number; items: DriftMetricItem[] }>("/monitoring/drift");
}

export async function getDataQualityMetrics(): Promise<{ total: number; items: DataQualityMetricItem[] }> {
  return fetchAPI<{ total: number; items: DataQualityMetricItem[] }>("/monitoring/data-quality");
}

export async function getPerformanceMetrics(): Promise<{ total: number; items: PerformanceMetricItem[] }> {
  return fetchAPI<{ total: number; items: PerformanceMetricItem[] }>("/monitoring/performance");
}

export async function triggerMonitoringRun(): Promise<Record<string, unknown>> {
  return fetchAPI<Record<string, unknown>>("/monitoring/run", { method: "POST" });
}

export async function promoteModel(version: string, force = false): Promise<Record<string, unknown>> {
  return fetchAPI<Record<string, unknown>>("/models/promote", {
    method: "POST",
    body: JSON.stringify({ version, force }),
  });
}

export async function rollbackModel(version: string): Promise<Record<string, unknown>> {
  return fetchAPI<Record<string, unknown>>("/models/rollback", {
    method: "POST",
    body: JSON.stringify({ version }),
  });
}
