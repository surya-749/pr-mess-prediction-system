import pytest
import pandas as pd
import numpy as np
from app.ml.feature_engineering import compute_temporal_features, prepare_features, build_single_inference_features
from app.ml.data_generator import generate_college_mess_dataset


def test_temporal_features_no_future_leakage():
    """
    CRITICAL REQUIREMENT (PRD Section 6):
    Verify that row t's features NEVER depend on row t's actual attendance.
    """
    df = generate_college_mess_dataset(num_days=30, base_population=1500, seed=123)
    df_engineered = compute_temporal_features(df)

    lunch_rows = df_engineered[df_engineered["meal_type"] == "lunch"].reset_index(drop=True)

    # For day index i >= 1, lag_1 MUST equal day i - 1 actual_attendance
    for i in range(1, len(lunch_rows)):
        prev_actual = lunch_rows.loc[i - 1, "actual_attendance"]
        current_lag1 = lunch_rows.loc[i, "attendance_lag_1"]
        assert current_lag1 == prev_actual, f"Lag 1 mismatch at row {i}: got {current_lag1}, expected {prev_actual}"

    # For day index i >= 7, lag_7 MUST equal day i - 7 actual_attendance
    for i in range(7, len(lunch_rows)):
        past_actual_7 = lunch_rows.loc[i - 7, "actual_attendance"]
        current_lag7 = lunch_rows.loc[i, "attendance_lag_7"]
        assert current_lag7 == past_actual_7, f"Lag 7 mismatch at row {i}: got {current_lag7}, expected {past_actual_7}"


def test_rolling_mean_strictly_historical():
    """
    Verify that rolling_mean_7 on row t is computed only over rows t-1 down to t-7,
    excluding row t.
    """
    df = generate_college_mess_dataset(num_days=20, base_population=1500, seed=99)
    df_engineered = compute_temporal_features(df)
    dinner_rows = df_engineered[df_engineered["meal_type"] == "dinner"].reset_index(drop=True)

    for i in range(7, len(dinner_rows)):
        expected_window = dinner_rows.loc[i - 7:i - 1, "actual_attendance"]
        expected_mean = float(expected_window.mean())
        computed_rm7 = float(dinner_rows.loc[i, "rolling_mean_7"])
        assert abs(computed_rm7 - expected_mean) < 1e-4, f"Rolling mean 7 mismatch at index {i}"


def test_inference_feature_builder():
    """
    Verify inference feature vector generation contains all required columns without NaNs.
    """
    context = {
        "date": "2026-09-20",
        "meal": "lunch",
        "menu": "Chicken Biryani / Paneer Biryani",
        "dish_category": "Special",
        "is_holiday": False,
        "is_exam": True,
        "expected_students": 1500
    }
    single_df = build_single_inference_features(context)
    assert len(single_df) == 1
    assert not single_df.isna().any().any(), "Inference row contains NaN values!"
    assert single_df["is_exam"].values[0] == 1
    assert single_df["expected_students"].values[0] == 1500
