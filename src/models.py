import numpy as np
import pandas as pd  # type: ignore  # pyrefly: ignore
from typing import Dict, List, Optional

from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from xgboost import XGBRegressor
from sklearn.ensemble import HistGradientBoostingRegressor

from src import config


class FreightRateEnsemble:
    def __init__(self, weights: Optional[Dict[str, float]] = None):

        self.weights = weights or {"hgb": 0.50, "lgbm": 0.25, "catboost": 0.15, "xgboost": 0.10}

        self.hgb = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_depth=10, random_state=42)
        self.lgbm = LGBMRegressor(**config.LGBM_PARAMS)
        self.catboost = CatBoostRegressor(**config.CATBOOST_PARAMS)
        self.xgboost = XGBRegressor(**config.XGBOOST_PARAMS)

        self.fitted = False

    def fit(self, X: pd.DataFrame, y_residual: pd.Series):
        self.hgb.fit(X, y_residual)
        self.lgbm.fit(X, y_residual)
        self.catboost.fit(X, y_residual)
        self.xgboost.fit(X, y_residual)
        self.fitted = True
        return self

    def predict(self, X: pd.DataFrame, base_signal: pd.Series) -> np.ndarray:
        if not self.fitted:
            raise RuntimeError("Model ensemble must be fitted before predict()")

        res_hgb = self.hgb.predict(X)
        res_lgb = self.lgbm.predict(X)
        res_cat = self.catboost.predict(X)
        res_xgb = self.xgboost.predict(X)

        w_hgb = self.weights.get("hgb", 0.50)
        w_lgb = self.weights.get("lgbm", 0.25)
        w_cat = self.weights.get("catboost", 0.15)
        w_xgb = self.weights.get("xgboost", 0.10)

        ensemble_res = (
            w_hgb * res_hgb
            + w_lgb * res_lgb
            + w_cat * res_cat
            + w_xgb * res_xgb
        )

        final_preds = base_signal.values + ensemble_res
        return np.maximum(final_preds, 10.0)

    def get_feature_importances(self, feature_names: List[str]) -> pd.DataFrame:
        lgb_imp = self.lgbm.feature_importances_ / (self.lgbm.feature_importances_.sum() + 1e-5)
        cat_imp = self.catboost.get_feature_importance() / (self.catboost.get_feature_importance().sum() + 1e-5)
        xgb_imp = self.xgboost.feature_importances_ / (self.xgboost.feature_importances_.sum() + 1e-5)

        avg_imp = (
            self.weights["lgbm"] * lgb_imp
            + self.weights["catboost"] * cat_imp
            + self.weights["xgboost"] * xgb_imp
        )

        return pd.DataFrame({
            "feature": feature_names,
            "importance": avg_imp,
            "lgb_importance": lgb_imp,
            "cat_importance": cat_imp,
            "xgb_importance": xgb_imp,
        }).sort_values("importance", ascending=False).reset_index(drop=True)
