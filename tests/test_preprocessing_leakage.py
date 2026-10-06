import pytest
import pandas as pd  # type: ignore  # pyrefly: ignore
import numpy as np

from src import data_loader, preprocessing, features, validation, target_strategy


def test_fit_preprocessing_stats_only_on_train():
    df_raw = data_loader.load_train_data()
    train_df, val_df = validation.split_oot_data(df_raw, train_cutoff_month=8)

    # Compute stats strictly on train
    train_stats = preprocessing.fit_preprocessing_stats(train_df)

    # Preprocess validation set using training stats
    val_prep, _ = preprocessing.preprocess_data(val_df, stats=train_stats)

    assert "weight_imputed" in val_prep.columns
    assert "market_index_imputed" in val_prep.columns
    assert not val_prep["weight_imputed"].isna().any()
    assert not val_prep["market_index_imputed"].isna().any()


def test_target_strategy_benchmarking():
    df_raw = data_loader.load_train_data()
    # Sample 3,000 rows across time range
    df_sample = df_raw.sample(n=3000, random_state=42).sort_values("date").reset_index(drop=True)
    train_df, val_df = validation.split_oot_data(df_sample, train_cutoff_month=8)

    train_prep, stats = preprocessing.preprocess_data(train_df)
    val_prep, _ = preprocessing.preprocess_data(val_df, stats=stats)

    train_feat = features.extract_features(train_prep)
    val_feat = features.extract_features(val_prep)

    benchmarks = target_strategy.evaluate_target_strategies(
        train_feat, val_feat, features.get_feature_names()
    )

    assert "Direct (posted_rate)" in benchmarks
    assert "Rate-per-mile (posted_rate / distance)" in benchmarks
    assert "Residual (posted_rate - base_signal)" in benchmarks

    for strat, metrics in benchmarks.items():
        assert "rmse" in metrics
        assert "mae" in metrics
        assert "mape" in metrics
        assert "r2" in metrics
