# Production Operations & Runbook Document

## 1. Routine Deployment
```bash
# Pull latest repository release
git pull origin main

# Build and start services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## 2. Model Retraining & Candidate Registration
```bash
python scripts/retrain.py freight-rate-v1.2.0
```

## 3. Model Promotion Gate Check
```bash
python scripts/promote_model.py freight-rate-v1.2.0
```

## 4. Emergency Model Rollback
```bash
python scripts/rollback_model.py freight-rate-v1.0.0
```

## 5. Ingesting Delayed Actual Outcomes
```bash
python scripts/ingest_outcomes.py data/validation.csv
```

## 6. Running Manual Offline Monitoring Cycle
```bash
python scripts/run_monitoring.py
```

## 7. Database Backup & Restoration
Backup:
```bash
docker exec -t freight_rate_db pg_dump -U postgres freight_db > backup_$(date +%Y%m%d).sql
```
Restore:
```bash
cat backup_20261006.sql | docker exec -i freight_rate_db psql -U postgres -d freight_db
```
