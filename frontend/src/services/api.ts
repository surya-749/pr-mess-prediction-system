export interface EvaluationMetrics {
  mae: number;
  rmse: number;
  r2: number;
  mape: number;
  total_waste: number;
  total_unmet_demand: number;
  waste_rate_pct: number;
  unmet_rate_pct: number;
  sample_count: number;
  model_version: string;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
  percentage: number;
}

export interface ModelStatus {
  active_version: string | null;
  is_loaded: boolean;
  hyperparameters: Record<string, any> | null;
  metrics: Record<string, any> | null;
  training_records_count: number;
  created_at: string | null;
}

export interface PredictionResult {
  predicted_attendance: number;
  range_low: number;
  range_high: number;
  model_version: string;
  prediction_timestamp: string;
  context: Record<string, any>;
}

export interface IngredientRequirement {
  item_key: string;
  item_name: string;
  unit: string;
  base_quantity: number;
  recommended_quantity: number;
  buffer_quantity: number;
  per_student_consumption: string;
}

export interface FoodRequirementResponse {
  predicted_attendance: number;
  buffer_percentage: number;
  effective_preparation_headcount: number;
  meal_type: string;
  is_special_menu: boolean;
  ingredients: IngredientRequirement[];
}

export interface ActualVsPredictedPoint {
  meal_date: string;
  meal_type: string;
  menu_name: string;
  actual_attendance: number;
  predicted_attendance: number;
  error: number;
  waste: number;
  unmet_demand: number;
  model_version: string;
}

export interface DriftReport {
  drift_detected: boolean;
  status: string;
  severity: string;
  message: string;
  baseline_mae: number;
  recent_mae: number | null;
  threshold_mae: number | null;
  bias: number;
  bias_direction: string;
  sample_count: number;
  recommended_action: string;
  active_version?: string;
}

export interface FeedbackRecord {
  id: number;
  meal_date: string;
  meal_type: string;
  predicted_attendance: number;
  actual_attendance: number;
  error: number;
  waste: number;
  unmet_demand: number;
  model_version: string;
  created_at: string;
}

const API_BASE = "http://127.0.0.1:8000/ml";

export async function fetchModelStatus(): Promise<ModelStatus> {
  const res = await fetch(`${API_BASE}/model-status`);
  if (!res.ok) throw new Error("Failed to fetch model status");
  return res.json();
}

export async function fetchEvaluation(): Promise<EvaluationMetrics> {
  const res = await fetch(`${API_BASE}/evaluation`);
  if (!res.ok) throw new Error("Failed to fetch evaluation metrics");
  return res.json();
}

export async function fetchFeatureImportance(): Promise<FeatureImportance[]> {
  const res = await fetch(`${API_BASE}/features`);
  if (!res.ok) throw new Error("Failed to fetch features");
  return res.json();
}

export async function predictAttendance(params: {
  date: string;
  meal: string;
  menu: string;
  dish_category: string;
  is_holiday: boolean;
  is_exam: boolean;
  expected_students: number;
}): Promise<PredictionResult> {
  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error("Prediction request failed");
  return res.json();
}

export async function fetchFoodRequirement(
  attendance: number,
  mealType: string,
  isSpecial: boolean,
  bufferPct: number
): Promise<FoodRequirementResponse> {
  const res = await fetch(
    `${API_BASE}/food-requirement?predicted_attendance=${attendance}&meal_type=${mealType}&is_special_menu=${isSpecial}&buffer_pct=${bufferPct}`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error("Failed to calculate food requirements");
  return res.json();
}

export async function fetchActualVsPredicted(limit = 60, mealType?: string): Promise<ActualVsPredictedPoint[]> {
  const url = mealType 
    ? `${API_BASE}/actual-vs-predicted?limit=${limit}&meal_type=${mealType}`
    : `${API_BASE}/actual-vs-predicted?limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch actual vs predicted data");
  return res.json();
}

export async function fetchDriftReport(): Promise<DriftReport> {
  const res = await fetch(`${API_BASE}/drift`);
  if (!res.ok) throw new Error("Failed to fetch drift report");
  return res.json();
}

export async function submitFeedback(data: {
  meal_date: string;
  meal_type: string;
  predicted_attendance: number;
  actual_attendance: number;
  menu_name?: string;
  model_version?: string;
  notes?: string;
}): Promise<FeedbackRecord> {
  const res = await fetch(`${API_BASE}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("Failed to submit feedback");
  return res.json();
}

export async function triggerRetrain(): Promise<any> {
  const res = await fetch(`${API_BASE}/retrain`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger retraining");
  return res.json();
}

export async function triggerSeedData(numDays = 300): Promise<any> {
  const res = await fetch(`${API_BASE}/seed-data?num_days=${numDays}`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to seed historical data");
  return res.json();
}
