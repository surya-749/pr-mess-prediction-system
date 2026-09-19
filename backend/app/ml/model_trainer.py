"""
Random Forest Model Training & Tuning Pipeline
Implements:
- Chronological TimeSeriesSplit cross validation
- Hyperparameter tuning for Random Forest Regressor
- Prediction interval estimation via tree ensemble variance
- Feature importance analysis
(PRD Sections 4, 7, 8, 9, 15)
"""
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV

from app.ml.feature_engineering import prepare_features, FEATURE_COLUMNS
from app.ml.metrics import calculate_metrics


class ModelTrainer:
    def __init__(self):
        self.feature_names = FEATURE_COLUMNS

    def train_and_tune(
        self,
        df: pd.DataFrame,
        tune_hyperparameters: bool = True,
        test_size_ratio: float = 0.20,
        n_iter_search: int = 8,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Trains Random Forest Regressor with strict chronological split and rolling-window validation.
        """
        # Step 1: Feature Engineering
        X, y = prepare_features(df)
        n_samples = len(X)
        split_idx = int(n_samples * (1.0 - test_size_ratio))

        # Strict chronological train / test split
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        best_params = {
            "n_estimators": 150,
            "max_depth": 14,
            "max_features": "sqrt",
            "min_samples_split": 4,
            "min_samples_leaf": 2,
            "random_state": random_state,
            "n_jobs": 1
        }

        if tune_hyperparameters and len(X_train) >= 100:
            # Chronological Rolling-window TimeSeriesSplit
            tscv = TimeSeriesSplit(n_splits=3)
            param_dist = {
                "n_estimators": [100, 150, 200],
                "max_depth": [8, 12, 16, None],
                "max_features": ["sqrt", 0.5, 0.8],
                "min_samples_split": [2, 4],
                "min_samples_leaf": [1, 2]
            }
            rf_base = RandomForestRegressor(random_state=random_state, n_jobs=1)
            search = RandomizedSearchCV(
                estimator=rf_base,
                param_distributions=param_dist,
                n_iter=n_iter_search,
                cv=tscv,
                scoring="neg_mean_absolute_error",
                random_state=random_state,
                n_jobs=1
            )
            search.fit(X_train, y_train)
            best_params = {**search.best_params_, "random_state": random_state, "n_jobs": 1}

        # Train final model on X_train with best hyperparameters
        final_model = RandomForestRegressor(**best_params)
        final_model.fit(X_train, y_train)

        # Evaluate on chronological holdout test set
        y_test_pred = final_model.predict(X_test)
        metrics = calculate_metrics(y_test.values, y_test_pred)

        # Compute feature importances
        importances = final_model.feature_importances_
        feature_importance_list = [
            {"feature": col, "importance": round(float(imp), 4), "percentage": round(float(imp) * 100, 2)}
            for col, imp in sorted(zip(self.feature_names, importances), key=lambda x: x[1], reverse=True)
        ]

        # Detailed test predictions for actual vs predicted visualization
        eval_df = df.iloc[split_idx:].copy()
        eval_df["predicted_attendance"] = np.round(y_test_pred).astype(int)
        eval_df["prediction_error"] = eval_df["predicted_attendance"] - eval_df["actual_attendance"]
        eval_records = eval_df[[
            "date", "meal_type", "menu_name", "is_exam", "is_holiday",
            "actual_attendance", "predicted_attendance", "prediction_error"
        ]].to_dict(orient="records")

        return {
            "model": final_model,
            "best_params": best_params,
            "metrics": metrics,
            "feature_importances": feature_importance_list,
            "eval_records": eval_records,
            "train_sample_count": len(X_train),
            "test_sample_count": len(X_test)
        }

    @staticmethod
    def predict_with_interval(
        model: RandomForestRegressor,
        X_single: pd.DataFrame,
        confidence_factor: float = 1.96
    ) -> Tuple[int, int, int]:
        """
        Predicts attendance along with prediction interval [range_low, range_high]
        using variance across individual decision trees in the forest.
        """
        # Collect predictions from all trees in the ensemble
        X_mat = np.asarray(X_single, dtype=float)
        tree_preds = np.array([tree.predict(X_mat)[0] for tree in model.estimators_])
        mean_pred = float(np.mean(tree_preds))
        std_pred = float(np.std(tree_preds))

        # Prediction interval
        low = int(max(0, np.round(mean_pred - (confidence_factor * std_pred))))
        high = int(np.round(mean_pred + (confidence_factor * std_pred)))
        point_prediction = int(np.round(mean_pred))

        return point_prediction, low, high
