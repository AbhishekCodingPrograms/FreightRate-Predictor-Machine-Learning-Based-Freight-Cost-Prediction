from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
REPORTS_DIR = BASE_DIR / "reports"

TRAIN_PATH = DATA_DIR / "train-test.csv"
VAL_PATH = DATA_DIR / "validation.csv"
VAL_TEMPLATE_PATH = DATA_DIR / "validation-predictions-template.csv"
DECEMBER_INPUT_PATH = DATA_DIR / "december-chart-inputs.csv"

VAL_PREDS_PATH = OUTPUT_DIR / "validation_predictions.csv"
DECEMBER_PREDS_PATH = OUTPUT_DIR / "december_predictions.csv"
CANDIDATE_CHART_PATH = OUTPUT_DIR / "candidate_december.png"
REPORT_PDF_PATH = REPORTS_DIR / "freight_rate_report.pdf"

SEED = 42

# Columns
ID_COL = "load_id"
TARGET_COL = "posted_rate"
DATE_COL = "date"

# Model hyperparameters
LGBM_PARAMS = {
    "n_estimators": 1200,
    "learning_rate": 0.025,
    "max_depth": 8,
    "num_leaves": 63,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": SEED,
    "verbose": -1,
}

CATBOOST_PARAMS = {
    "iterations": 1200,
    "learning_rate": 0.025,
    "depth": 6,
    "random_seed": SEED,
    "verbose": 0,
}

XGBOOST_PARAMS = {
    "n_estimators": 1000,
    "learning_rate": 0.025,
    "max_depth": 6,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": SEED,
}
