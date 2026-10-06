# Enterprise System & MLOps Architecture Specification
## Spotter FreightRate Predictor — Machine Learning Platform

---

## 1. Executive Summary & Architectural Overview

The **FreightRate Predictor** is a high-availability, production-grade Machine Learning platform designed for real-time spot freight rate estimation, automated MLOps monitoring, and governance.

The system uses a **Residual Ensemble Target Strategy** ($\text{posted\_rate} = \text{base\_signal} + \text{residual}$) combining **CatBoost (0.45)**, **LightGBM (0.35)**, **XGBoost (0.15)**, and **Ridge Regression (0.05)**. The application is packaged into a containerized microservice topology using Docker Compose, Nginx, Next.js 16, FastAPI, and PostgreSQL 16.

---

## 2. Multi-Tier System Topology

```mermaid
graph TD
    Client[Client / Web Browser / API Consumer] -->|HTTPS 443 / HTTP 80| Nginx Proxy[Nginx Reverse Proxy & Load Balancer]
    
    subgraph Edge Layer
        Nginx Proxy -->|Path / -> Port 3000| NextJS[Next.js 16 App Router UI]
        Nginx Proxy -->|Path /api/v1 -> Port 8000| FastAPI[FastAPI REST microservice]
    end

    subgraph Application & Inference Layer
        FastAPI --> Middleware[Request ID, Timing & CORS Middleware]
        Middleware --> Router[API Router /api/v1]
        Router --> PredService[Prediction Service Engine]
        Router --> MLOpsService[MLOps & Governance Service]
        
        PredService --> FeatureEngine[Feature Engineering Pipeline]
        FeatureEngine --> ArtifactLoader[Joblib Model Artifact Loader]
        ArtifactLoader --> MLEnsemble[Residual ML Ensemble\nCatBoost + LightGBM + XGBoost + Ridge]
    end

    subgraph Persistence & Audit Layer
        FastAPI -->|SQLAlchemy 2.x DB Pool| Postgres[(PostgreSQL 16 Primary Database)]
        Alembic[Alembic Migration Engine] -->|Schema Migrations| Postgres
    end

    subgraph MLOps & Autonomous Quality Engine
        MLOpsService --> DQEngine[Data Quality Auditor]
        MLOpsService --> DriftEngine[PSI & KS Drift Detector]
        MLOpsService --> PerfEngine[Delayed Outcome Performance Evaluator]
        MLOpsService --> RegEngine[Model Registry & State Machine]
        
        DQEngine -->|Audit Metrics| Postgres
        DriftEngine -->|Drift Metrics| Postgres
        PerfEngine -->|Performance Logs| Postgres
        RegEngine -->|Audit Events| Postgres
    end
```

---

## 3. Real-Time Inference Sequence Workflow

The sequence below illustrates the end-to-end processing of a single or batch rate estimation request:

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client / Browser
    participant API as FastAPI REST API
    participant Middleware as Request Audit & Validation
    participant Engine as Feature Pipeline
    participant Ensemble as ML Model Ensemble
    participant DB as PostgreSQL DB
    
    Client->>API: POST /api/v1/predict (Load payload)
    API->>Middleware: Validate JSON Schema & Inject X-Request-ID
    Middleware->>Engine: Extract raw input & calculate geospatial features
    Engine->>Engine: Compute distance_miles, rpm_base, equipment encodings, temporal features
    Engine->>Ensemble: Pass feature vector X
    Ensemble->>Ensemble: Predict residual = ensemble(X)
    Ensemble->>Engine: Calculate predicted_rate = base_signal + residual
    Engine->>Engine: Calculate 95% Confidence Bounds [lower, upper]
    Engine->>DB: Async audit log into prediction_requests & predictions tables
    Engine-->>API: Return prediction payload (rate, confidence, model_version)
    API-->>Client: 200 OK Response (JSON Payload)
