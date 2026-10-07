import { APIErrorResponse } from "../types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class APIClientError extends Error {
  status: number;
  errorCode?: string;
  details?: unknown;

  constructor(message: string, status: number, errorCode?: string, details?: unknown) {
    super(message);
    this.name = "APIClientError";
    this.status = status;
    this.errorCode = errorCode;
    this.details = details;
  }
}

export async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body && typeof options.body === "string") {
    headers.set("Content-Type", "application/json");
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
      let errorCode = "API_ERROR";
      let details: unknown = null;

      try {
        const errorJson: APIErrorResponse = await response.json();
        details = errorJson;
        errorCode = errorJson.error_code || `HTTP_${response.status}`;

        if (typeof errorJson.detail === "string") {
          errorMsg = errorJson.detail;
        } else if (Array.isArray(errorJson.detail)) {
          errorMsg = errorJson.detail.map((d) => d.msg).join(", ");
        } else if (errorJson.message) {
          errorMsg = errorJson.message;
        }
      } catch {
        // Raw non-JSON response error
      }

      throw new APIClientError(errorMsg, response.status, errorCode, details);
    }

    return (await response.json()) as T;
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    if (err instanceof APIClientError) {
      throw err;
    }
    if (err instanceof Error && err.name === "AbortError") {
      throw new APIClientError("Request timed out after 30 seconds.", 408, "TIMEOUT");
    }
    const message = err instanceof Error ? err.message : "Failed to communicate with prediction service.";
    throw new APIClientError(message, 0, "NETWORK_ERROR");
  }
}
