"use client";

import React, { useState } from "react";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { Button } from "../ui/Button";
import { Alert } from "../ui/Alert";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../ui/Card";
import { Calculator, Sparkles, MapPin } from "lucide-react";
import { SinglePredictionRequest, SinglePredictionResponse } from "../../lib/types/api";
import { predictSingle } from "../../lib/api/predictions";

export interface PredictionFormProps {
  onSuccess: (result: SinglePredictionResponse) => void;
}

const SAMPLE_PRESET: SinglePredictionRequest = {
  load_id: "TE-000001",
  pickup: "Lexington",
  delivery: "Fort Wayne",
  pickup_lat: 38.0464,
  pickup_lon: -84.4970,
  delivery_lat: 41.0793,
  delivery_lon: -85.1394,
  distance: 360.0,
  equipment: "Dry Van",
  weight: 32000.0,
  market_index: 1.05,
  quote_signal: 5.25,
  date: "2025-12-15",
};

export function PredictionForm({ onSuccess }: PredictionFormProps) {
  const [formData, setFormData] = useState<SinglePredictionRequest>(SAMPLE_PRESET);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleChange = (field: keyof SinglePredictionRequest, value: unknown) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handlePreset = () => {
    setFormData(SAMPLE_PRESET);
    setErrorMsg(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    // Client side validation
    if (!formData.pickup.trim() || !formData.delivery.trim()) {
      setErrorMsg("Pickup and delivery locations are required.");
      return;
    }
    if (formData.distance <= 0) {
      setErrorMsg("Distance must be greater than 0 miles.");
      return;
    }
    if (formData.weight <= 0) {
      setErrorMsg("Weight must be greater than 0 pounds.");
      return;
    }
    if (formData.pickup_lat < -90 || formData.pickup_lat > 90 || formData.delivery_lat < -90 || formData.delivery_lat > 90) {
      setErrorMsg("Latitude must be between -90 and 90 degrees.");
      return;
    }
    if (formData.pickup_lon < -180 || formData.pickup_lon > 180 || formData.delivery_lon < -180 || formData.delivery_lon > 180) {
      setErrorMsg("Longitude must be between -180 and 180 degrees.");
      return;
    }

    try {
      setLoading(true);
      const response = await predictSingle({
        ...formData,
        distance: Number(formData.distance),
        weight: Number(formData.weight),
        pickup_lat: Number(formData.pickup_lat),
        pickup_lon: Number(formData.pickup_lon),
        delivery_lat: Number(formData.delivery_lat),
        delivery_lon: Number(formData.delivery_lon),
        market_index: formData.market_index ? Number(formData.market_index) : undefined,
        quote_signal: formData.quote_signal ? Number(formData.quote_signal) : undefined,
      });
      onSuccess(response);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setErrorMsg(message || "Failed to calculate freight rate. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              Single Spot Rate Estimator
            </CardTitle>
            <CardDescription className="mt-1">
              Enter shipment route and cargo details to estimate spot freight rates using ML.
            </CardDescription>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={handlePreset} leftIcon={<Sparkles className="h-4 w-4" />}>
            Load Preset Sample
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {errorMsg && (
            <Alert variant="error" title="Prediction Failed">
              {errorMsg}
            </Alert>
          )}

          {/* Section 1: Identification & Locations */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5 border-b pb-2 dark:border-slate-800">
              <MapPin className="h-4 w-4 text-blue-500" /> Route & Identification
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="Load ID (Optional)"
                placeholder="e.g. TE-000001"
                value={formData.load_id || ""}
                onChange={(e) => handleChange("load_id", e.target.value)}
              />
              <Input
                label="Pickup Origin"
                required
                placeholder="City / State (e.g. Lexington)"
                value={formData.pickup}
                onChange={(e) => handleChange("pickup", e.target.value)}
              />
              <Input
                label="Delivery Destination"
                required
                placeholder="City / State (e.g. Fort Wayne)"
                value={formData.delivery}
                onChange={(e) => handleChange("delivery", e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Input
                label="Pickup Lat"
                type="number"
                step="any"
                required
                value={formData.pickup_lat}
                onChange={(e) => handleChange("pickup_lat", e.target.value)}
              />
              <Input
                label="Pickup Lon"
                type="number"
                step="any"
                required
                value={formData.pickup_lon}
                onChange={(e) => handleChange("pickup_lon", e.target.value)}
              />
              <Input
                label="Delivery Lat"
                type="number"
                step="any"
                required
                value={formData.delivery_lat}
                onChange={(e) => handleChange("delivery_lat", e.target.value)}
              />
              <Input
                label="Delivery Lon"
                type="number"
                step="any"
                required
                value={formData.delivery_lon}
                onChange={(e) => handleChange("delivery_lon", e.target.value)}
              />
            </div>
          </div>

          {/* Section 2: Equipment & Cargo */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 border-b pb-2 dark:border-slate-800">
              Shipment Specification
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="Distance (Miles)"
                type="number"
                step="0.1"
                required
                min="0.1"
                placeholder="360"
                value={formData.distance}
                onChange={(e) => handleChange("distance", e.target.value)}
              />
              <Select
                label="Equipment Type"
                required
                value={formData.equipment}
                onChange={(e) => handleChange("equipment", e.target.value)}
                options={[
                  { value: "Dry Van", label: "Dry Van" },
                  { value: "Reefer", label: "Reefer" },
                  { value: "Flatbed", label: "Flatbed" },
                ]}
              />
              <Input
                label="Cargo Weight (Lbs)"
                type="number"
                step="1"
                required
                min="1"
                placeholder="32000"
                value={formData.weight}
                onChange={(e) => handleChange("weight", e.target.value)}
              />
            </div>
          </div>

          {/* Section 3: Signals & Dates */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 border-b pb-2 dark:border-slate-800">
              Market Multipliers & Scheduled Date
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="Market Index (Optional)"
                type="number"
                step="0.01"
                placeholder="Defaults to median (1.05)"
                value={formData.market_index ?? ""}
                onChange={(e) => handleChange("market_index", e.target.value ? parseFloat(e.target.value) : undefined)}
              />
              <Input
                label="Quote Signal (Optional)"
                type="number"
                step="0.01"
                placeholder="Defaults to median (5.25)"
                value={formData.quote_signal ?? ""}
                onChange={(e) => handleChange("quote_signal", e.target.value ? parseFloat(e.target.value) : undefined)}
              />
              <Input
                label="Scheduled Pickup Date"
                type="date"
                required
                value={formData.date}
                onChange={(e) => handleChange("date", e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t dark:border-slate-800">
            <Button type="submit" size="lg" isLoading={loading} leftIcon={<Calculator className="h-5 w-5" />}>
              Calculate Spot Rate Prediction
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
