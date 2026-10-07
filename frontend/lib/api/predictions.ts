import { fetchAPI } from "./client";
import {
  SinglePredictionRequest,
  SinglePredictionResponse,
  BatchPredictionRequest,
  BatchPredictionResponse,
  PredictionListResponse,
  PredictionDetailResponse,
} from "../types/api";

export async function predictSingle(request: SinglePredictionRequest): Promise<SinglePredictionResponse> {
  return fetchAPI<SinglePredictionResponse>("/api/v1/predict", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function predictBatch(request: BatchPredictionRequest): Promise<BatchPredictionResponse> {
  return fetchAPI<BatchPredictionResponse>("/api/v1/predict/batch", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export interface ListPredictionsParams {
  load_id?: string;
  model_version?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export async function listPredictions(params: ListPredictionsParams = {}): Promise<PredictionListResponse> {
  const query = new URLSearchParams();
  if (params.load_id) query.append("load_id", params.load_id);
  if (params.model_version) query.append("model_version", params.model_version);
  if (params.start_date) query.append("start_date", params.start_date);
  if (params.end_date) query.append("end_date", params.end_date);
  if (params.limit !== undefined) query.append("limit", params.limit.toString());
  if (params.offset !== undefined) query.append("offset", params.offset.toString());

  const queryString = query.toString();
  const endpoint = `/api/v1/predictions${queryString ? `?${queryString}` : ""}`;
  return fetchAPI<PredictionListResponse>(endpoint, { method: "GET" });
}

export async function getPredictionById(predictionId: number): Promise<PredictionDetailResponse> {
  return fetchAPI<PredictionDetailResponse>(`/api/v1/predictions/${predictionId}`, {
    method: "GET",
  });
}
