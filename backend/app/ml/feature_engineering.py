"""
Feature Engineering Engine
Transforms raw mess attendance and context records into temporal, academic, calendar,
and menu features while strictly preventing future data leakage.
(PRD Section 6)
"""
from typing import Tuple, List, Optional
import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    # Temporal lag features
    "attendance_lag_1",
    "attendance_lag_2",
    "attendance_lag_3",
    "attendance_lag_7",
    # Rolling window features
    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_mean_30",
    # Calendar features
    "day_of_week",
    "month",
    "is_weekend",
    "is_holiday",
    # Academic context features
    "is_cat1",
    "is_cat2",
    "is_fat",
    "is_exam",
    "days_to_exam",
    "days_after_exam",
    # Meal & Menu features
    "meal_type_code",
    "dish_category_code",
    "is_special_dish",
    "historical_menu_popularity",
    # Population features
    "expected_students",
    "expected_class_attendance"
]

MEAL_TYPE_MAP = {
    "breakfast": 0,
    "lunch": 1,
    "snacks": 2,
    "dinner": 3
}

DISH_CATEGORY_MAP = {
    "South Indian": 0,
    "North Indian": 1,
    "Special": 2,
    "Snack": 3,
    "Light": 4,
    "Indo-Chinese": 5,
    "Other": 6
}


def compute_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes lag and rolling window features strictly per meal_type.
    Uses shift(1) or higher to guarantee zero future leakage.
    """
    df = df.copy()
    
    # Ensure datetime parsing and chronological sorting
    if "date" in df.columns:
        df["datetime"] = pd.to_datetime(df["date"])
    
    df["meal_order"] = df["meal_type"].map(MEAL_TYPE_MAP).fillna(0).astype(int)
    df = df.sort_values(by=["datetime", "meal_order"]).reset_index(drop=True)

    # Calculate month and day of week if not present
    df["month"] = df["datetime"].dt.month
    if "day_of_week" not in df.columns:
        df["day_of_week"] = df["datetime"].dt.weekday

    # Group by meal_type to compute lags per specific meal
    grouped = df.groupby("meal_type", group_keys=False)

    # Shift(1) guarantees that row t only sees row t-1 (yesterday's meal)
    df["attendance_lag_1"] = grouped["actual_attendance"].shift(1)
    df["attendance_lag_2"] = grouped["actual_attendance"].shift(2)
    df["attendance_lag_3"] = grouped["actual_attendance"].shift(3)
    df["attendance_lag_7"] = grouped["actual_attendance"].shift(7)

    # Rolling means strictly on past values: shift(1).rolling(w)
    df["rolling_mean_7"] = grouped["actual_attendance"].apply(
        lambda s: s.shift(1).rolling(window=7, min_periods=1).mean()
    )
    df["rolling_mean_14"] = grouped["actual_attendance"].apply(
        lambda s: s.shift(1).rolling(window=14, min_periods=1).mean()
    )
    df["rolling_mean_30"] = grouped["actual_attendance"].apply(
        lambda s: s.shift(1).rolling(window=30, min_periods=1).mean()
    )

    # For any initial rows where lags are NaN, backfill with rolling mean or expected * base ratio
    default_attendance = df["expected_students"] * 0.75
    df["attendance_lag_1"] = df["attendance_lag_1"].fillna(default_attendance)
    df["attendance_lag_2"] = df["attendance_lag_2"].fillna(df["attendance_lag_1"])
    df["attendance_lag_3"] = df["attendance_lag_3"].fillna(df["attendance_lag_2"])
    df["attendance_lag_7"] = df["attendance_lag_7"].fillna(df["attendance_lag_1"])

    df["rolling_mean_7"] = df["rolling_mean_7"].fillna(df["attendance_lag_1"])
    df["rolling_mean_14"] = df["rolling_mean_14"].fillna(df["rolling_mean_7"])
    df["rolling_mean_30"] = df["rolling_mean_30"].fillna(df["rolling_mean_14"])

    # Categorical encodings
    df["meal_type_code"] = df["meal_type"].map(MEAL_TYPE_MAP).fillna(0).astype(int)
    df["dish_category_code"] = df["dish_category"].map(DISH_CATEGORY_MAP).fillna(6).astype(int)

    return df


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Extracts feature matrix X and target series y for training.
    """
    engineered_df = compute_temporal_features(df)
    
    # Verify all feature columns exist
    for col in FEATURE_COLUMNS:
        if col not in engineered_df.columns:
            engineered_df[col] = 0

    X = engineered_df[FEATURE_COLUMNS]
    y = engineered_df["actual_attendance"]
    return X, y


