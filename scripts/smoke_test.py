"""
FreightRate Predictor - Automated Production Smoke Test
Verifies health, readiness, model metadata, single prediction, batch prediction, and history persistence endpoints.
"""

import sys
import time
import requests

BASE_URL = "http://localhost:8000"

def run_smoke_test():
    print("=" * 60)
    print("FREIGHTRATE PREDICTOR - AUTOMATED SMOKE TEST")
    print("=" * 60)

    session = requests.Session()

    # 1. Health Endpoint
    print("\n1. Testing GET /health...")
    try:
        r = session.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {r.status_code}")
        print(f"Payload: {r.json()}")
        assert r.status_code == 200
        assert r.json().get("status") == "healthy"
        print("[PASS] Health check PASSED")
    except Exception as e:
        print(f"[FAIL] Health check FAILED: {e}")
        return False

    # 2. Readiness Endpoint
    print("\n2. Testing GET /ready...")
    try:
        r = session.get(f"{BASE_URL}/ready", timeout=5)
        print(f"Status: {r.status_code}")
        print(f"Payload: {r.json()}")
        assert r.status_code == 200
        assert r.json().get("status") == "ready"
        print("[PASS] Readiness check PASSED")
    except Exception as e:
        print(f"[FAIL] Readiness check FAILED: {e}")
        return False

    # 3. Model Info Endpoint
    print("\n3. Testing GET /api/v1/model/info...")
    try:
        r = session.get(f"{BASE_URL}/api/v1/model/info", timeout=5)
        print(f"Status: {r.status_code}")
        payload = r.json()
        print(f"Model Version: {payload.get('model_version')}")
        print(f"Feature Count: {payload.get('feature_count')}")
        assert r.status_code == 200
        assert "ensemble_weights" in payload
        print("[PASS] Model info PASSED")
    except Exception as e:
        print(f"[FAIL] Model info FAILED: {e}")
        return False

    # 4. Single Prediction Endpoint
    print("\n4. Testing POST /api/v1/predict...")
    sample_request = {
        "load_id": "SMOKE-0001",
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
    try:
        t0 = time.time()
        r = session.post(f"{BASE_URL}/api/v1/predict", json=sample_request, timeout=5)
        latency = (time.time() - t0) * 1000
        print(f"Status: {r.status_code} ({latency:.1f} ms)")
        payload = r.json()
        print(f"Predicted Rate: ${payload.get('predicted_rate'):.2f}")
        print(f"Rate Per Mile: ${payload.get('rate_per_mile'):.2f}")
        assert r.status_code == 200
        assert payload.get("predicted_rate") > 0
        print("[PASS] Single prediction PASSED")
    except Exception as e:
        print(f"[FAIL] Single prediction FAILED: {e}")
        return False

    # 5. Batch Prediction Endpoint
    print("\n5. Testing POST /api/v1/predict/batch...")
    batch_request = {
        "loads": [sample_request, {**sample_request, "load_id": "SMOKE-0002", "distance": 450.0}]
    }
    try:
        t0 = time.time()
        r = session.post(f"{BASE_URL}/api/v1/predict/batch", json=batch_request, timeout=5)
        latency = (time.time() - t0) * 1000
        print(f"Status: {r.status_code} ({latency:.1f} ms)")
        payload = r.json()
        print(f"Batch Count: {payload.get('count')}")
        assert r.status_code == 200
        assert payload.get("count") == 2
        print("[PASS] Batch prediction PASSED")
    except Exception as e:
        print(f"[FAIL] Batch prediction FAILED: {e}")
        return False

    # 6. History Endpoint
    print("\n6. Testing GET /api/v1/predictions...")
    try:
        r = session.get(f"{BASE_URL}/api/v1/predictions?limit=10", timeout=5)
        print(f"Status: {r.status_code}")
        payload = r.json()
        print(f"Total Logged Predictions: {payload.get('total')}")
        assert r.status_code == 200
        assert len(payload.get("items", [])) > 0
        print("[PASS] History listing PASSED")
    except Exception as e:
        print(f"[FAIL] History listing FAILED: {e}")
        return False

    print("\n" + "=" * 60)
    print("ALL SMOKE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
