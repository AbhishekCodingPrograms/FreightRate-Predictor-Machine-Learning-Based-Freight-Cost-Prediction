"use client";

import React from "react";
import { Modal } from "../ui/Modal";
import { Badge } from "../ui/Badge";
import { formatCurrency, formatDateTime } from "../../lib/utils/formatters";
import { PredictionDetailResponse } from "../../lib/types/api";
import { Truck, MapPin, Calendar, Weight, Ruler, Layers } from "lucide-react";

export interface PredictionDetailModalProps {
  prediction: PredictionDetailResponse | null;
  isOpen: boolean;
  onClose: () => void;
}

export function PredictionDetailModal({ prediction, isOpen, onClose }: PredictionDetailModalProps) {
  if (!prediction) return null;

  const inp = prediction.input_data || {};
  const pickup = String(inp.pickup ?? "N/A");
  const delivery = String(inp.delivery ?? "N/A");
  const distance = inp.distance ? `${String(inp.distance)} mi` : "N/A";
  const equipment = String(inp.equipment ?? "N/A");
  const weight = inp.weight ? `${Number(inp.weight).toLocaleString()} lbs` : "N/A";
  const dateStr = String(inp.date ?? "N/A");

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Prediction Audit Detail #${prediction.id}`}>
      <div className="space-y-6 text-sm">
        {/* Top Summary Banner */}
        <div className="flex items-center justify-between rounded-lg bg-blue-50 p-4 dark:bg-blue-950/40 border border-blue-100 dark:border-blue-900/50">
          <div>
            <span className="text-xs text-blue-600 dark:text-blue-400 font-semibold uppercase tracking-wider block">
              Predicted Rate
            </span>
            <div className="text-3xl font-extrabold text-blue-700 dark:text-blue-300 mt-0.5">
              {formatCurrency(prediction.predicted_rate)}
            </div>
            <span className="text-xs text-slate-500">
              {formatCurrency(prediction.rate_per_mile)} per mile
            </span>
          </div>
          <div className="text-right">
            <Badge variant="info" className="mb-1">
              {prediction.model_version}
            </Badge>
            <span className="block text-xs text-slate-500">
              {formatDateTime(prediction.prediction_timestamp)}
            </span>
          </div>
        </div>

        {/* Confidence & Components */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
            <span className="text-slate-500 font-medium">95% Confidence Interval</span>
            <div className="text-sm font-semibold text-slate-900 dark:text-slate-100 mt-0.5">
              {formatCurrency(prediction.confidence_interval.lower)} – {formatCurrency(prediction.confidence_interval.upper)}
            </div>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
            <span className="text-slate-500 font-medium">Base Signal / Residual</span>
            <div className="text-sm font-semibold text-slate-900 dark:text-slate-100 mt-0.5">
              {formatCurrency(prediction.base_signal || 0)} / {formatCurrency(prediction.residual || 0)}
            </div>
          </div>
        </div>

        {/* Input Payload Record */}
        <div className="space-y-3 border-t pt-4 dark:border-slate-800">
          <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <Layers className="h-4 w-4 text-blue-500" /> Stored Route & Shipment Attributes
          </h4>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
            <div className="flex items-center gap-2 rounded-md bg-slate-50 p-2.5 dark:bg-slate-800/50">
              <MapPin className="h-4 w-4 text-slate-400 shrink-0" />
              <div>
                <span className="text-slate-400 block text-[10px]">Origin</span>
                <span className="font-medium">{pickup}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 rounded-md bg-slate-50 p-2.5 dark:bg-slate-800/50">
              <MapPin className="h-4 w-4 text-slate-400 shrink-0" />
              <div>
                <span className="text-slate-400 block text-[10px]">Destination</span>
                <span className="font-medium">{delivery}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 rounded-md bg-slate-50 p-2.5 dark:bg-slate-800/50">
              <Ruler className="h-4 w-4 text-slate-400 shrink-0" />
              <div>
                <span className="text-slate-400 block text-[10px]">Distance</span>
                <span className="font-medium">{distance}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 rounded-md bg-slate-50 p-2.5 dark:bg-slate-800/50">
              <Truck className="h-4 w-4 text-slate-400 shrink-0" />
              <div>
                <span className="text-slate-400 block text-[10px]">Equipment</span>
                <span className="font-medium">{equipment}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 rounded-md bg-slate-50 p-2.5 dark:bg-slate-800/50">
              <Weight className="h-4 w-4 text-slate-400 shrink-0" />
              <div>
                <span className="text-slate-400 block text-[10px]">Weight</span>
                <span className="font-medium">{weight}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 rounded-md bg-slate-50 p-2.5 dark:bg-slate-800/50">
              <Calendar className="h-4 w-4 text-slate-400 shrink-0" />
              <div>
                <span className="text-slate-400 block text-[10px]">Scheduled Date</span>
                <span className="font-medium">{dateStr}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Audit Meta */}
        <div className="rounded-lg bg-slate-100 p-3 text-xs font-mono text-slate-600 dark:bg-slate-800 dark:text-slate-400 flex justify-between">
          <span>Request ID: {prediction.request_id}</span>
          <span>Load ID: {prediction.load_id || "N/A"}</span>
        </div>
      </div>
    </Modal>
  );
}
