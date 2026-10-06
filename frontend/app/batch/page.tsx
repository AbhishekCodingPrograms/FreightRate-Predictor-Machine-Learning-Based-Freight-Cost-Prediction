"use client";

import React, { useState } from "react";
import { BatchUploadForm } from "../../components/batch/BatchUploadForm";
import { BatchResultsTable } from "../../components/batch/BatchResultsTable";
import { BatchPredictionResponse } from "../../lib/types/api";

export default function BatchPage() {
  const [batchResult, setBatchResult] = useState<BatchPredictionResponse | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Batch Freight Rate Prediction
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Process batch CSV load manifests efficiently (up to 1,000 loads per request) and export predictions.
        </p>
      </div>

      {!batchResult ? (
        <BatchUploadForm onSuccess={(res) => setBatchResult(res)} />
      ) : (
        <BatchResultsTable batchResult={batchResult} onReset={() => setBatchResult(null)} />
      )}
    </div>
  );
}
