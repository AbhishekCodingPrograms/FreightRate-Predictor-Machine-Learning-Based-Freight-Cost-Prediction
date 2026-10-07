import { fetchAPI } from "./client";
import { ModelInfoResponse } from "../types/api";

export async function getModelInfo(): Promise<ModelInfoResponse> {
  return fetchAPI<ModelInfoResponse>("/api/v1/model/info", {
    method: "GET",
  });
}
