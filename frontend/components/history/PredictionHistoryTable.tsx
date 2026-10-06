"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../ui/Card";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import { Skeleton } from "../ui/Skeleton";
import { Alert } from "../ui/Alert";
import { PredictionDetailModal } from "./PredictionDetailModal";
import { History, RefreshCw, Eye, Filter } from "lucide-react";
import { listPredictions } from "../../lib/api/predictions";
import { PredictionDetailResponse, PredictionListResponse } from "../../lib/types/api";
import { formatCurrency, formatDateTime } from "../../lib/utils/formatters";

export function PredictionHistoryTable() {
  const [data, setData] = useState<PredictionListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [loadIdFilter, setLoadIdFilter] = useState("");
  const [modelVersionFilter, setModelVersionFilter] = useState("");
  const [startDateFilter, setStartDateFilter] = useState("");
  const [endDateFilter, setEndDateFilter] = useState("");

  const limit = 20;
  const [offset, setOffset] = useState(0);

  // Selected for modal
  const [selectedPrediction, setSelectedPrediction] = useState<PredictionDetailResponse | null>(null);

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await listPredictions({
        load_id: loadIdFilter.trim() || undefined,
        model_version: modelVersionFilter.trim() || undefined,
        start_date: startDateFilter || undefined,
        end_date: endDateFilter || undefined,
        limit,
        offset,
      });
      setData(res);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message || "Failed to load prediction history.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [loadIdFilter, modelVersionFilter, startDateFilter, endDateFilter, limit, offset]);

  useEffect(() => {
    let isMounted = true;
    const loadData = async () => {
      try {
        const res = await listPredictions({
          load_id: loadIdFilter.trim() || undefined,
          model_version: modelVersionFilter.trim() || undefined,
          start_date: startDateFilter || undefined,
          end_date: endDateFilter || undefined,
          limit,
          offset,
        });
        if (isMounted) {
          setData(res);
          setError(null);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const message = err instanceof Error ? err.message : String(err);
          setError(message || "Failed to load prediction history.");
          setData(null);
          setLoading(false);
        }
      }
    };
    loadData();
    return () => {
      isMounted = false;
    };
  }, [loadIdFilter, modelVersionFilter, startDateFilter, endDateFilter, limit, offset]);

  const handleResetFilters = () => {
    setLoadIdFilter("");
    setModelVersionFilter("");
    setStartDateFilter("");
    setEndDateFilter("");
    setOffset(0);
  };

  const totalPages = data ? Math.ceil(data.total / limit) || 1 : 1;
  const currentPage = Math.floor(offset / limit) + 1;

  return (
    <Card className="w-full space-y-6">
      <CardHeader className="border-b border-slate-100 dark:border-slate-800">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              Persistent Prediction History Audit
            </CardTitle>
            <CardDescription className="mt-1">
              Query past single and batch prediction logs stored in PostgreSQL.
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={fetchHistory} leftIcon={<RefreshCw className="h-4 w-4" />}>
            Refresh Table
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Filters bar */}
        <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-4 dark:border-slate-800 dark:bg-slate-900/40 space-y-3">
          <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <Filter className="h-3.5 w-3.5 text-blue-500" /> Filter Prediction Records
          </span>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            <Input
              placeholder="Search Load ID..."
              value={loadIdFilter}
              onChange={(e) => {
                setLoadIdFilter(e.target.value);
                setOffset(0);
              }}
            />
            <Input
              placeholder="Model Version..."
              value={modelVersionFilter}
              onChange={(e) => {
                setModelVersionFilter(e.target.value);
                setOffset(0);
              }}
            />
            <Input
              type="date"
              value={startDateFilter}
              onChange={(e) => {
                setStartDateFilter(e.target.value);
                setOffset(0);
              }}
            />
            <Input
              type="date"
              value={endDateFilter}
              onChange={(e) => {
                setEndDateFilter(e.target.value);
                setOffset(0);
              }}
            />
          </div>

          {(loadIdFilter || modelVersionFilter || startDateFilter || endDateFilter) && (
            <div className="flex justify-end pt-1">
              <button
                onClick={handleResetFilters}
                className="text-xs font-medium text-blue-600 hover:underline dark:text-blue-400"
              >
                Clear all filters
              </button>
            </div>
          )}
        </div>

        {error && (
          <Alert variant="error" title="Error Loading History">
            {error}
          </Alert>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        )}

        {/* Table Content */}
        {!loading && data && data.items.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-200 p-8 text-center dark:border-slate-800">
            <History className="h-8 w-8 text-slate-400 mx-auto mb-2" />
            <h4 className="font-semibold text-slate-700 dark:text-slate-300 text-sm">No prediction records found</h4>
            <p className="text-xs text-slate-500 mt-1">Try adjusting your filters or run a single prediction.</p>
          </div>
        )}

        {!loading && data && data.items.length > 0 && (
          <>
            <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-100 dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  <tr>
                    <th className="p-3">ID</th>
                    <th className="p-3">Load ID</th>
                    <th className="p-3">Predicted Rate</th>
                    <th className="p-3">Rate / Mile</th>
                    <th className="p-3">Model Version</th>
                    <th className="p-3">Timestamp</th>
                    <th className="p-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {data.items.map((rec) => (
                    <tr key={rec.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                      <td className="p-3 text-xs text-slate-400 font-mono">#{rec.id}</td>
                      <td className="p-3 font-semibold text-slate-900 dark:text-slate-100 font-mono">
                        {rec.load_id || "N/A"}
                      </td>
                      <td className="p-3 font-bold text-blue-600 dark:text-blue-400">
                        {formatCurrency(rec.predicted_rate)}
                      </td>
                      <td className="p-3 text-slate-700 dark:text-slate-300">
                        {formatCurrency(rec.rate_per_mile)} / mi
                      </td>
                      <td className="p-3 text-xs text-slate-600 dark:text-slate-400">
                        <span className="rounded-md bg-slate-100 px-2 py-0.5 dark:bg-slate-800 font-mono">
                          {rec.model_version}
                        </span>
                      </td>
                      <td className="p-3 text-xs text-slate-500">
                        {formatDateTime(rec.prediction_timestamp)}
                      </td>
                      <td className="p-3 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedPrediction(rec)}
                          leftIcon={<Eye className="h-3.5 w-3.5" />}
                        >
                          Details
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
              <span className="text-xs text-slate-500">
                Showing {offset + 1} to {Math.min(offset + limit, data.total)} of {data.total} records
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={offset === 0}
                  onClick={() => setOffset((o) => Math.max(0, o - limit))}
                >
                  Previous
                </Button>
                <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={offset + limit >= data.total}
                  onClick={() => setOffset((o) => o + limit)}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </CardContent>

      <PredictionDetailModal
        prediction={selectedPrediction}
        isOpen={selectedPrediction !== null}
        onClose={() => setSelectedPrediction(null)}
      />
    </Card>
  );
}
