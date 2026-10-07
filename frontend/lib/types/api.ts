export interface SinglePredictionRequest {
  load_id?: string;
  pickup: string;
  delivery: string;
  pickup_lat: number;
  pickup_lon: number;
  delivery_lat: number;
  delivery_lon: number;
  distance: number;
  equipment: string;
  weight: number;
  market_index?: number;
  quote_signal?: number;
  date: string;
}

export interface BatchPredictionRequest {
  loads: SinglePredictionRequest[];
}

export interface ConfidenceInterval {
  lower: number;
  upper: number;
}

export interface SinglePredictionResponse {
  id?: number;
  request_id?: string;
  load_id?: string;
  predicted_rate: number;
  rate_per_mile: number;
  currency: string;
  base_signal: number;
  residual: number;
  confidence_interval: ConfidenceInterval;
  model_version: string;
  prediction_timestamp: string;
}

export interface BatchPredictionResponse {
  count: number;
  predictions: SinglePredictionResponse[];
}

export interface PredictionDetailResponse {
  id: number;
  request_id: string;
  load_id?: string;
  predicted_rate: number;
  rate_per_mile: number;
  base_signal?: number;
  residual?: number;
  confidence_interval: ConfidenceInterval;
  model_version: string;
  prediction_timestamp: string;
  input_data?: Record<string, unknown>;
}

export interface PredictionListResponse {
  total: number;
  limit: number;
  offset: number;
  items: PredictionDetailResponse[];
}

export interface HealthResponse {
  status: string;
  service: string;
  model_loaded: boolean;
  database_connected: boolean;
  timestamp: string;
}

export interface ModelInfoResponse {
  model_version: string;
  created_at: string;
  random_seed: number;
  target_strategy: string;
  ensemble_weights: Record<string, number>;
  feature_count: number;
  feature_names: string[];
  metrics: Record<string, unknown>;
  database_metadata?: Record<string, unknown>;
}

export interface DriftMetricItem {
  id: number;
  run_id: string;
  timestamp: string;
  feature_name: string;
  metric_type: string;
  metric_value: number;
  threshold_warning: number;
  threshold_critical: number;
  status: string;
}

export interface DataQualityMetricItem {
  id: number;
  run_id: string;
  timestamp: string;
  feature_name: string;
  total_records: number;
  missing_count: number;
  missing_pct: number;
  invalid_count: number;
  invalid_pct: number;
  status: string;
}

export interface PerformanceMetricItem {
  id: number;
  run_id: string;
  timestamp: string;
  model_version: string;
  sample_size: number;
  rmse: number;
  mae: number;
  mape: number;
  r2: number;
  residual_mean?: number;
  residual_std?: number;
  segment_name: string;
  segment_value: string;
}

export interface MonitoringSummaryResponse {
  status: string;
  total_predictions: number;
  total_actual_outcomes: number;
  last_run?: {
    run_id: string;
    timestamp: string;
    prediction_count: number;
    data_quality_status: string;
    drift_status: string;
    performance_status: string;
    alert_count: number;
    details?: Record<string, unknown>;
  };
}

export interface APIErrorDetail {
  loc?: (string | number)[];
  msg: string;
  type?: string;
}

export interface APIErrorResponse {
  detail?: string | APIErrorDetail[];
  error_code?: string;
  message?: string;
}
