import sys
import time
import platform
from pathlib import Path

# Add project root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
from fastapi.testclient import TestClient
from app.main import app


def benchmark_single_prediction(client: TestClient, n_runs: int = 100):
    payload = {
        "load_id": "BENCH-001",
        "pickup": "Lexington",
        "delivery": "Fort Wayne",
        "pickup_lat": 38.0464,
        "pickup_lon": -84.4970,
        "delivery_lat": 41.0793,
        "delivery_lon": -85.1394,
        "distance": 360.0,
        "equipment": "Dry Van",
        "weight": 32000.0,
        "market_index": 1.05,
        "quote_signal": 5.25,
        "date": "2025-12-15"
    }

    # Warmup
    for _ in range(5):
        client.post("/api/v1/predict", json=payload)

    latencies = []
    t_start = time.time()
    for _ in range(n_runs):
        s = time.time()
        res = client.post("/api/v1/predict", json=payload)
        latencies.append((time.time() - s) * 1000.0)
        assert res.status_code == 200

    total_time = time.time() - t_start
    throughput = n_runs / total_time

    print(f"--- Single Prediction Benchmark ({n_runs} runs) ---")
    print(f"Mean Latency   : {np.mean(latencies):.2f} ms")
    print(f"Median Latency : {np.median(latencies):.2f} ms")
    print(f"P95 Latency    : {np.percentile(latencies, 95):.2f} ms")
    print(f"P99 Latency    : {np.percentile(latencies, 99):.2f} ms")
    print(f"Throughput     : {throughput:.2f} req/sec\n")


def benchmark_batch_prediction(client: TestClient, batch_sizes=[10, 50, 100, 500]):
    base_item = {
        "pickup": "Lexington",
        "delivery": "Fort Wayne",
        "pickup_lat": 38.0464,
        "pickup_lon": -84.4970,
        "delivery_lat": 41.0793,
        "delivery_lon": -85.1394,
        "distance": 360.0,
        "equipment": "Dry Van",
        "weight": 32000.0,
        "date": "2025-12-15"
    }

    print("--- Batch Prediction Benchmark ---")
    for size in batch_sizes:
        payload = {"loads": [dict(base_item, load_id=f"B-{i}") for i in range(size)]}
        t0 = time.time()
        res = client.post("/api/v1/predict/batch", json=payload)
        elapsed_ms = (time.time() - t0) * 1000.0
        assert res.status_code == 200
        print(f"Batch Size {size:3d} : {elapsed_ms:.2f} ms ({elapsed_ms/size:.3f} ms/load | {size/(elapsed_ms/1000.0):.1f} loads/sec)")


if __name__ == "__main__":
    print(f"Benchmarking Spotter Freight Rate API on {platform.system()} {platform.machine()}")
    with TestClient(app) as client:
        benchmark_single_prediction(client, 100)
        benchmark_batch_prediction(client, [10, 50, 100, 500])