def build_single_inference_features(
    context: dict,
    historical_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Builds a single-row DataFrame formatted for model prediction.
    If historical_df is provided, lags are accurately pulled from recent past records.
    """
    date_val = pd.to_datetime(context.get("date", "2026-09-20"))
    dow = date_val.weekday()
    month = date_val.month
    meal_type = context.get("meal", context.get("meal_type", "lunch")).lower()
    expected_students = int(context.get("expected_students", 1500))

    # Determine lags from recent history if available
    lag_1 = None
    lag_2 = None
    lag_3 = None
    lag_7 = None
    rm_7 = None
    rm_14 = None
    rm_30 = None

    if historical_df is not None and len(historical_df) > 0:
        meal_hist = historical_df[historical_df["meal_type"] == meal_type].sort_values(by="date")
        if len(meal_hist) >= 1:
            recent_vals = meal_hist["actual_attendance"].tolist()
            lag_1 = recent_vals[-1]
            lag_2 = recent_vals[-2] if len(recent_vals) >= 2 else lag_1
            lag_3 = recent_vals[-3] if len(recent_vals) >= 3 else lag_2
            lag_7 = recent_vals[-7] if len(recent_vals) >= 7 else lag_1
            rm_7 = float(np.mean(recent_vals[-7:]))
            rm_14 = float(np.mean(recent_vals[-14:]))
            rm_30 = float(np.mean(recent_vals[-30:]))

    base_ratio = 0.82 if meal_type == "lunch" else (0.78 if meal_type == "dinner" else 0.68)
    if lag_1 is None:
        lag_1 = expected_students * base_ratio
        lag_2 = lag_1
        lag_3 = lag_1
        lag_7 = lag_1
        rm_7 = lag_1
        rm_14 = lag_1
        rm_30 = lag_1

    dish_cat = context.get("dish_category", "Special" if "biryani" in context.get("menu", "").lower() or "paneer" in context.get("menu", "").lower() else "North Indian")
    is_special = 1 if ("special" in dish_cat.lower() or "biryani" in context.get("menu", "").lower() or "paneer" in context.get("menu", "").lower()) else int(context.get("is_special_dish", 0))
    popularity = float(context.get("historical_menu_popularity", 1.15 if is_special else 1.0))

    row = {
        "attendance_lag_1": float(context.get("attendance_lag_1", lag_1)),
        "attendance_lag_2": float(context.get("attendance_lag_2", lag_2)),
        "attendance_lag_3": float(context.get("attendance_lag_3", lag_3)),
        "attendance_lag_7": float(context.get("attendance_lag_7", lag_7)),
        "rolling_mean_7": float(context.get("rolling_mean_7", rm_7)),
        "rolling_mean_14": float(context.get("rolling_mean_14", rm_14)),
        "rolling_mean_30": float(context.get("rolling_mean_30", rm_30)),
        "day_of_week": int(dow),
        "month": int(month),
        "is_weekend": int(dow in (5, 6)),
        "is_holiday": int(context.get("is_holiday", False)),
        "is_cat1": int(context.get("is_cat1", False)),
        "is_cat2": int(context.get("is_cat2", False)),
        "is_fat": int(context.get("is_fat", False)),
        "is_exam": int(context.get("is_exam", context.get("is_cat1", False) or context.get("is_cat2", False) or context.get("is_fat", False))),
        "days_to_exam": int(context.get("days_to_exam", 0 if context.get("is_exam") else 14)),
        "days_after_exam": int(context.get("days_after_exam", 0)),
        "meal_type_code": MEAL_TYPE_MAP.get(meal_type, 1),
        "dish_category_code": DISH_CATEGORY_MAP.get(dish_cat, 1),
        "is_special_dish": is_special,
        "historical_menu_popularity": popularity,
        "expected_students": expected_students,
        "expected_class_attendance": int(context.get("expected_class_attendance", int(expected_students * 0.90)))
    }

    return pd.DataFrame([row])[FEATURE_COLUMNS]
