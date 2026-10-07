import { fetchAPI } from "./client";
import { HealthResponse } from "../types/api";

export async function getHealth(): Promise<HealthResponse> {
  return fetchAPI<HealthResponse>("/health", {
    method: "GET",
  });
}

export async function getReady(): Promise<{ status: string; service: string; model_version: string; database_connected: boolean }> {
  return fetchAPI<{ status: string; service: string; model_version: string; database_connected: boolean }>("/ready", {
    method: "GET",
  });
}
