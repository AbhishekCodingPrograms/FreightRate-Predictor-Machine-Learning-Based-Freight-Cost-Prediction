# FreightRate Predictor - Enterprise Machine Learning & Spot Rate SaaS Platform

Production-grade Machine Learning pipeline, FastAPI REST API, PostgreSQL persistence engine, and modern Next.js App Router frontend for spot freight rate forecasting (`posted_rate`).

Built with **Next.js 16 (App Router)**, **TypeScript**, **Tailwind CSS**, **FastAPI**, **PostgreSQL**, **SQLAlchemy 2.x**, **Alembic**, **LightGBM**, **CatBoost**, **XGBoost**, **Docker**, **Nginx**, and **GitHub Actions**.

---

## Live Deployments

- **Frontend Application:** [https://freight-rate-predictor-machine-learning-based-freigh-4wexasm1i.vercel.app](https://freight-rate-predictor-machine-learning-based-freigh-4wexasm1i.vercel.app)
- **Backend API Service:** [https://freightrate-predictor-backend.onrender.com](https://freightrate-predictor-backend.onrender.com)
- **Interactive API Documentation:** [https://freightrate-predictor-backend.onrender.com/docs](https://freightrate-predictor-backend.onrender.com/docs)
- **Health Check Endpoint:** [https://freightrate-predictor-backend.onrender.com/api/v1/health](https://freightrate-predictor-backend.onrender.com/api/v1/health)

---

## Architecture & Directory Layout

```text
freight-rate-predictor/
├── frontend/                       # Next.js App Router Frontend
│   ├── app/                        # App Router Pages (/, /predict, /batch, /history, /models, /monitoring)
│   ├── components/                 # UI, Layout, Form, Table, and Modal Components
│   ├── lib/                        # Typed API Client, TypeScript Interfaces, Utilities
│   ├── public/                     # Static Assets
│   ├── Dockerfile                  # Multi-Stage Production Frontend Dockerfile
│   ├── package.json                # Dependencies & Scripts
│   └── tsconfig.json               # TypeScript Configuration
│
├── app/                            # FastAPI Application
│   ├── main.py                     # FastAPI setup, middleware, CORS, lifespan, routes
│   ├── config.py                   # Pydantic Settings & environment configuration
│   ├── dependencies.py             # Dependency injection container
│   ├── core/                       # Logger, Middleware, Exceptions
│   ├── db/                         # Database engine, SQLAlchemy 2.x models, repositories
│   ├── schemas/                    # Pydantic validation request & response schemas
│   ├── services/                   # Model artifact lifecycle & prediction engine
│   └── api/v1/                     # Health, Prediction, and Model endpoints
│
├── nginx/                          # Reverse Proxy Configuration
│   └── nginx.conf                  # Nginx routing (/ -> Frontend, /api/ -> Backend, Security Headers)
│
├── docs/                           # Documentation & Verification Guides
│   └── PRODUCTION_CHECKLIST.md     # Production Gate & Infrastructure Verification Checklist
│
├── migrations/                     # Alembic Database Schema Migrations
│   ├── env.py                      # Migration environment configuration
│   └── versions/                   # Versioned schema migration files
│
├── artifacts/                      # Serialized ML Artifacts
│   ├── freight_rate_model.joblib   # Trained ensemble model & scaler pipeline
│   └── model_metadata.json         # Feature definitions and validation metrics
│
├── data/                           # Datasets
│   ├── train-test.csv              # Historical load records (48,000 rows)
│   ├── validation.csv              # Target validation loads (12,000 rows)
│   └── december-chart-inputs.csv   # December forecast inputs
│
├── scripts/
│   ├── benchmark_api.py            # API latency & throughput benchmark script
│   └── smoke_test.py               # Automated end-to-end production smoke test
│
├── .github/workflows/              # CI/CD Pipelines
│   ├── ci.yml                      # Unified Pytest, Frontend Lint/Build & Docker CI
│   └── deploy.yml                  # Deployment pipeline template
│
├── Dockerfile                      # Backend FastAPI Multi-stage Dockerfile
├── docker-compose.yml              # Multi-Container Orchestrator
├── docker-compose.prod.yml         # Production Container Overrides
├── .env.example                    # Environment variable template
├── score.py                        # ML December Immutability & Evaluation benchmark
├── main.py                         # ML pipeline assessment wrapper
└── pyproject.toml / requirements.txt
```

---

## System Architecture

```text
                    INTERNET / CLIENT
                           │
                           ▼
                  Nginx Reverse Proxy
                (Port 80 / 443, SSL/TLS)
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
Next.js App Router                  FastAPI REST API
 (Frontend Container)              (Backend Container)
         │                                   │
         │ HTTP API                          ├──────────────────┐
         └─────────────────────────►         ▼                  ▼
                                     ML Artifacts         PostgreSQL
                                     (.joblib)            (Database Container)
```

---

## Database Architecture & Schema

### Technology Stack
- **Database Engine:** PostgreSQL 16 (SQLite supported for testing)
- **ORM & Repository Layer:** SQLAlchemy 2.x declarative models with repository pattern
- **Database Migrations:** Alembic schema versioning

### Schema Overview
1. **`model_versions`**: Persistent registry of deployed ML models and validation metrics.
2. **`prediction_requests`**: Operational audit log for single and batch predictions.
3. **`predictions`**: Individual load predictions, confidence intervals, and sanitized input payloads.

---

## Quick Start & Local Development

### 1. Local Python & Next.js Development

#### Backend Setup:
```bash
# Install Python dependencies
pip install -r requirements.txt

# Execute database migrations
alembic upgrade head

# Launch FastAPI backend server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```

### 2. Docker Compose Orchestration
Spin up the complete multi-container architecture (PostgreSQL, FastAPI, Next.js, Nginx):
```bash
docker compose up --build
```
Access endpoints:
- Web Dashboard: `http://localhost`
- API Documentation: `http://localhost/api/v1/docs` or `http://localhost:8000/docs`
- Health Probe: `http://localhost/health`

---

## Testing & Quality Gate Commands

Run complete backend test suite (41 tests):
```bash
pytest tests/
```

Run frontend linting & production build validation:
```bash
cd frontend
npm run lint
npm run build
```

Run automated end-to-end production smoke test:
```bash
python scripts/smoke_test.py
```

Run ML assessment and evaluation benchmark:
```bash
python main.py
python score.py --predictions validation_predictions.csv --december-predictions data/december-chart-inputs.csv
```

---

## Security, Secret Management & Production Hardening

1. **Zero Secret Exposure:** Credentials are read strictly from environment variables (`.env`). Secret files are excluded via `.gitignore`.
2. **Network Isolation:** In production (`docker-compose.prod.yml`), database ports are restricted to internal Docker networks.
3. **CORS Governance:** Production environment restricts allowed origins (`CORS_ORIGINS`) to authorized domains. Wildcards are disabled in production.
4. **Security Headers:** Nginx enforces HSTS, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, and Content-Security-Policy.
5. **Non-Root Containers:** Backend and Frontend Docker containers execute under unprivileged dedicated system users (`appuser` and `nextjs`).

---

## Backup & Disaster Recovery Strategy

1. **Database Backup:**
   ```bash
   docker exec -t freight_rate_db pg_dump -U postgres freight_db > backup_$(date +%Y%m%d_%H%M%S).sql
   ```
2. **Database Restoration:**
   ```bash
   cat backup_20261006.sql | docker exec -i freight_rate_db psql -U postgres -d freight_db
   ```
3. **Model Artifact Deployment & Rollback:**
   Model artifacts are versioned in `artifacts/`. Rollbacks are executed by updating `MODEL_ARTIFACT_PATH` in `.env` without mutating database audit logs.
