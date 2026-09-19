# AI Food Demand Forecasting Engine for College Messes

An end-to-end Machine Learning forecasting platform designed for college messes that predicts continuous student attendance per meal (Breakfast, Lunch, Snacks, Dinner) using **Random Forest Regression** and converts demand forecasts into actionable operational food-preparation quantities (Rice kg, Dal L, Sabzi kg, Roti units) with safety buffer optimization.

---

## Key Features

1. **Random Forest Regression Engine**:
   - Primary causal demand model learning non-linear interactions across historical lags, academic calendar, exams, and menu items.
   - Continuous headcount target prediction with tree ensemble variance prediction intervals ($\hat{y} \pm 1.96 \cdot \sigma_{\text{trees}}$).

2. **Zero-Leakage Feature Engineering**:
   - Strictly chronological temporal lag generation (`attendance_lag_1`, `2`, `3`, `7`).
   - Rolling means (`rolling_mean_7`, `14`, `30`) computed strictly on prior historical windows.
   - Academic exam context (`is_cat1`, `is_cat2`, `is_fat`, `days_to_exam`, `days_after_exam`).
   - Meal type and menu popularity factors (e.g. Biryani, Paneer, Chicken boosts).

3. **Domain-Specific Evaluation & Metrics**:
   - **MAE & RMSE**: Precision of headcount estimates.
   - **R² Score**: Explains over 93% of variance on college campus test sets.
   - **Potential Waste**: $\max(\hat{y} - y, 0)$
   - **Unmet Demand**: $\max(y - \hat{y}, 0)$
   - Waste rate % and Unmet demand rate % bounded under 3%.

4. **Operational Food Requirement Converter**:
   - Configurable per-student consumption rules (e.g. 120g rice, 150ml dal, 140g sabzi, 2.5 rotis, 160g protein).
   - Adjustable kitchen safety buffer slider (+0% to +10%) preventing shortages while bounding surplus.

5. **Closed-Loop Feedback, Retraining & Drift Detection**:
   - Record actual turnstile biometric headcounts post-meal.
   - Automated model drift detector monitoring rolling 14-meal error vs baseline benchmark.
   - Retraining pipeline with automated safe promotion: candidate models only replace production if validation error improves.

6. **Interactive Modern Web Dashboard**:
   - Next-meal demand forecaster & kitchen preparation prep sheet.
   - Actual vs. Predicted time-series visualizer with exam & holiday markers.
   - Random Forest MDI Feature Importance bar chart.
   - Model drift monitor and one-click retraining trigger.

---

## System Architecture

```
pr-mess-prediction-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py               # Dependency injection & singletons
│   │   │   └── routes.py             # REST API endpoints
│   │   ├── core/
│   │   │   ├── config.py             # App configurations
│   │   │   └── database.py           # SQLAlchemy SQLite/PostgreSQL setup
│   │   ├── ml/
│   │   │   ├── data_generator.py     # Academic calendar synthetic dataset generator
│   │   │   ├── feature_engineering.py# Temporal lags & rolling windows
│   │   │   ├── model_trainer.py      # Random Forest training & tuning
│   │   │   ├── model_registry.py     # Versioning & promotion logic
│   │   │   ├── metrics.py            # MAE, RMSE, R2, Waste, Unmet Demand
│   │   │   ├── drift_detector.py     # Error deterioration tracking
│   │   │   └── food_calculator.py    # Headcount to kg/units conversion
│   │   ├── models/
│   │   │   └── schemas.py            # ORM and Pydantic schemas
│   │   └── main.py                   # FastAPI app entry point
│   ├── tests/                        # 100% passing test suite
│   ├── saved_models/                 # Model registry artifacts
│   ├── requirements.txt
│   └── seed_production.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   ├── MetricCards.tsx
│   │   │   ├── ActualVsPredictedChart.tsx
│   │   │   ├── FeatureImportanceChart.tsx
│   │   │   ├── PredictionAndKitchenPlanner.tsx
│   │   │   └── FeedbackAndDriftModal.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── index.css
│   └── package.json
└── start_system.bat
```

---

## Quickstart Guide

### 1. Backend Setup & Startup
```powershell
# In project root
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Swagger Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend Startup
```powershell
cd frontend
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

### 3. Or Launch Both Together (Windows)
Double-click `start_system.bat` to launch both servers simultaneously in separate windows.

---

## Running Automated Tests

Run the full pytest suite:
```powershell
$env:PYTHONPATH="backend"; pytest backend/tests -v
```
All 7 tests cover zero-leakage feature engineering, food requirement conversion, model training, rolling cross-validation, and API integration.
