import pytest
import os
import shutil
from app.ml.data_generator import generate_college_mess_dataset
from app.ml.model_trainer import ModelTrainer
from app.ml.model_registry import ModelRegistry
from app.ml.feature_engineering import build_single_inference_features


@pytest.fixture
def temp_registry(tmp_path):
    reg_dir = str(tmp_path / "saved_models")
    return ModelRegistry(registry_dir=reg_dir)


def test_data_generation_and_trainer(temp_registry):
    # 1. Generate 60 days of synthetic college data (~240 meals)
    df = generate_college_mess_dataset(num_days=60, base_population=1500, seed=42)
    assert len(df) == 240
    assert "actual_attendance" in df.columns

    # 2. Train model with chronological split
    trainer = ModelTrainer()
    train_res = trainer.train_and_tune(df, tune_hyperparameters=False)

    model = train_res["model"]
    metrics = train_res["metrics"]
    importances = train_res["feature_importances"]

    # Basic validity checks
    assert metrics["mae"] > 0
    assert metrics["r2"] > 0.5  # Model should comfortably learn clear campus patterns
    assert len(importances) == len(trainer.feature_names)
    assert importances[0]["importance"] >= importances[-1]["importance"]

    # 3. Test prediction with tree variance interval
    context = {
        "date": "2026-09-21",
        "meal": "lunch",
        "menu": "Chicken Biryani / Paneer Biryani",
        "dish_category": "Special",
        "is_holiday": False,
        "is_exam": False,
        "expected_students": 1500
    }
    X_single = build_single_inference_features(context)
    pred, low, high = trainer.predict_with_interval(model, X_single)

    assert low <= pred <= high, f"Prediction range invalid: low={low}, pred={pred}, high={high}"
    assert pred > 500  # Lunch attendance for 1500 students should be healthy

    # 4. Save to Model Registry and verify versioning & safe promotion
    v1 = temp_registry.save_model(
        model=model,
        version_tag="RF-v1.0",
        metrics=metrics,
        hyperparameters=train_res["best_params"],
        feature_importances=importances,
        training_records_count=len(df),
        make_active=True
    )
    assert v1 == "RF-v1.0"

    loaded_model, info = temp_registry.load_active_model()
    assert loaded_model is not None
    assert info["version_tag"] == "RF-v1.0"

    # 5. Verify Safe Promotion: if candidate has worse MAE, it shouldn't replace active
    worse_metrics = {**metrics, "mae": metrics["mae"] + 20.0}
    promo_res = temp_registry.promote_version_safely(
        candidate_model=model,
        candidate_metrics=worse_metrics,
        hyperparameters=train_res["best_params"],
        feature_importances=importances,
        training_records_count=len(df)
    )
    assert promo_res["promoted"] is False
    assert promo_res["active_version"] == "RF-v1.0"
