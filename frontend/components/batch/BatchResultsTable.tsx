"use client";

import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../ui/Card";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Download, RotateCcw, CheckCircle2 } from "lucide-react";
import { BatchPredictionResponse } from "../../lib/types/api";
import { formatCurrency } from "../../lib/utils/formatters";
import { exportBatchToCSV } from "../../lib/utils/csv";

export interface BatchResultsTableProps {
  batchResult: BatchPredictionResponse;
  onReset: () => void;
}

export function BatchResultsTable({ batchResult, onReset }: BatchResultsTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const filtered = batchResult.predictions.filter((p) => {
    const term = searchTerm.toLowerCase();
    return (
      (p.load_id && p.load_id.toLowerCase().includes(term)) ||
      (p.model_version && p.model_version.toLowerCase().includes(term)) ||
      p.predicted_rate.toString().includes(term)
    );
  });

  const totalPages = Math.ceil(filtered.length / pageSize) || 1;
  const paginated = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const avgRate =
    batchResult.predictions.reduce((sum, p) => sum + p.predicted_rate, 0) / (batchResult.count || 1);

  return (
    <Card className="w-full space-y-6">
      <CardHeader className="border-b border-slate-100 dark:border-slate-800">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <div>
              <CardTitle>Batch Prediction Complete</CardTitle>
              <CardDescription>
                Successfully processed {batchResult.count} load predictions in batch.
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onReset} leftIcon={<RotateCcw className="h-4 w-4" />}>
              New Batch Upload
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => exportBatchToCSV(batchResult.predictions)}
              leftIcon={<Download className="h-4 w-4" />}
            >
              Export Results CSV
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 pt-4">
        {/* Metric Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/50">
            <span className="text-xs text-slate-500 font-medium">Total Loads Processed</span>
            <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
              {batchResult.count}
            </div>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/50">
            <span className="text-xs text-slate-500 font-medium">Average Spot Freight Rate</span>
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
              {formatCurrency(avgRate)}
            </div>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/50">
            <span className="text-xs text-slate-500 font-medium">Model Version Used</span>
            <div className="text-xl font-semibold text-slate-900 dark:text-slate-100 mt-1">
              {batchResult.predictions[0]?.model_version || "N/A"}
            </div>
          </div>
        </div>

        {/* Filter bar */}
        <div className="flex items-center justify-between gap-4">
          <div className="w-full sm:w-72">
            <Input
              placeholder="Search load ID..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>
          <span className="text-xs text-slate-500">
            Showing {filtered.length} of {batchResult.count} predictions
          </span>
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-100 dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300">
              <tr>
                <th className="p-3">#</th>
                <th className="p-3">Load ID</th>
                <th className="p-3">Predicted Rate</th>
                <th className="p-3">Rate / Mile</th>
                <th className="p-3">95% Confidence Interval</th>
                <th className="p-3">Base Signal</th>
                <th className="p-3">Residual</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {paginated.map((item, index) => (
                <tr key={index} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                  <td className="p-3 text-xs text-slate-400 font-mono">
                    {(currentPage - 1) * pageSize + index + 1}
                  </td>
                  <td className="p-3 font-semibold text-slate-900 dark:text-slate-100 font-mono">
                    {item.load_id || "N/A"}
                  </td>
                  <td className="p-3 font-bold text-blue-600 dark:text-blue-400">
                    {formatCurrency(item.predicted_rate)}
                  </td>
                  <td className="p-3 text-slate-700 dark:text-slate-300">
                    {formatCurrency(item.rate_per_mile)} / mi
                  </td>
                  <td className="p-3 text-xs text-slate-600 dark:text-slate-400">
                    {formatCurrency(item.confidence_interval.lower)} – {formatCurrency(item.confidence_interval.upper)}
                  </td>
                  <td className="p-3 text-xs text-slate-500">
                    {formatCurrency(item.base_signal)}
                  </td>
                  <td className="p-3 text-xs text-slate-500">
                    {formatCurrency(item.residual)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination controls */}
        <div className="flex items-center justify-between pt-2">
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          >
            Previous
          </Button>
          <span className="text-xs text-slate-500">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
          >
            Next
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
