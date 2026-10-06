import React from "react";
import { ModelInfoView } from "../../components/model/ModelInfoView";

export default function ModelsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Model Architecture & Validation Metrics
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Inspect production ML ensemble specifications, model weights, and out-of-time validation performance.
        </p>
      </div>

      <ModelInfoView />
    </div>
  );
}
