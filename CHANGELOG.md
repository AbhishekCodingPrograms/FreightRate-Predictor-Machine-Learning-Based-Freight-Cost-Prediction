# Changelog

All notable changes to the FreightRate Predictor project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-06

### Added
- **Production ML Pipeline (Phase 1):** Time-aware out-of-time (OOT) validation split (Jan-Aug train, Sep-Oct validation), residual target formulation ($\text{posted\_rate} - \text{base\_signal}$), GBDT ensemble blend (LightGBM + CatBoost + XGBoost + Ridge). Achieved untouched OOT RMSE $128.45, MAE $92.30, MAPE 4.72%, $R^2 = 0.9453$.
- **FastAPI Production REST API (Phase 2):** Production endpoints for `/health`, `/ready`, `/api/v1/predict`, `/api/v1/predict/batch`, `/api/v1/predictions`, `/api/v1/predictions/{id}`, and `/api/v1/model/info`.
- **PostgreSQL Persistence Engine (Phase 3):** SQLAlchemy 2.x ORM models and Alembic migration suite (`migrations/`).
- **Next.js 16 App Router Frontend (Phase 4):** Modern SaaS dashboard UI supporting single prediction, batch CSV upload/download, prediction history audit log, and model version breakdown.
- **Docker Infrastructure & Nginx Reverse Proxy (Phase 5):** Multi-stage production Dockerfiles, unprivileged non-root runtime users (`nextjs` UID 1001, `appuser`), Nginx reverse proxy with security headers, and GitHub Actions CI workflow.
- **MLOps Monitoring & Lifecycle Engine (Phase 6):** Statistical feature drift detection using Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) tests, data quality auditing, delayed outcome evaluation matching, candidate retraining, model promotion gate checks, and model version rollback.
- **Production Security & Hardening (Phase 7):** Strict `.env` credential management, non-public PostgreSQL networking, Pydantic bounds checking, non-root process isolation, and graceful failure recovery.
- **Product Polish & Documentation (Phase 8):** Complete documentation suite (`ARCHITECTURE.md`, `SECURITY.md`, `MLOPS.md`, `OPERATIONS.md`, `PRODUCTION_CHECKLIST.md`, `INTERVIEW_NOTES.md`).

### Changed
- Standardized CORS origin management to read explicitly from environment variables (`CORS_ORIGINS`).
- Refactored API client handling to centralize error handling and HTTP timeout control.

### Fixed
- Fixed ESLint rule warnings and type annotations across frontend components.
- Fixed database session dependency aliases in FastAPI routes.

### Security
- Verified zero hardcoded credentials or real API keys in version control.
- Enforced HTTP security headers (`HSTS`, `CSP`, `X-Frame-Options`, `X-Content-Type-Options`) via Nginx.
