"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../ui/Card";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { Skeleton } from "../ui/Skeleton";
import { Alert } from "../ui/Alert";
import {
  UploadCloud,
  History,
  Cpu,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";
import { getHealth } from "../../lib/api/health";
import { getModelInfo } from "../../lib/api/models";
import { listPredictions } from "../../lib/api/predictions";
import { HealthResponse, ModelInfoResponse, PredictionListResponse } from "../../lib/types/api";
import { formatCurrency, formatDateTime } from "../../lib/utils/formatters";

export function DashboardOverview() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);
  const [recent, setRecent] = useState<PredictionListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError(null);

        const [healthRes, modelRes, recentRes] = await Promise.allSettled([
          getHealth(),
          getModelInfo(),
          listPredictions({ limit: 5 }),
        ]);

        if (healthRes.status === "fulfilled") setHealth(healthRes.value);
        if (modelRes.status === "fulfilled") setModelInfo(modelRes.value);
        if (recentRes.status === "fulfilled") setRecent(recentRes.value);

        if (healthRes.status === "rejected" && modelRes.status === "rejected" && recentRes.status === "rejected") {
          setError("Unable to connect to FreightRate Predictor service. Ensure FastAPI backend is running.");
        }
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        setError(message || "Failed to load dashboard data.");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-blue-700 via-blue-600 to-indigo-700 p-6 sm:p-8 text-white shadow-lg">
        <div className="max-w-3xl space-y-3">
          <Badge variant="info" className="bg-white/20 text-white ring-white/30 backdrop-blur-xs">
            Machine Learning Powered Spot Rates
          </Badge>
          <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
            Spot Freight Rate Cost Predictor
          </h2>
          <p className="text-sm sm:text-base text-blue-100 leading-relaxed">
            Estimate spot freight rates (`posted_rate`) using an out-of-time benchmarked residual ensemble combining LightGBM, CatBoost, and XGBoost models.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/predict">
              <Button size="md" className="bg-white text-blue-700 hover:bg-blue-50 font-semibold shadow-md">
                Calculate Single Spot Rate <ArrowRight className="ml-1.5 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/batch">
              <Button size="md" variant="outline" className="border-white/40 text-white hover:bg-white/10">
                Upload Batch CSV <UploadCloud className="ml-1.5 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {error && (
        <Alert variant="error" title="Backend Connection Issue">
          {error}
        </Alert>
      )}

      {/* Operational Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* System Health */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider flex items-center justify-between">
              <span>Service Health & Database</span>
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {loading ? (
              <Skeleton className="h-12 w-full" />
            ) : health ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600 dark:text-slate-400">FastAPI ML Service</span>
                  <Badge variant={health.model_loaded ? "success" : "error"}>
                    {health.model_loaded ? "Model Active" : "Unloaded"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600 dark:text-slate-400">PostgreSQL Database</span>
                  <Badge variant={health.database_connected ? "success" : "warning"}>
                    {health.database_connected ? "Connected" : "Offline"}
                  </Badge>
                </div>
              </>
            ) : (
              <p className="text-xs text-slate-400">Status unavailable</p>
            )}
          </CardContent>
        </Card>

        {/* Model Info */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider flex items-center justify-between">
              <span>Active Model Version</span>
              <Cpu className="h-4 w-4 text-blue-500" />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {loading ? (
              <Skeleton className="h-12 w-full" />
            ) : modelInfo ? (
              <>
                <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 font-mono">
                  {modelInfo.model_version}
                </div>
                <p className="text-xs text-slate-500">
                  Target: <span className="font-semibold capitalize text-slate-700 dark:text-slate-300">{modelInfo.target_strategy}</span> • {modelInfo.feature_count} Features
                </p>
              </>
            ) : (
              <p className="text-xs text-slate-400">Model metadata unavailable</p>
            )}
          </CardContent>
        </Card>

        {/* History Log Count */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider flex items-center justify-between">
              <span>Persisted Audit Records</span>
              <History className="h-4 w-4 text-indigo-500" />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {loading ? (
              <Skeleton className="h-12 w-full" />
            ) : recent ? (
              <>
                <div className="text-3xl font-extrabold text-slate-900 dark:text-slate-100">
                  {recent.total}
                </div>
                <p className="text-xs text-slate-500">
                  Total prediction requests logged in database
                </p>
              </>
            ) : (
              <p className="text-xs text-slate-400">No predictions recorded yet</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Predictions Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <History className="h-4 w-4 text-blue-500" /> Recent Spot Rate Predictions
              </CardTitle>
              <CardDescription>Latest prediction logs from database audit trail</CardDescription>
            </div>
            <Link href="/history">
              <Button variant="ghost" size="sm">
                View All History <ArrowRight className="ml-1 h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          )}

          {!loading && recent && recent.items.length === 0 && (
            <div className="p-6 text-center text-sm text-slate-500">
              No predictions recorded yet. Run a single or batch prediction to see records here.
            </div>
          )}

          {!loading && recent && recent.items.length > 0 && (
            <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 dark:bg-slate-800 font-semibold text-slate-700 dark:text-slate-300">
                  <tr>
                    <th className="p-3">ID</th>
                    <th className="p-3">Load ID</th>
                    <th className="p-3">Predicted Rate</th>
                    <th className="p-3">Rate / Mile</th>
                    <th className="p-3">Model</th>
                    <th className="p-3">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {recent.items.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                      <td className="p-3 font-mono text-slate-400">#{item.id}</td>
                      <td className="p-3 font-semibold text-slate-900 dark:text-slate-100 font-mono">
                        {item.load_id || "N/A"}
                      </td>
                      <td className="p-3 font-bold text-blue-600 dark:text-blue-400">
                        {formatCurrency(item.predicted_rate)}
                      </td>
                      <td className="p-3 text-slate-700 dark:text-slate-300">
                        {formatCurrency(item.rate_per_mile)} / mi
                      </td>
                      <td className="p-3 font-mono text-slate-500">{item.model_version}</td>
                      <td className="p-3 text-slate-400">{formatDateTime(item.prediction_timestamp)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
