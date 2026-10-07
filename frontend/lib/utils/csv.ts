import Papa from "papaparse";
import { SinglePredictionRequest, SinglePredictionResponse } from "../types/api";

export interface CSVParseResult {
  data: SinglePredictionRequest[];
  errors: string[];
  totalRows: number;
}

export function parseCSVFile(file: File): Promise<CSVParseResult> {
  return new Promise((resolve, reject) => {
    Papa.parse<Record<string, unknown>>(file, {
      header: true,
      skipEmptyLines: true,
      dynamicTyping: true,
      complete: (results) => {
        const parsedRequests: SinglePredictionRequest[] = [];
        const errors: string[] = [];

        results.data.forEach((row, idx) => {
          const r = row as Record<string, unknown>;
          const lineNum = idx + 2; // header is row 1

          const getVal = (...keys: string[]): string => {
            for (const key of keys) {
              if (r[key] !== undefined && r[key] !== null && r[key] !== "") {
                return String(r[key]).trim();
              }
            }
            return "";
          };

          const getNum = (...keys: string[]): number => {
            for (const key of keys) {
              if (r[key] !== undefined && r[key] !== null && r[key] !== "") {
                const val = Number(r[key]);
                if (!isNaN(val)) return val;
              }
            }
            return NaN;
          };

          const pickup = getVal("pickup", "Pickup", "origin", "Origin");
          const delivery = getVal("delivery", "Delivery", "destination", "Destination");
          const distance = getNum("distance", "Distance");
          const weight = getNum("weight", "Weight");
          const equipment = getVal("equipment", "Equipment") || "Dry Van";
          const date = getVal("date", "Date") || new Date().toISOString().split("T")[0];

          const pickup_lat = getNum("pickup_lat", "pickup_latitude");
          const pickup_lon = getNum("pickup_lon", "pickup_longitude");
          const delivery_lat = getNum("delivery_lat", "delivery_latitude");
          const delivery_lon = getNum("delivery_lon", "delivery_longitude");

          const market_index = getNum("market_index");
          const quote_signal = getNum("quote_signal");

          if (!pickup || !delivery) {
            errors.push(`Row ${lineNum}: Missing pickup or delivery city.`);
            return;
          }
          if (isNaN(distance) || distance <= 0) {
            errors.push(`Row ${lineNum}: Distance must be > 0.`);
            return;
          }
          if (isNaN(weight) || weight <= 0) {
            errors.push(`Row ${lineNum}: Weight must be > 0.`);
            return;
          }

          const load_id = getVal("load_id", "Load_ID") || `LOAD-${String(idx + 1).padStart(4, "0")}`;

          parsedRequests.push({
            load_id,
            pickup,
            delivery,
            pickup_lat: isNaN(pickup_lat) ? 38.0464 : pickup_lat,
            pickup_lon: isNaN(pickup_lon) ? -84.497 : pickup_lon,
            delivery_lat: isNaN(delivery_lat) ? 41.0793 : delivery_lat,
            delivery_lon: isNaN(delivery_lon) ? -85.1394 : delivery_lon,
            distance,
            equipment,
            weight,
            market_index: isNaN(market_index) ? undefined : market_index,
            quote_signal: isNaN(quote_signal) ? undefined : quote_signal,
            date,
          });
        });

        resolve({
          data: parsedRequests,
          errors,
          totalRows: results.data.length,
        });
      },
      error: (err) => {
        reject(err);
      },
    });
  });
}

export function exportBatchToCSV(predictions: SinglePredictionResponse[], filename = "batch_predictions.csv") {
  const exportRows = predictions.map((p) => ({
    load_id: p.load_id || "",
    predicted_rate: p.predicted_rate,
    rate_per_mile: p.rate_per_mile,
    currency: p.currency || "USD",
    confidence_lower: p.confidence_interval?.lower || 0,
    confidence_upper: p.confidence_interval?.upper || 0,
    base_signal: p.base_signal || 0,
    residual: p.residual || 0,
    model_version: p.model_version || "",
    prediction_timestamp: p.prediction_timestamp || "",
    request_id: p.request_id || "",
  }));

  const csv = Papa.unparse(exportRows);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
