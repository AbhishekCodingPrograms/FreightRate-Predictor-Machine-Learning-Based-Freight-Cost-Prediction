"use client";

import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../ui/Card";
import { Button } from "../ui/Button";
import { Alert } from "../ui/Alert";
import { UploadCloud, FileText, Download, CheckCircle } from "lucide-react";
import { SinglePredictionRequest, BatchPredictionResponse } from "../../lib/types/api";
import { parseCSVFile } from "../../lib/utils/csv";
import { predictBatch } from "../../lib/api/predictions";

export interface BatchUploadFormProps {
  onSuccess: (results: BatchPredictionResponse) => void;
}

export function BatchUploadForm({ onSuccess }: BatchUploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<SinglePredictionRequest[]>([]);
  const [parseErrors, setParseErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;

    if (!selected.name.endsWith(".csv")) {
      setApiError("Please select a valid CSV file (.csv).");
      return;
    }

    setFile(selected);
    setApiError(null);

    try {
      const res = await parseCSVFile(selected);
      setParsedData(res.data);
      setParseErrors(res.errors);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setApiError(`Failed to parse CSV file: ${message}`);
      setParsedData([]);
    }
  };

  const handleDownloadSample = () => {
    const sampleHeaders = "load_id,pickup,delivery,pickup_lat,pickup_lon,delivery_lat,delivery_lon,distance,equipment,weight,date,market_index,quote_signal\n";
    const sampleRows =
      "LOAD-0001,Lexington,Fort Wayne,38.0464,-84.4970,41.0793,-85.1394,360,Dry Van,32000,2025-12-15,1.05,5.25\n" +
      "LOAD-0002,Chicago,Detroit,41.8781,-87.6298,42.3314,-83.0458,280,Reefer,40000,2025-12-16,1.02,5.10\n" +
      "LOAD-0003,Dallas,Houston,32.7767,-96.7970,29.7604,-95.3698,240,Flatbed,45000,2025-12-17,1.08,5.40\n";

    const blob = new Blob([sampleHeaders + sampleRows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "sample_freight_batch.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleSubmit = async () => {
    if (parsedData.length === 0) {
      setApiError("No valid load records to process.");
      return;
    }

    try {
      setLoading(true);
      setApiError(null);
      const res = await predictBatch({ loads: parsedData });
      onSuccess(res);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setApiError(message || "Batch prediction request failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2">
              <UploadCloud className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              Batch CSV Upload & Execution
            </CardTitle>
            <CardDescription className="mt-1">
              Upload a CSV file containing multiple freight loads (up to 1,000 loads per request).
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={handleDownloadSample} leftIcon={<Download className="h-4 w-4" />}>
            Download Sample CSV Template
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {apiError && (
          <Alert variant="error" title="Batch Processing Error">
            {apiError}
          </Alert>
        )}

        {/* Dropzone / File Select */}
        <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50/50 p-8 text-center transition-colors dark:border-slate-800 dark:bg-slate-900/40 hover:border-blue-400">
          <FileText className="h-10 w-10 text-slate-400 mb-3" />
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
            {file ? `Selected File: ${file.name} (${(file.size / 1024).toFixed(1)} KB)` : "Choose or drag a .csv batch file"}
          </p>
          <p className="text-xs text-slate-500 mt-1">Required columns: pickup, delivery, distance, equipment, weight, date</p>
          <label className="mt-4">
            <span className="inline-flex cursor-pointer items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700">
              Select CSV File
            </span>
            <input type="file" accept=".csv" onChange={handleFileChange} className="hidden" />
          </label>
        </div>

        {/* Parse Warnings */}
        {parseErrors.length > 0 && (
          <Alert variant="warning" title={`${parseErrors.length} validation warning(s) found`}>
            <ul className="list-disc list-inside space-y-1 text-xs">
              {parseErrors.slice(0, 3).map((err, i) => (
                <li key={i}>{err}</li>
              ))}
              {parseErrors.length > 3 && <li>...and {parseErrors.length - 3} more warnings.</li>}
            </ul>
          </Alert>
        )}

        {/* File Preview */}
        {parsedData.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                <CheckCircle className="h-4 w-4 text-emerald-500" />
                Validated {parsedData.length} load record(s) ready for inference
              </span>
            </div>

            <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 dark:bg-slate-800 font-semibold text-slate-700 dark:text-slate-300">
                  <tr>
                    <th className="p-2.5">Load ID</th>
                    <th className="p-2.5">Pickup</th>
                    <th className="p-2.5">Delivery</th>
                    <th className="p-2.5">Distance</th>
                    <th className="p-2.5">Equipment</th>
                    <th className="p-2.5">Weight</th>
                    <th className="p-2.5">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {parsedData.slice(0, 5).map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                      <td className="p-2.5 font-mono">{row.load_id}</td>
                      <td className="p-2.5">{row.pickup}</td>
                      <td className="p-2.5">{row.delivery}</td>
                      <td className="p-2.5">{row.distance} mi</td>
                      <td className="p-2.5">{row.equipment}</td>
                      <td className="p-2.5">{row.weight.toLocaleString()} lbs</td>
                      <td className="p-2.5">{row.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {parsedData.length > 5 && (
              <p className="text-xs text-slate-500 text-center">...showing first 5 of {parsedData.length} records</p>
            )}

            <div className="flex justify-end pt-4 border-t dark:border-slate-800">
              <Button onClick={handleSubmit} isLoading={loading} size="lg" leftIcon={<UploadCloud className="h-5 w-5" />}>
                Process {parsedData.length} Batch Predictions
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