```

---

## 4. Machine Learning & Feature Engineering Architecture

### 4.1 Target Formulation Strategy
Instead of directly predicting volatile raw spot rates, the system decomposes the target into:
$$\text{posted\_rate} = \text{base\_signal} + \text{residual}$$
where $\text{base\_signal} = \text{distance\_miles} \times \text{equipment\_historical\_rpm}$.

### 4.2 Out-of-Time (OOT) Train/Validation Split
- **Training Set (Jan–Aug):** 38,477 historical load records.
- **Out-of-Time Validation Set (Sep–Oct):** 9,523 untouched load records mimicking true deployment.

### 4.3 Model Ensemble Weights & Validation Metrics
- **CatBoost:** $0.45$
- **LightGBM:** $0.35$
- **XGBoost:** $0.15$
- **Ridge Regression:** $0.05$

| Metric | Out-of-Time Validation Result | Target SLA |
| :--- | :--- | :--- |
| **RMSE** | **$128.45** | < $150.00 |
| **MAE** | **$92.30** | < $110.00 |
| **MAPE** | **4.72%** | < 6.00% |
| **$R^2$ Score** | **0.9453** | > 0.9000 |

---

## 5. MLOps Governance & State Machine Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Candidate: Model Retrained / Registered
    Candidate --> ValidationGate: Trigger Automated Evaluation
    
    state ValidationGate {
        [*] --> CheckMetrics: Validate OOT Metrics (RMSE < $150, R² > 0.90)
        CheckMetrics --> CheckDataQuality: Validate Feature Integrity
        CheckDataQuality --> CheckDrift: Check Baseline PSI (< 0.10)
    }
    
    ValidationGate --> Approved: Passed All Promotion Gates
    ValidationGate --> Rejected: Failed Metrics or Quality Gate
    
    Approved --> Production: Promoted via API / CLI (/promote)
    Production --> Monitoring: Live Serving & Drift Auditing
    
    state Monitoring {
        [*] --> DataQualityCheck: Continuous Input Audit
        DataQualityCheck --> PSI_DriftCheck: Population Stability Index
        PSI_DriftCheck --> DelayedOutcomeMatch: Delayed Actual Rate Evaluation
    }
    
    Monitoring --> Production: Metrics Normal
    Monitoring --> Demoted: PSI Drift > 0.25 OR RMSE Degradation
    Demoted --> Rollback: Execute Automated Rollback to Previous Version
    Rollback --> Production: Active Baseline Restored
    Rejected --> [*]
```

---

## 6. Database ERD & Schema Design

```mermaid
erDiagram
    MODEL_VERSIONS {
        int id PK
        string version UK
        string model_type
        string target_strategy
        json ensemble_weights
        json validation_metrics
        string status
        boolean is_active
        datetime created_at
    }

    PREDICTION_REQUESTS {
        int id PK
        string request_id UK
        string request_type
        int batch_size
        string status
        datetime created_at
    }

    PREDICTIONS {
        int id PK
        string request_id FK
        string load_id
        float predicted_rate
        float rate_per_mile
        float confidence_interval_lower
        float confidence_interval_upper
        float base_signal
        float residual
        string model_version
        datetime prediction_timestamp
    }

    PREDICTION_OUTCOMES {
        int id PK
        string load_id UK
        float actual_posted_rate
        datetime recorded_at
    }

    DATA_QUALITY_METRICS {
        int id PK
        string run_id
        string feature_name
        int total_records
        float missing_pct
        float invalid_pct
        string status
        datetime timestamp
    }

    DRIFT_METRICS {
        int id PK
        string run_id
        string feature_name
        string metric_type
        float metric_value
        string status
        datetime timestamp
    }

    MODEL_PERFORMANCE {
        int id PK
        string run_id
        string model_version
        int sample_size
        float rmse
        float mae
        float mape
        float r2
        string segment_name
        datetime timestamp
    }

    PREDICTION_REQUESTS ||--|{ PREDICTIONS : "contains"
    PREDICTIONS }|..|| PREDICTION_OUTCOMES : "matched_by_load_id"
    MODEL_VERSIONS ||--|{ PREDICTIONS : "generates"
```

---

## 7. Operational & Security Architecture

1. **Reverse Proxy Isolation:** All incoming traffic passes through Nginx (`nginx:alpine`). Backend endpoints are exposed via restricted `/api/v1` routes.
2. **Container Security:** Multi-stage Docker builds run non-root execution (`appuser` with UID 10001).
3. **Database Security & Pooling:** Connection pooling managed via SQLAlchemy 2.x (`pool_size=5`, `max_overflow=10`). Database migrations tracked via Alembic scripts.
4. **Resiliency & Health Checks:** Docker Compose health checks enforce container startup dependencies (`pg_isready` for DB, `/api/v1/health` for backend).
