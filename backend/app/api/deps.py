from app.core.database import get_db
from app.ml.model_registry import ModelRegistry
from app.ml.food_calculator import FoodRequirementCalculator
from app.ml.drift_detector import DriftDetector

registry = ModelRegistry()
food_calc = FoodRequirementCalculator()
drift_detector = DriftDetector()
