from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import pandas as pd

from app.core.database import get_db
from app.models.schemas import (
    PredictRequest, PredictResponse,
    FeedbackCreate, FeedbackResponse,
    FoodRequirementResponse, FeatureImportanceItem,
    EvaluationResponse, ModelStatusResponse,
    AttendanceORM, PredictionORM, FeedbackORM
)
from app.api.deps import registry, food_calc, drift_detector
from app.ml.data_generator import generate_college_mess_dataset
from app.ml.feature_engineering import build_single_inference_features
from app.ml.model_trainer import ModelTrainer


router = APIRouter()
trainer = ModelTrainer()


@router.post("/seed-data", summary="Generate multi-semester dataset and train baseline model")
def seed_data(
    num_days: int = Query(default=300, description="Number of days to generate"),
    db: Session = Depends(get_db)
):
    """
    Seeds the database with realistic college mess attendance data spanning CAT-1, CAT-2, FAT,
    and trains the initial Random Forest model (RF-v1.0).
    """
    # 1. Clear existing raw attendance records if any
    db.query(AttendanceORM).delete()
    db.commit()

    # 2. Generate synthetic college mess dataset
    df = generate_college_mess_dataset(num_days=num_days)

    # 3. Store in DB
    records_to_insert = [
        AttendanceORM(
            date=row["date"],
            day_index=row["day_index"],
            semester=row["semester"],
            academic_week=row["academic_week"],
            day_of_week=row["day_of_week"],
            is_weekend=row["is_weekend"],
            is_holiday=row["is_holiday"],
            is_cat1=row["is_cat1"],
            is_cat2=row["is_cat2"],
            is_fat=row["is_fat"],
            is_exam=row["is_exam"],
            days_to_exam=row["days_to_exam"],
            days_after_exam=row["days_after_exam"],
            meal_type=row["meal_type"],
            menu_name=row["menu_name"],
            dish_category=row["dish_category"],
            is_special_dish=row["is_special_dish"],
            historical_menu_popularity=row["historical_menu_popularity"],
            total_hostel_population=row["total_hostel_population"],
            expected_students=row["expected_students"],
            expected_class_attendance=row["expected_class_attendance"],
            actual_attendance=row["actual_attendance"]
        )
        for _, row in df.iterrows()
    ]
    db.bulk_save_objects(records_to_insert)
    db.commit()

    # 4. Train baseline Random Forest model
    train_result = trainer.train_and_tune(df, tune_hyperparameters=True, n_iter_search=6)
    
    # 5. Save to Model Registry
    version_tag = registry.save_model(
        model=train_result["model"],
        version_tag="RF-v1.0",
        metrics=train_result["metrics"],
        hyperparameters=train_result["best_params"],
        feature_importances=train_result["feature_importances"],
        training_records_count=len(df),
        make_active=True
    )

    # 6. Pre-populate some feedback records from the test evaluation
    db.query(FeedbackORM).delete()
    for rec in train_result["eval_records"][-30:]:
        err = rec["predicted_attendance"] - rec["actual_attendance"]
        db.add(FeedbackORM(
            meal_date=rec["date"],
            meal_type=rec["meal_type"],
            menu_name=rec["menu_name"],
            predicted_attendance=rec["predicted_attendance"],
            actual_attendance=rec["actual_attendance"],
            error=err,
            waste=max(err, 0),
            unmet_demand=max(-err, 0),
            model_version=version_tag,
            notes="Seeded evaluation feedback"
        ))
    db.commit()

    return {
        "status": "success",
        "message": f"Generated {len(df)} historical mess records and trained baseline model {version_tag}.",
        "version_tag": version_tag,
        "metrics": train_result["metrics"],
        "hyperparameters": train_result["best_params"],
        "records_count": len(df)
    }


