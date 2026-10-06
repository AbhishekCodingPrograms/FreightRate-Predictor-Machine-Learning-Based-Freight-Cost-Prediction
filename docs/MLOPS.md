# MLOps Lifecycle, Monitoring & Model Registry Document

## 1. Model Lifecycle States
- **`candidate`**: Newly trained model registered with immutable metadata. Cannot serve production inference until promoted.
- **`approved`**: Candidate model that passed automated validation gates.
- **`production`**: Active production model serving live prediction requests.
- **`archived`**: Superseded model versions preserved for audit traceability.
- **`rejected`**: Candidate models that failed validation gates during comparison.

## 2. Statistical Feature Drift Detection
- **Population Stability Index (PSI):**
  - $\text{PSI} < 0.10$: `NORMAL`
  - $0.10 \le \text{PSI} < 0.25$: `WARNING`
  - $\text{PSI} \ge 0.25$: `CRITICAL`
- **Kolmogorov-Smirnov (KS) Test:** 2-sample KS test comparing live sample against baseline dataset (`data/train-test.csv`).

## 3. Controlled Retraining & Promotion Policy
- Retraining does **NOT** automatically deploy models to production.
- Candidate models are registered in status `candidate`.
- Candidate must beat or equal active production validation MAPE before promotion (`python scripts/promote_model.py <version>`).

## 4. Model Rollback
- Production model can be rolled back on demand:
  ```bash
  python scripts/rollback_model.py <target_version>
  ```
- Historical predictions retain their original `model_version` tag for audit traceability.
