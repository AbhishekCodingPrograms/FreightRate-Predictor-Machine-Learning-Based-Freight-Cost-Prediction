import pytest
import pandas as pd  # type: ignore  # pyrefly: ignore
import hashlib
from src import config, predict, artifact


def get_file_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def test_december_input_immutability():
    dec_input_path = config.DECEMBER_INPUT_PATH
    if not dec_input_path.exists():
        dec_input_path = config.BASE_DIR / "december-chart-inputs.csv"

    initial_hash = get_file_hash(dec_input_path)

    # Run prediction pipeline
    predict.run_prediction_pipeline()

    final_hash = get_file_hash(dec_input_path)
    assert initial_hash == final_hash, "data/december-chart-inputs.csv was modified!"