@router.post("/train", summary="Train/tune Random Forest model on current dataset")
def train_model(
    tune: bool = Query(default=True, description="Whether to run hyperparameter tuning"),
    db: Session = Depends(get_db)
):
    """
    Trains a Random Forest Regression model on all available historical mess records in DB.
    Uses chronological validation and saves to Model Registry.
    """
    records = db.query(AttendanceORM).all()
    if len(records) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient historical records in database. Please call /ml/seed-data first."
        )

    data = [{
        "date": r.date,
        "day_index": r.day_index,
        "semester": r.semester,
        "academic_week": r.academic_week,
        "day_of_week": r.day_of_week,
        "is_weekend": r.is_weekend,
        "is_holiday": r.is_holiday,
        "is_cat1": r.is_cat1,
        "is_cat2": r.is_cat2,
        "is_fat": r.is_fat,
        "is_exam": r.is_exam,
        "days_to_exam": r.days_to_exam,
        "days_after_exam": r.days_after_exam,
        "meal_type": r.meal_type,
        "menu_name": r.menu_name,
        "dish_category": r.dish_category,
        "is_special_dish": r.is_special_dish,
        "historical_menu_popularity": r.historical_menu_popularity,
        "total_hostel_population": r.total_hostel_population,
        "expected_students": r.expected_students,
        "expected_class_attendance": r.expected_class_attendance,
        "actual_attendance": r.actual_attendance
    } for r in records]

    df = pd.DataFrame(data)
    train_result = trainer.train_and_tune(df, tune_hyperparameters=tune, n_iter_search=6)

    # Safe promotion check
    promotion = registry.promote_version_safely(
        candidate_model=train_result["model"],
        candidate_metrics=train_result["metrics"],
        hyperparameters=train_result["best_params"],
        feature_importances=train_result["feature_importances"],
        training_records_count=len(df)
    )

    return {
        "status": "success",
        "version_tag": promotion["version_tag"],
        "promoted_to_active": promotion["promoted"],
        "promotion_reason": promotion["reason"],
        "active_version": promotion["active_version"],
        "metrics": train_result["metrics"],
        "hyperparameters": train_result["best_params"],
        "training_records": len(df)
    }


@router.post("/predict", response_model=PredictResponse, summary="Predict attendance for upcoming meal")
def predict_attendance(
    req: PredictRequest,
    db: Session = Depends(get_db)
):
    """
    Predicts student attendance and range [range_low, range_high] for a specific meal context.
    (PRD Section 9 & 18)
    """
    model, version_info = registry.load_active_model()
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No active trained model available. Please run /ml/seed-data or /ml/train first."
        )

    # Fetch recent history for meal type to compute actual lag features accurately
    meal_hist_records = (
        db.query(AttendanceORM)
        .filter(AttendanceORM.meal_type == req.meal.lower())
        .order_by(AttendanceORM.id.desc())
        .limit(35)
        .all()
    )
    hist_df = None
    if meal_hist_records:
        hist_df = pd.DataFrame([
            {"date": r.date, "meal_type": r.meal_type, "actual_attendance": r.actual_attendance}
            for r in reversed(meal_hist_records)
        ])

    context_dict = req.model_dump()
    X_single = build_single_inference_features(context_dict, historical_df=hist_df)

    predicted_val, range_low, range_high = trainer.predict_with_interval(model, X_single)

    # Log prediction into DB
    pred_record = PredictionORM(
        meal_date=req.date,
        meal_type=req.meal.lower(),
        menu_name=req.menu,
        predicted_attendance=predicted_val,
        range_low=range_low,
        range_high=range_high,
        model_version=version_info["version_tag"],
        expected_students=req.expected_students,
        is_exam=int(req.is_exam or req.is_cat1 or req.is_cat2 or req.is_fat),
        is_holiday=int(req.is_holiday)
    )
    db.add(pred_record)
    db.commit()

    return PredictResponse(
        predicted_attendance=predicted_val,
        range_low=range_low,
        range_high=range_high,
        model_version=version_info["version_tag"],
        prediction_timestamp=datetime.now().isoformat(),
        context=context_dict
    )


@router.get("/evaluation", response_model=EvaluationResponse, summary="Get active model evaluation metrics")
def get_evaluation():
    """
    Returns active Random Forest evaluation metrics: MAE, RMSE, R2, Potential Waste %, Unmet Demand %.
    (PRD Section 12, 13, 18)
    """
    _, version_info = registry.load_active_model()
    if not version_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active model found."
        )

    m = version_info.get("metrics", {})
    return EvaluationResponse(
        mae=m.get("mae", 0.0),
        rmse=m.get("rmse", 0.0),
        r2=m.get("r2", 0.0),
        mape=m.get("mape", 0.0),
        total_waste=m.get("total_waste", 0.0),
        total_unmet_demand=m.get("total_unmet_demand", 0.0),
        waste_rate_pct=m.get("waste_rate_pct", 0.0),
        unmet_rate_pct=m.get("unmet_rate_pct", 0.0),
        sample_count=m.get("sample_count", 0),
        model_version=version_info.get("version_tag", "unknown")
    )


@router.get("/features", response_model=List[FeatureImportanceItem], summary="Get feature importance ranking")
def get_feature_importance():
    """
    Returns feature importance breakdown to explain predictions.
    (PRD Section 15, 18)
    """
    _, version_info = registry.load_active_model()
    if not version_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active model found."
        )

    importances = version_info.get("feature_importances", [])
    return [FeatureImportanceItem(**item) for item in importances]


