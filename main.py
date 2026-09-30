import sys
import shutil
import subprocess
from pathlib import Path

# Add project root directory to path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src import config, train, predict, evaluate, data_loader, preprocessing, features


def run_scorer():
    print("\nRunning score.py verification...")
    score_script = BASE_DIR / "score.py"
    val_preds = config.BASE_DIR / "validation_predictions.csv"
    dec_preds = config.DATA_DIR / "december_chart_inputs.csv"

    cmd = [
        sys.executable,
        str(score_script),
        "--predictions",
        str(val_preds),
        "--december-predictions",
        str(dec_preds),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print("Scorer failed:", res.stderr)
        raise RuntimeError("Scorer verification failed")

    # Copy generated chart to outputs directory
    scorer_chart = BASE_DIR / "scorer_results" / "candidate_december.png"
    if scorer_chart.exists():
        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy(scorer_chart, config.CANDIDATE_CHART_PATH)
        print(f"Saved chart to {config.CANDIDATE_CHART_PATH}")


def main():
    print("Starting Freight Rate Predictor Pipeline\n")

    # 1. Train Model
    final_ensemble, stats, oot_metrics = train.run_training_pipeline()

    # 2. Evaluate Full Dataset Performance
    df_raw = data_loader.load_train_data()
    df_prep, _ = preprocessing.preprocess_data(df_raw, stats)
    df_feat = features.extract_features(df_prep)

    eval_summary = evaluate.evaluate_model_performance(final_ensemble, df_feat)
    evaluate.print_evaluation_report(eval_summary)

    # 3. Predict Validation & December Sets
    val_df, dec_df = predict.run_prediction_pipeline(final_ensemble, stats)

    # 4. Run Scorer Verification
    run_scorer()

    print("\nFreight Rate Prediction Pipeline Finished Successfully!")


if __name__ == "__main__":
    main()
