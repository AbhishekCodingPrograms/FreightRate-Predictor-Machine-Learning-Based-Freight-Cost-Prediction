"use client";

import React, { useState } from "react";
import { PredictionForm } from "../../components/prediction/PredictionForm";
import { PredictionResultCard } from "../../components/prediction/PredictionResultCard";
import { SinglePredictionResponse } from "../../lib/types/api";

export default function PredictPage() {
  const [result, setResult] = useState<SinglePredictionResponse | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Single Spot Freight Rate Prediction
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Estimate spot freight rates and 95% confidence intervals for individual truckload shipments.
        </p>
      </div>

      {!result ? (
        <PredictionForm onSuccess={(res) => setResult(res)} />
      ) : (
        <PredictionResultCard result={result} onReset={() => setResult(null)} />
      )}
    </div>
  );
}