@router.get("/model-status", response_model=ModelStatusResponse, summary="Get active model status and hyperparameters")
def get_model_status():
    """
    Returns deployment status, hyperparameters, active version, and sample counts.
    (PRD Section 18)
    """
    model, version_info = registry.load_active_model()
    if not version_info:
        return ModelStatusResponse(
            active_version=None,
            is_loaded=False,
            hyperparameters=None,
            metrics=None,
            training_records_count=0,
            created_at=None
        )

    return ModelStatusResponse(
        active_version=version_info.get("version_tag"),
        is_loaded=model is not None,
        hyperparameters=version_info.get("hyperparameters"),
        metrics=version_info.get("metrics"),
        training_records_count=version_info.get("training_records_count"),
        created_at=version_info.get("created_at")
    )


@router.post("/food-requirement", response_model=FoodRequirementResponse, summary="Convert attendance into kitchen prep amounts")
def calculate_food_requirement(
    predicted_attendance: int = Query(..., ge=1, description="Predicted or targeted student attendance"),
    meal_type: str = Query(default="lunch", description="breakfast, lunch, snacks, or dinner"),
    is_special_menu: bool = Query(default=False, description="Whether special protein/paneer item is served"),
    buffer_pct: float = Query(default=3.0, ge=0.0, le=20.0, description="Safety buffer percentage")
):
    """
    Operational conversion of predicted attendance into kitchen food requirements (kg, liters, units).
    (PRD Section 10)
    """
    result = food_calc.calculate(
        predicted_attendance=predicted_attendance,
        meal_type=meal_type,
        is_special_menu=is_special_menu,
        buffer_percentage=buffer_pct
    )
    return FoodRequirementResponse(**result)


@router.post("/feedback", response_model=FeedbackResponse, summary="Record actual attendance and compute waste/unmet demand")
def record_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Feedback loop: Compares prediction with actual outcome, calculates waste and unmet demand,
    and stores record for continuous retraining.
    (PRD Section 11)
    """
    err = feedback.predicted_attendance - feedback.actual_attendance
    waste = max(err, 0)
    unmet = max(-err, 0)

    rec = FeedbackORM(
        prediction_id=feedback.prediction_id,
        meal_date=feedback.meal_date,
        meal_type=feedback.meal_type.lower(),
        menu_name=feedback.menu_name or "",
        predicted_attendance=feedback.predicted_attendance,
        actual_attendance=feedback.actual_attendance,
        error=err,
        waste=waste,
        unmet_demand=unmet,
        model_version=feedback.model_version or "RF-v1.0",
        notes=feedback.notes
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return FeedbackResponse(
        id=rec.id,
        meal_date=rec.meal_date,
        meal_type=rec.meal_type,
        predicted_attendance=rec.predicted_attendance,
        actual_attendance=rec.actual_attendance,
        error=rec.error,
        waste=rec.waste,
        unmet_demand=rec.unmet_demand,
        model_version=rec.model_version,
        created_at=rec.created_at.isoformat()
    )


@router.get("/feedback", response_model=List[FeedbackResponse], summary="List feedback records")
def list_feedbacks(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    feedbacks = db.query(FeedbackORM).order_by(FeedbackORM.id.desc()).limit(limit).all()
    return [
        FeedbackResponse(
            id=f.id,
            meal_date=f.meal_date,
            meal_type=f.meal_type,
            predicted_attendance=f.predicted_attendance,
            actual_attendance=f.actual_attendance,
            error=f.error,
            waste=f.waste,
            unmet_demand=f.unmet_demand,
            model_version=f.model_version,
            created_at=f.created_at.isoformat()
        )
        for f in feedbacks
    ]


@router.get("/actual-vs-predicted", summary="Get time-series comparison with exam/holiday markers")
def get_actual_vs_predicted(
    limit: int = Query(default=60, ge=10, le=300),
    meal_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Time-series data comparing actual attendance vs predicted attendance with contextual markers.
    (PRD Section 14)
    """
    feedbacks = db.query(FeedbackORM).order_by(FeedbackORM.id.desc()).limit(limit).all()
    feedbacks = list(reversed(feedbacks))

    if meal_type:
        feedbacks = [f for f in feedbacks if f.meal_type.lower() == meal_type.lower()]

    result = []
    for f in feedbacks:
        result.append({
            "meal_date": f.meal_date,
            "meal_type": f.meal_type,
            "menu_name": f.menu_name,
            "actual_attendance": f.actual_attendance,
            "predicted_attendance": f.predicted_attendance,
            "error": f.error,
            "waste": f.waste,
            "unmet_demand": f.unmet_demand,
            "model_version": f.model_version
        })

    return result


