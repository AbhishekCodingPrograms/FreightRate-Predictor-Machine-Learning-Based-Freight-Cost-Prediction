# Technical Deep-Dive & Interview Preparation Notes

### Q1: Why did you frame freight rate prediction as a residual model ($\text{posted\_rate} - \text{base\_signal}$)?
**Answer:** Spot freight rates exhibit strong linear baseline scaling with shipment distance ($\text{base\_signal} = \text{distance} \times \text{median\_rpm}$). By predicting the residual component ($\text{Residual} = \text{posted\_rate} - \text{base\_signal}$), the gradient boosted decision trees (LightGBM, CatBoost, XGBoost) focus entirely on non-linear market multipliers, equipment surcharges, weight scaling, and geographic dynamics, reducing variance and improving out-of-time $R^2$ to $0.9453$.

### Q2: Why use an ensemble of LightGBM, CatBoost, and XGBoost?
**Answer:** Each GBDT engine handles tabular data nuances differently:
- **CatBoost:** Superior categorical handling for origin/destination regional clusters.
- **LightGBM:** Fast leaf-wise tree growth capturing high-order feature interactions.
- **XGBoost:** Precise depth-wise regularization.
Blending them with constrained scipy optimization ($\text{LightGBM}: 0.35, \text{CatBoost}: 0.45, \text{XGBoost}: 0.15, \text{Ridge}: 0.05$) yielded lower out-of-time RMSE ($128.45) than any single model alone.

### Q3: How did you ensure time-aware validation and zero data leakage?
**Answer:** Loads were split strictly chronologically: Jan–Aug (38,477 loads) for training, and Sep–Oct (9,523 loads) for untouched validation. Target encoding and scaling statistics were computed exclusively on the training split and applied to validation data via immutable transformer state.

### Q4: Why use PostgreSQL with SQLAlchemy 2.x and Alembic?
**Answer:** Spot rate prediction requires transactional audit trails for batch quotes and model performance tracking. SQLAlchemy 2.x declarative ORM with repository patterns provides atomic unit-of-work transactions. Alembic provides deterministic database schema versioning.

### Q5: How is statistical feature drift detected in production?
**Answer:** We calculate Population Stability Index (PSI) and 2-sample Kolmogorov-Smirnov (KS) tests comparing live prediction input features against the baseline training distribution (`data/train-test.csv`). Features with $\text{PSI} \ge 0.25$ trigger `CRITICAL` alerts.

### Q6: Does feature drift automatically deploy a retrained model?
**Answer:** No. Drift is a signal, not proof of model superiority. Retraining creates a model registered as `candidate`. It must pass an automated validation gate comparing candidate OOT MAPE against active production MAPE before an engineer or automated approval can promote it (`python scripts/promote_model.py`).
