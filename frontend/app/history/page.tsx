import React from "react";
import { PredictionHistoryTable } from "../../components/history/PredictionHistoryTable";

export default function HistoryPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Prediction History Audit Log
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Query persistent prediction records from PostgreSQL, filter by Load ID or model version, and inspect audit details.
        </p>
      </div>

      <PredictionHistoryTable />
    </div>
  );
}
