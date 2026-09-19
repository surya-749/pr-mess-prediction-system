"""
Model Evaluation Metrics for Mess Demand Forecasting
Computes MAE, RMSE, R2, MAPE, Potential Waste, and Unmet Demand as defined in PRD Section 12.
"""
from typing import Dict, Any, Union
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def calculate_metrics(y_true: Union[np.ndarray, pd.Series, list], 
                      y_pred: Union[np.ndarray, pd.Series, list]) -> Dict[str, float]:
    """
    Computes standard regression metrics and domain-specific mess metrics:
    - MAE: Mean Absolute Error in student count
    - RMSE: Root Mean Squared Error (penalizes large swings)
    - R2: Variance explained
    - MAPE: Mean Absolute Percentage Error
    - Total Waste: sum(max(y_pred - y_true, 0)) in student meal equivalents
    - Total Unmet Demand: sum(max(y_true - y_pred, 0)) in student meal equivalents
    - Waste Rate (%): total waste / total true attendance * 100
    - Unmet Demand Rate (%): total unmet demand / total true attendance * 100
    """
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)

    if len(y_true_arr) == 0:
        return {
            "mae": 0.0,
            "rmse": 0.0,
            "r2": 0.0,
            "mape": 0.0,
            "total_waste": 0.0,
            "total_unmet_demand": 0.0,
            "waste_rate_pct": 0.0,
            "unmet_rate_pct": 0.0,
            "sample_count": 0
        }

    mae = float(mean_absolute_error(y_true_arr, y_pred_arr))
    rmse = float(np.sqrt(mean_squared_error(y_true_arr, y_pred_arr)))
    
    # R2 can be negative if model is worse than mean baseline
    r2 = float(r2_score(y_true_arr, y_pred_arr)) if len(y_true_arr) > 1 else 1.0

    # Avoid division by zero in MAPE
    non_zero_mask = y_true_arr > 0
    if np.any(non_zero_mask):
        mape = float(np.mean(np.abs(y_true_arr[non_zero_mask] - y_pred_arr[non_zero_mask]) / y_true_arr[non_zero_mask])) * 100.0
    else:
        mape = 0.0

    # Domain specific food demand metrics:
    # Overprediction -> excess food prepared -> potential food waste
    waste = np.maximum(y_pred_arr - y_true_arr, 0)
    # Underprediction -> insufficient food -> unmet student demand
    unmet = np.maximum(y_true_arr - y_pred_arr, 0)

    total_actual = float(np.sum(y_true_arr))
    total_waste = float(np.sum(waste))
    total_unmet = float(np.sum(unmet))

    waste_rate = (total_waste / total_actual * 100.0) if total_actual > 0 else 0.0
    unmet_rate = (total_unmet / total_actual * 100.0) if total_actual > 0 else 0.0

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 4),
        "mape": round(mape, 2),
        "total_waste": round(total_waste, 1),
        "total_unmet_demand": round(total_unmet, 1),
        "waste_rate_pct": round(waste_rate, 2),
        "unmet_rate_pct": round(unmet_rate, 2),
        "sample_count": int(len(y_true_arr))
    }
