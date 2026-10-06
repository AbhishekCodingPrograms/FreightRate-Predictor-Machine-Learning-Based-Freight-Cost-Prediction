"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "../ui/Card";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { CheckCircle2, RotateCcw, Tag, ShieldCheck, Clock, Hash } from "lucide-react";
import { SinglePredictionResponse } from "../../lib/types/api";
import { formatCurrency, formatDateTime } from "../../lib/utils/formatters";

export interface PredictionResultCardProps {
  result: SinglePredictionResponse;
  onReset: () => void;
}

export function PredictionResultCard({ result, onReset }: PredictionResultCardProps) {
  return (
    <Card className="w-full border-blue-200 bg-gradient-to-b from-blue-50/40 to-white dark:border-blue-900/50 dark:from-slate-900 dark:to-slate-900 shadow-md">
      <CardHeader className="border-b border-blue-100 dark:border-slate-800 pb-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <div>
              <CardTitle className="text-xl">Prediction Generated Successfully</CardTitle>
              <CardDescription>
                Estimated total spot rate for Load ID: <span className="font-semibold text-slate-900 dark:text-slate-100">{result.load_id || "N/A"}</span>
              </CardDescription>
            </div>
          </div>
          <Badge variant="success" size="md" className="gap-1">
            <ShieldCheck className="h-3.5 w-3.5" /> Model Version: {result.model_version}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 pt-6">
        {/* Highlight Banner */}
        <div className="flex flex-col sm:flex-row items-baseline justify-between rounded-xl bg-blue-600 p-6 text-white shadow-md">
          <div>
            <span className="text-xs font-semibold tracking-wider uppercase text-blue-200">
              Predicted Total Spot Rate
            </span>
            <div className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-1">
              {formatCurrency(result.predicted_rate)}
            </div>
          </div>
          <div className="mt-3 sm:mt-0 text-left sm:text-right border-t sm:border-t-0 border-blue-500/50 pt-2 sm:pt-0">
            <span className="text-xs text-blue-200 block">Rate Per Mile</span>
            <span className="text-2xl font-bold">{formatCurrency(result.rate_per_mile)} / mi</span>
          </div>
        </div>

        {/* Breakdown Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/50">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              95% Confidence Interval
            </span>
            <div className="text-base font-semibold text-slate-900 dark:text-slate-100 mt-1">
              {formatCurrency(result.confidence_interval.lower)} – {formatCurrency(result.confidence_interval.upper)}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/50">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Base Signal Component
            </span>
            <div className="text-base font-semibold text-slate-900 dark:text-slate-100 mt-1">
              {formatCurrency(result.base_signal)}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/50">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              ML Residual Adjustment
            </span>
            <div className="text-base font-semibold text-slate-900 dark:text-slate-100 mt-1">
              {result.residual >= 0 ? `+${formatCurrency(result.residual)}` : formatCurrency(result.residual)}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/50">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Record ID / DB Primary Key
            </span>
            <div className="text-base font-semibold text-slate-900 dark:text-slate-100 mt-1 flex items-center gap-1">
              <Hash className="h-4 w-4 text-slate-400" />
              <span>#{result.id || "N/A"}</span>
            </div>
          </div>
        </div>

        {/* Audit Meta */}
        <div className="flex flex-wrap items-center justify-between text-xs text-slate-500 dark:text-slate-400 border-t pt-4 dark:border-slate-800">
          <span className="flex items-center gap-1">
            <Tag className="h-3.5 w-3.5" /> Request ID: <code className="font-mono">{result.request_id || "N/A"}</code>
          </span>
          <span className="flex items-center gap-1 mt-1 sm:mt-0">
            <Clock className="h-3.5 w-3.5" /> Execution Timestamp: {formatDateTime(result.prediction_timestamp)}
          </span>
        </div>
      </CardContent>

      <CardFooter className="flex justify-end gap-3 border-t border-slate-100 dark:border-slate-800 pt-4">
        <Button variant="outline" onClick={onReset} leftIcon={<RotateCcw className="h-4 w-4" />}>
          Calculate Another Spot Rate
        </Button>
      </CardFooter>
    </Card>
  );
}
