import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def test_api_seed_and_predict(client):
    # 1. Seed small dataset
    seed_resp = client.post("/ml/seed-data?num_days=40")
    assert seed_resp.status_code == 200
    seed_json = seed_resp.json()
    assert seed_json["status"] == "success"
    assert "RF-v1.0" in seed_json["version_tag"]

    # 2. Check model status
    status_resp = client.get("/ml/model-status")
    assert status_resp.status_code == 200
    status_json = status_resp.json()
    assert status_json["is_loaded"] is True
    assert status_json["active_version"] == "RF-v1.0"

    # 3. Predict endpoint (PRD Section 18)
    predict_payload = {
        "date": "2026-09-22",
        "meal": "lunch",
        "menu": "Chicken Biryani / Paneer Biryani",
        "is_holiday": False,
        "is_exam": True,
        "expected_students": 1500
    }
    pred_resp = client.post("/ml/predict", json=predict_payload)
    assert pred_resp.status_code == 200
    pred_json = pred_resp.json()
    assert "predicted_attendance" in pred_json
    assert pred_json["range_low"] <= pred_json["predicted_attendance"] <= pred_json["range_high"]
    assert pred_json["model_version"] == "RF-v1.0"

    # 4. Evaluation endpoint
    eval_resp = client.get("/ml/evaluation")
    assert eval_resp.status_code == 200
    eval_json = eval_resp.json()
    assert "mae" in eval_json
    assert "rmse" in eval_json
    assert "waste_rate_pct" in eval_json

    # 5. Features endpoint
    feat_resp = client.get("/ml/features")
    assert feat_resp.status_code == 200
    feat_json = feat_resp.json()
    assert isinstance(feat_json, list)
    assert len(feat_json) > 0

    # 6. Food requirement endpoint
    food_resp = client.post(f"/ml/food-requirement?predicted_attendance={pred_json['predicted_attendance']}&meal_type=lunch&buffer_pct=4.0")
    assert food_resp.status_code == 200
    food_json = food_resp.json()
    assert food_json["effective_preparation_headcount"] > food_json["predicted_attendance"]
    assert len(food_json["ingredients"]) > 0

    # 7. Feedback endpoint
    feedback_payload = {
        "meal_date": "2026-09-22",
        "meal_type": "lunch",
        "predicted_attendance": pred_json["predicted_attendance"],
        "actual_attendance": pred_json["predicted_attendance"] - 25,
        "menu_name": "Chicken Biryani / Paneer Biryani",
        "model_version": "RF-v1.0",
        "notes": "Good turnout despite slight drizzle"
    }
    fb_resp = client.post("/ml/feedback", json=feedback_payload)
    assert fb_resp.status_code == 200
    fb_json = fb_resp.json()
    assert fb_json["waste"] == 25
    assert fb_json["unmet_demand"] == 0

    # 8. Drift check
    drift_resp = client.get("/ml/drift")
    assert drift_resp.status_code == 200
    drift_json = drift_resp.json()
    assert "drift_detected" in drift_json
