import numpy as np
import pandas as pd
from typing import Dict, List
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from xgboost import XGBRegressor

from src import config


class FreightRateEnsemble:
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {"lgbm": 0.4, "catboost": 0.4, "xgboost": 0.2}

        self.lgbm = LGBMRegressor(**config.LGBM_PARAMS)
        self.catboost = CatBoostRegressor(**config.CATBOOST_PARAMS)
        self.xgboost = XGBRegressor(**config.XGBOOST_PARAMS)

        self.fitted = False

    def fit(self, X: pd.DataFrame, y_residual: pd.Series):
        self.lgbm.fit(X, y_residual)
        self.catboost.fit(X, y_residual)
        self.xgboost.fit(X, y_residual)
        self.fitted = True
        return self

    def predict(self, X: pd.DataFrame, base_signal: pd.Series) -> np.ndarray:
        if not self.fitted:
            raise RuntimeError("Model ensemble must be fitted before predict()")

        res_lgb = self.lgbm.predict(X)
        res_cat = self.catboost.predict(X)
        res_xgb = self.xgboost.predict(X)

        ensemble_res = (
            self.weights["lgbm"] * res_lgb
            + self.weights["catboost"] * res_cat
            + self.weights["xgboost"] * res_xgb
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
