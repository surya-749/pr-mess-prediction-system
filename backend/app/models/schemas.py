from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.core.database import Base


# ==========================================
# SQLAlchemy ORM Models
# ==========================================

class AttendanceORM(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(String(50), index=True)
    day_index = Column(Integer, index=True)
    semester = Column(Integer, default=1)
    academic_week = Column(Integer, default=1)
    day_of_week = Column(Integer)
    is_weekend = Column(Integer, default=0)
    is_holiday = Column(Integer, default=0)
    is_cat1 = Column(Integer, default=0)
    is_cat2 = Column(Integer, default=0)
    is_fat = Column(Integer, default=0)
    is_exam = Column(Integer, default=0)
    days_to_exam = Column(Integer, default=0)
    days_after_exam = Column(Integer, default=0)
    meal_type = Column(String(50), index=True)
    menu_name = Column(String(200))
    dish_category = Column(String(100))
    is_special_dish = Column(Integer, default=0)
    historical_menu_popularity = Column(Float, default=1.0)
    total_hostel_population = Column(Integer, default=1600)
    expected_students = Column(Integer, default=1500)
    expected_class_attendance = Column(Integer, default=1350)
    actual_attendance = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class PredictionORM(Base):
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    meal_date = Column(String(50), index=True)
    meal_type = Column(String(50))
    menu_name = Column(String(200), default="")
    predicted_attendance = Column(Integer)
    range_low = Column(Integer)
    range_high = Column(Integer)
    model_version = Column(String(50))
    expected_students = Column(Integer, default=1500)
    is_exam = Column(Integer, default=0)
    is_holiday = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class FeedbackORM(Base):
    __tablename__ = "feedback_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    prediction_id = Column(Integer, nullable=True)
    meal_date = Column(String(50), index=True)
    meal_type = Column(String(50))
    menu_name = Column(String(200), default="")
    predicted_attendance = Column(Integer)
    actual_attendance = Column(Integer)
    error = Column(Integer)  # predicted - actual
    waste = Column(Integer)  # max(predicted - actual, 0)
    unmet_demand = Column(Integer)  # max(actual - predicted, 0)
    model_version = Column(String(50), default="unknown")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==========================================
# Pydantic Request & Response Schemas
# ==========================================

class PredictRequest(BaseModel):
    date: str = Field(default="2026-09-20", description="Date in YYYY-MM-DD format")
    meal: str = Field(default="lunch", description="breakfast, lunch, snacks, or dinner")
    menu: str = Field(default="Chicken Biryani / Paneer Biryani", description="Menu name")
    dish_category: Optional[str] = Field(default="Special", description="South Indian, North Indian, Special, Snack, Light")
    is_holiday: bool = Field(default=False)
    is_exam: bool = Field(default=False)
    is_cat1: bool = Field(default=False)
    is_cat2: bool = Field(default=False)
    is_fat: bool = Field(default=False)
    days_to_exam: int = Field(default=0)
    expected_students: int = Field(default=1500)
    expected_class_attendance: Optional[int] = Field(default=1350)
    is_special_dish: Optional[int] = Field(default=1)
    historical_menu_popularity: Optional[float] = Field(default=1.20)


class PredictResponse(BaseModel):
    predicted_attendance: int
    range_low: int
    range_high: int
    model_version: str
    prediction_timestamp: str
    context: Dict[str, Any]


class FeedbackCreate(BaseModel):
    prediction_id: Optional[int] = None
    meal_date: str
    meal_type: str
    predicted_attendance: int
    actual_attendance: int
    menu_name: Optional[str] = ""
    model_version: Optional[str] = "RF-v1.0"
    notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    meal_date: str
    meal_type: str
    predicted_attendance: int
    actual_attendance: int
    error: int
    waste: int
    unmet_demand: int
    model_version: str
    created_at: str


class FoodRequirementItem(BaseModel):
    item_key: str
    item_name: str
    unit: str
    base_quantity: float
    recommended_quantity: float
    buffer_quantity: float
    per_student_consumption: str


class FoodRequirementResponse(BaseModel):
    predicted_attendance: int
    buffer_percentage: float
    effective_preparation_headcount: int
    meal_type: str
    is_special_menu: bool
    ingredients: List[FoodRequirementItem]


class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float
    percentage: float


class EvaluationResponse(BaseModel):
    mae: float
    rmse: float
    r2: float
    mape: float
    total_waste: float
    total_unmet_demand: float
    waste_rate_pct: float
    unmet_rate_pct: float
    sample_count: int
    model_version: str


class ModelStatusResponse(BaseModel):
    active_version: Optional[str]
    is_loaded: bool
    hyperparameters: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    training_records_count: Optional[int]
    created_at: Optional[str]