@router.get("/drift", summary="Check model drift status based on recent feedback errors")
def check_drift(
    window_size: int = Query(default=14, ge=5, le=50),
    db: Session = Depends(get_db)
):
    """
    Monitors recent prediction error vs baseline MAE to detect model drift.
    (PRD Section 17)
    """
    _, version_info = registry.load_active_model()
    if not version_info:
        raise HTTPException(status_code=404, detail="No active model found to evaluate drift against.")

    baseline_mae = version_info.get("metrics", {}).get("mae", 25.0)

    feedbacks = db.query(FeedbackORM).order_by(FeedbackORM.id.asc()).all()
    feedback_dicts = [
        {
            "predicted_attendance": f.predicted_attendance,
            "actual_attendance": f.actual_attendance,
            "meal_date": f.meal_date
        }
        for f in feedbacks
    ]

    drift_report = drift_detector.evaluate_drift(
        baseline_mae=baseline_mae,
        recent_feedbacks=feedback_dicts,
        window_size=window_size
    )
    drift_report["active_version"] = version_info.get("version_tag")
    return drift_report


@router.post("/retrain", summary="Trigger retraining pipeline on updated historical data")
def retrain_model(
    db: Session = Depends(get_db)
):
    """
    Retrains Random Forest with all existing historical records + feedback records,
    evaluates chronologically, and safely promotes if accuracy improves.
    (PRD Section 16)
    """
    # 1. Pull base attendance records
    hist_records = db.query(AttendanceORM).all()
    if len(hist_records) < 50:
        raise HTTPException(status_code=400, detail="Insufficient historical records.")

    # 2. Convert feedback into training records if available
    feedbacks = db.query(FeedbackORM).all()
    
    data = [{
        "date": r.date,
        "day_index": r.day_index,
        "semester": r.semester,
        "academic_week": r.academic_week,
        "day_of_week": r.day_of_week,
        "is_weekend": r.is_weekend,
        "is_holiday": r.is_holiday,
        "is_cat1": r.is_cat1,
        "is_cat2": r.is_cat2,
        "is_fat": r.is_fat,
        "is_exam": r.is_exam,
        "days_to_exam": r.days_to_exam,
        "days_after_exam": r.days_after_exam,
        "meal_type": r.meal_type,
        "menu_name": r.menu_name,
        "dish_category": r.dish_category,
        "is_special_dish": r.is_special_dish,
        "historical_menu_popularity": r.historical_menu_popularity,
        "total_hostel_population": r.total_hostel_population,
        "expected_students": r.expected_students,
        "expected_class_attendance": r.expected_class_attendance,
        "actual_attendance": r.actual_attendance
    } for r in hist_records]

    # Append any feedback records with actual outcomes
    max_day_index = max(r.day_index for r in hist_records)
    for idx, f in enumerate(feedbacks):
        dt = pd.to_datetime(f.meal_date)
        data.append({
            "date": f.meal_date,
            "day_index": max_day_index + idx + 1,
            "semester": 2,
            "academic_week": 10,
            "day_of_week": dt.weekday(),
            "is_weekend": int(dt.weekday() in (5, 6)),
            "is_holiday": 0,
            "is_cat1": 0,
            "is_cat2": 0,
            "is_fat": 0,
            "is_exam": 0,
            "days_to_exam": 14,
            "days_after_exam": 0,
            "meal_type": f.meal_type,
            "menu_name": f.menu_name,
            "dish_category": "Special" if "biryani" in (f.menu_name or "").lower() else "North Indian",
            "is_special_dish": 1 if "biryani" in (f.menu_name or "").lower() else 0,
            "historical_menu_popularity": 1.15 if "biryani" in (f.menu_name or "").lower() else 1.0,
            "total_hostel_population": 1600,
            "expected_students": 1500,
            "expected_class_attendance": 1350,
            "actual_attendance": f.actual_attendance
        })

    df = pd.DataFrame(data)
    train_result = trainer.train_and_tune(df, tune_hyperparameters=True, n_iter_search=6)

    promotion = registry.promote_version_safely(
        candidate_model=train_result["model"],
        candidate_metrics=train_result["metrics"],
        hyperparameters=train_result["best_params"],
        feature_importances=train_result["feature_importances"],
        training_records_count=len(df)
    )

    return {
        "status": "success",
        "retrain_status": "COMPLETED",
        "version_tag": promotion["version_tag"],
        "promoted_to_active": promotion["promoted"],
        "promotion_reason": promotion["reason"],
        "active_version": promotion["active_version"],
        "candidate_metrics": train_result["metrics"],
        "total_records_trained": len(df)
    }
