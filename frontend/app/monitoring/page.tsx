"use client";

import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Skeleton } from "../../components/ui/Skeleton";
import { Alert } from "../../components/ui/Alert";
import {
  Activity,
  ShieldCheck,
  RefreshCw,
  BarChart3,
  Layers,
  Database,
  Play,
  ArrowUpRight,
  RotateCcw
} from "lucide-react";

import {
  getMonitoringSummary,
  getDriftMetrics,
  getDataQualityMetrics,
  getPerformanceMetrics,
  triggerMonitoringRun,
  promoteModel,
  rollbackModel
} from "../../lib/api/monitoring";

import { getModelInfo } from "../../lib/api/models";

import {
  MonitoringSummaryResponse,
  DriftMetricItem,
  DataQualityMetricItem,
  PerformanceMetricItem,
  ModelInfoResponse
} from "../../lib/types/api";

import { formatDateTime } from "../../lib/utils/formatters";

export default function MonitoringPage() {
  const [summary, setSummary] = useState<MonitoringSummaryResponse | null>(null);
  const [driftItems, setDriftItems] = useState<DriftMetricItem[]>([]);
  const [qualityItems, setQualityItems] = useState<DataQualityMetricItem[]>([]);
  const [performanceItems, setPerformanceItems] = useState<PerformanceMetricItem[]>([]);
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchTelemetryData = async () => {
    try {
      const [sumRes, driftRes, qualRes, perfRes, modelRes] = await Promise.allSettled([
        getMonitoringSummary(),
        getDriftMetrics(),
        getDataQualityMetrics(),
        getPerformanceMetrics(),
        getModelInfo(),
      ]);

      if (sumRes.status === "fulfilled") setSummary(sumRes.value);
      if (driftRes.status === "fulfilled") setDriftItems(driftRes.value.items || []);
      if (qualRes.status === "fulfilled") setQualityItems(qualRes.value.items || []);
      if (perfRes.status === "fulfilled") setPerformanceItems(perfRes.value.items || []);
      if (modelRes.status === "fulfilled") setModelInfo(modelRes.value);
      setError(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Failed to fetch monitoring telemetry.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    const init = async () => {
      try {
        const [sumRes, driftRes, qualRes, perfRes, modelRes] = await Promise.allSettled([
          getMonitoringSummary(),
          getDriftMetrics(),
          getDataQualityMetrics(),
          getPerformanceMetrics(),
          getModelInfo(),
        ]);

        if (isMounted) {
          if (sumRes.status === "fulfilled") setSummary(sumRes.value);
          if (driftRes.status === "fulfilled") setDriftItems(driftRes.value.items || []);
          if (qualRes.status === "fulfilled") setQualityItems(qualRes.value.items || []);
          if (perfRes.status === "fulfilled") setPerformanceItems(perfRes.value.items || []);
          if (modelRes.status === "fulfilled") setModelInfo(modelRes.value);
          setLoading(false);
        }
      } catch {
        if (isMounted) {
          setLoading(false);
        }
      }
    };
    init();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleTriggerRun = async () => {
    try {
      setActionLoading(true);
      setError(null);
      setSuccessMsg(null);
      await triggerMonitoringRun();
      setSuccessMsg("Monitoring cycle executed successfully.");
      await fetchTelemetryData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Failed to trigger monitoring cycle.");
    } finally {
      setActionLoading(false);
    }
  };

  const handlePromote = async (version: string) => {
    try {
      setActionLoading(true);
      setError(null);
      setSuccessMsg(null);
      await promoteModel(version, true);
      setSuccessMsg(`Model '${version}' promoted to active production.`);
      await fetchTelemetryData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || `Failed to promote model '${version}'.`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRollback = async (version: string) => {
    try {
      setActionLoading(true);
      setError(null);
      setSuccessMsg(null);
      await rollbackModel(version);
      setSuccessMsg(`Production model rolled back to '${version}'.`);
      await fetchTelemetryData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || `Failed to rollback to '${version}'.`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const lastRun = summary?.last_run;
  const activeVersion = modelInfo?.model_version || "freight-rate-v1.0.0";

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Activity className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            MLOps Production Monitoring & Governance
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time feature drift detection, data quality metrics, and delayed actual performance audit.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchTelemetryData} leftIcon={<RefreshCw className="h-4 w-4" />}>
            Refresh Telemetry
          </Button>
          <Button size="sm" onClick={handleTriggerRun} isLoading={actionLoading} leftIcon={<Play className="h-4 w-4" />}>
            Run Monitoring Cycle
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="error" title="Monitoring Alert">
          {error}
        </Alert>
      )}

      {successMsg && (
        <Alert variant="success" title="Action Completed">
          {successMsg}
        </Alert>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Production Model</span>
            <div className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-1 flex items-center gap-1.5 font-mono">
              <ShieldCheck className="h-5 w-5 text-emerald-500" />
              <span>{activeVersion}</span>
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Status: ACTIVE PRODUCTION</span>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Predictions Logged</span>
            <div className="text-2xl font-extrabold text-blue-600 dark:text-blue-400 mt-1 font-mono">
              {summary?.total_predictions ?? 0}
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Inference audit trail count</span>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Matched Actual Outcomes</span>
            <div className="text-2xl font-extrabold text-purple-600 dark:text-purple-400 mt-1 font-mono">
              {summary?.total_actual_outcomes ?? 0}
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Delayed actual posted rates</span>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Monitoring Alert Status</span>
            <div className="mt-1 flex items-center gap-2">
              <Badge variant={lastRun?.alert_count ? "warning" : "success"} size="md">
                {lastRun?.alert_count ? `${lastRun.alert_count} Alerts Triggered` : "All Systems Normal"}
              </Badge>
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">
              Last Run: {lastRun?.timestamp ? formatDateTime(lastRun.timestamp) : "None"}
            </span>
          </CardContent>
        </Card>
      </div>

      {/* Feature Drift Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Layers className="h-5 w-5 text-blue-500" />
            Feature Distribution Drift (PSI & KS Test)
          </CardTitle>
          <CardDescription>
            Statistical comparison between baseline training reference and live prediction input distribution.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {driftItems.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-200 p-6 text-center text-xs text-slate-500 dark:border-slate-800">
              No drift monitoring data available. Click &quot;Run Monitoring Cycle&quot; to execute check.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 dark:bg-slate-800 font-semibold text-slate-700 dark:text-slate-300">
                  <tr>
                    <th className="p-3">Feature</th>
                    <th className="p-3">Metric Type</th>
                    <th className="p-3">PSI Value</th>
                    <th className="p-3">Warning Threshold</th>
                    <th className="p-3">Critical Threshold</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
                  {driftItems.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                      <td className="p-3 font-semibold text-slate-900 dark:text-slate-100">{item.feature_name}</td>
                      <td className="p-3 text-slate-600 dark:text-slate-400">{item.metric_type}</td>
                      <td className="p-3 font-bold text-blue-600 dark:text-blue-400">{item.metric_value.toFixed(4)}</td>
                      <td className="p-3 text-slate-500">{item.threshold_warning}</td>
                      <td className="p-3 text-slate-500">{item.threshold_critical}</td>
                      <td className="p-3 font-sans">
                        <Badge variant={item.status === "CRITICAL" ? "error" : item.status === "WARNING" ? "warning" : "success"}>
                          {item.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Data Quality Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Database className="h-5 w-5 text-blue-500" />
            Input Data Quality & Sanity Audit
          </CardTitle>
          <CardDescription>
            Audit log of missing values, invalid bounds, and unexpected categorical values across input records.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {qualityItems.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-200 p-6 text-center text-xs text-slate-500 dark:border-slate-800">
              No data quality audit records available.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 dark:bg-slate-800 font-semibold text-slate-700 dark:text-slate-300">
                  <tr>
                    <th className="p-3">Feature</th>
                    <th className="p-3">Total Evaluated</th>
                    <th className="p-3">Missing Count (%)</th>
                    <th className="p-3">Invalid Count (%)</th>
                    <th className="p-3">Quality Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
                  {qualityItems.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                      <td className="p-3 font-semibold text-slate-900 dark:text-slate-100">{item.feature_name}</td>
                      <td className="p-3 text-slate-600 dark:text-slate-400">{item.total_records}</td>
                      <td className="p-3 text-slate-700 dark:text-slate-300">
                        {item.missing_count} ({item.missing_pct}%)
                      </td>
                      <td className="p-3 text-slate-700 dark:text-slate-300">
                        {item.invalid_count} ({item.invalid_pct}%)
                      </td>
                      <td className="p-3 font-sans">
                        <Badge variant={item.status === "CRITICAL" ? "error" : item.status === "WARNING" ? "warning" : "success"}>
                          {item.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delayed Model Performance Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BarChart3 className="h-5 w-5 text-blue-500" />
            Delayed Model Evaluation (Actual Posted Rates Matched)
          </CardTitle>
          <CardDescription>
            True accuracy evaluation calculated by comparing stored predictions against actual load outcomes.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {performanceItems.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-200 p-6 text-center text-xs text-slate-500 dark:border-slate-800">
              No delayed outcome evaluation data available. Ingest actual posted rates to view accuracy metrics.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 dark:bg-slate-800 font-semibold text-slate-700 dark:text-slate-300">
                  <tr>
                    <th className="p-3">Model Version</th>
                    <th className="p-3">Segment</th>
                    <th className="p-3">Sample Size</th>
                    <th className="p-3">RMSE</th>
                    <th className="p-3">MAE</th>
                    <th className="p-3">MAPE (%)</th>
                    <th className="p-3">R² Score</th>
                    <th className="p-3">Residual Mean / Std</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
                  {performanceItems.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                      <td className="p-3 font-semibold text-slate-900 dark:text-slate-100">{item.model_version}</td>
                      <td className="p-3 text-slate-600 dark:text-slate-400 capitalize">
                        {item.segment_name}: {item.segment_value}
                      </td>
                      <td className="p-3 text-slate-600 dark:text-slate-400">{item.sample_size}</td>
                      <td className="p-3 font-bold text-blue-600 dark:text-blue-400">${item.rmse.toFixed(2)}</td>
                      <td className="p-3 font-semibold text-slate-800 dark:text-slate-200">${item.mae.toFixed(2)}</td>
                      <td className="p-3 font-semibold text-slate-800 dark:text-slate-200">{item.mape.toFixed(2)}%</td>
                      <td className="p-3 font-semibold text-slate-800 dark:text-slate-200">{item.r2.toFixed(4)}</td>
                      <td className="p-3 text-slate-500">
                        ${item.residual_mean?.toFixed(2)} / ${item.residual_std?.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Model Lifecycle & Promotion Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldCheck className="h-5 w-5 text-blue-500" />
            Model Registry & Promotion Control Gate
          </CardTitle>
          <CardDescription>
            Controlled promotion gate and rollback options for active production model artifacts.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg bg-slate-50 p-4 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800">
            <div>
              <span className="text-xs text-slate-500 font-medium block">Active Production Model</span>
              <span className="text-base font-bold font-mono text-slate-900 dark:text-slate-100">{activeVersion}</span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleRollback(activeVersion)}
                isLoading={actionLoading}
                leftIcon={<RotateCcw className="h-4 w-4" />}
              >
                Rollback to {activeVersion}
              </Button>
              <Button
                size="sm"
                onClick={() => handlePromote(activeVersion)}
                isLoading={actionLoading}
                leftIcon={<ArrowUpRight className="h-4 w-4" />}
              >
                Promote Candidate
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
