"use client";

import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Skeleton } from "../ui/Skeleton";
import { Alert } from "../ui/Alert";
import { Cpu, ShieldCheck, Layers, BarChart3, Database } from "lucide-react";
import { getModelInfo } from "../../lib/api/models";
import { ModelInfoResponse } from "../../lib/types/api";

export function ModelInfoView() {
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError(null);
        const info = await getModelInfo();
        setModelInfo(info);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        setError(message || "Failed to load model metadata.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (error || !modelInfo) {
    return (
      <Alert variant="error" title="Model Information Unavailable">
        {error || "No model metadata returned by service."}
      </Alert>
    );
  }

  const weights = modelInfo.ensemble_weights || {};
  const metrics = modelInfo.metrics || {};
  const dbMeta = modelInfo.database_metadata;

  return (
    <div className="space-y-6">
      {/* Active Model Overview */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white shadow-sm">
                <Cpu className="h-6 w-6" />
              </div>
              <div>
                <CardTitle>Production ML Model Ensemble</CardTitle>
                <CardDescription>
                  Active inference artifact loaded in service memory and registered in PostgreSQL.
                </CardDescription>
              </div>
            </div>
            <Badge variant="success" size="md" className="gap-1">
              <ShieldCheck className="h-3.5 w-3.5" /> Version: {modelInfo.model_version}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/50">
            <span className="text-xs text-slate-500 font-medium">Target Formulation</span>
            <div className="text-base font-semibold text-slate-900 dark:text-slate-100 mt-1 capitalize font-mono">
              {modelInfo.target_strategy}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/50">
            <span className="text-xs text-slate-500 font-medium">Engineered Feature Count</span>
            <div className="text-base font-semibold text-slate-900 dark:text-slate-100 mt-1 font-mono">
              {modelInfo.feature_count} Columns
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/50">
            <span className="text-xs text-slate-500 font-medium">Training Seed</span>
            <div className="text-base font-semibold text-slate-900 dark:text-slate-100 mt-1 font-mono">
              Seed {modelInfo.random_seed}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/50">
            <span className="text-xs text-slate-500 font-medium">Training Date</span>
            <div className="text-xs font-semibold text-slate-900 dark:text-slate-100 mt-1 font-mono">
              {modelInfo.created_at ? new Date(modelInfo.created_at).toLocaleString() : "N/A"}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Ensemble Weights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Layers className="h-4 w-4 text-blue-500" />
            Ensemble Model Component Weights
          </CardTitle>
          <CardDescription>
            Weighted blend computed from Out-of-Time validation optimization.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {Object.entries(weights).map(([modelKey, weightVal]) => {
            const pct = (Number(weightVal) * 100).toFixed(1);
            return (
              <div key={modelKey} className="space-y-1.5">
                <div className="flex justify-between text-sm font-medium">
                  <span className="capitalize text-slate-800 dark:text-slate-200">{modelKey}</span>
                  <span className="font-mono text-blue-600 dark:text-blue-400 font-bold">{pct}%</span>
                </div>
                <div className="h-2.5 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-blue-600 transition-all duration-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* Validation Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BarChart3 className="h-4 w-4 text-blue-500" />
            Out-of-Time (OOT) Validation Performance Metrics
          </CardTitle>
          <CardDescription>
            Evaluation metrics computed on untouched holdout validation loads.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(metrics).map(([metricKey, metricValue]) => (
            <div key={metricKey} className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
              <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">{metricKey}</span>
              <div className="text-xl font-extrabold text-slate-900 dark:text-slate-100 mt-1 font-mono">
                {typeof metricValue === "number" ? metricValue.toFixed(4) : String(metricValue)}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Database Metadata */}
      {dbMeta && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Database className="h-4 w-4 text-blue-500" />
              PostgreSQL Model Version Trace
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs space-y-2 font-mono bg-slate-50 p-4 rounded-lg dark:bg-slate-900/40">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <div>DB Record ID: #{String(dbMeta.id ?? "N/A")}</div>
              <div>Version String: {String(dbMeta.version ?? "N/A")}</div>
              <div>Training Period: {String(dbMeta.training_period ?? "2025-01 to 2025-11")}</div>
              <div>Status: {dbMeta.is_active ? "ACTIVE PRODUCTION" : "INACTIVE"}</div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
