"""
Food Requirement Engine
Converts predicted attendance counts into operational kitchen quantities (in kg or units)
using configurable per-student consumption rules and safety buffers.
(PRD Section 10)
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class IngredientRule(BaseModel):
    name: str
    unit: str  # "kg", "liters", "units"
    grams_or_units_per_student: float
    description: Optional[str] = None


# Default mess consumption standards based on university mess operations
DEFAULT_CONSUMPTION_RULES: Dict[str, Dict[str, IngredientRule]] = {
    "breakfast": {
        "idli_vada": IngredientRule(
            name="Idli / Vada",
            unit="units",
            grams_or_units_per_student=3.0,
            description="3 idlis or vadas per student"
        ),
        "sambar": IngredientRule(
            name="Sambar",
            unit="liters",
            grams_or_units_per_student=150.0,  # 150 ml per student
            description="150 ml per student"
        ),
        "chutney": IngredientRule(
            name="Coconut Chutney",
            unit="kg",
            grams_or_units_per_student=45.0,  # 45 g per student
            description="45g per student"
        ),
        "bread": IngredientRule(
            name="Bread Slices",
            unit="units",
            grams_or_units_per_student=2.0,
            description="2 slices per student"
        ),
        "tea_coffee": IngredientRule(
            name="Tea / Coffee",
            unit="liters",
            grams_or_units_per_student=120.0,  # 120 ml per student
            description="120 ml per student"
        )
    },
    "lunch": {
        "rice": IngredientRule(
            name="Rice (Raw)",
            unit="kg",
            grams_or_units_per_student=120.0,  # 120g per student
            description="120g raw rice per student"
        ),
        "dal": IngredientRule(
            name="Dal / Lentils (Cooked)",
            unit="liters",
            grams_or_units_per_student=150.0,  # 150 ml per student
            description="150 ml dal per student"
        ),
        "sabzi_curry": IngredientRule(
            name="Main Vegetable Curry / Sabzi",
            unit="kg",
            grams_or_units_per_student=140.0,  # 140g per student
            description="140g vegetable per student"
        ),
        "roti": IngredientRule(
            name="Roti / Chapati",
            unit="units",
            grams_or_units_per_student=2.5,  # 2.5 rotis per student
            description="2.5 pieces per student"
        ),
        "curd": IngredientRule(
            name="Curd",
            unit="liters",
            grams_or_units_per_student=80.0,
            description="80 ml per student"
        ),
        "chicken_or_paneer": IngredientRule(
            name="Special Protein (Chicken/Paneer)",
            unit="kg",
            grams_or_units_per_student=160.0,  # 160g on special menu days
            description="160g protein on non-veg/paneer days"
        )
    },
    "snacks": {
        "snack_item": IngredientRule(
            name="Snack (Samosa/Puff/Cutlet)",
            unit="units",
            grams_or_units_per_student=2.0,
            description="2 pieces per student"
        ),
        "tea_coffee": IngredientRule(
            name="Tea / Coffee",
            unit="liters",
            grams_or_units_per_student=120.0,
            description="120 ml per student"
        )
    },
    "dinner": {
        "rice": IngredientRule(
            name="Rice (Raw)",
            unit="kg",
            grams_or_units_per_student=110.0,
            description="110g raw rice per student"
        ),
        "dal": IngredientRule(
            name="Dal / Lentils",
            unit="liters",
            grams_or_units_per_student=140.0,
            description="140 ml dal per student"
        ),
        "sabzi_curry": IngredientRule(
            name="Vegetable Gravy / Sabzi",
            unit="kg",
            grams_or_units_per_student=130.0,
            description="130g vegetable per student"
        ),
        "roti": IngredientRule(
            name="Roti / Chapati",
            unit="units",
            grams_or_units_per_student=2.5,
            description="2.5 pieces per student"
        ),
        "egg_or_sweet": IngredientRule(
            name="Egg / Dessert",
            unit="units",
            grams_or_units_per_student=1.0,
            description="1 egg or sweet per student"
        )
    }
}


class FoodRequirementCalculator:
    def __init__(self, custom_rules: Optional[Dict[str, Dict[str, IngredientRule]]] = None):
        self.rules = custom_rules or DEFAULT_CONSUMPTION_RULES

    def calculate(
        self,
        predicted_attendance: float,
        meal_type: str,
        is_special_menu: bool = False,
        buffer_percentage: float = 3.0  # Default 3% kitchen safety buffer
    ) -> Dict[str, Any]:
        """
        Calculates recommended food preparation quantities.
        The buffer_percentage ensures that minor spikes in student demand do not cause food shortage.
        """
        meal_key = meal_type.lower().strip()
        meal_rules = self.rules.get(meal_key, self.rules.get("lunch", {}))

        effective_headcount = predicted_attendance * (1.0 + (buffer_percentage / 100.0))

        requirements = []
        for key, rule in meal_rules.items():
            # If item is chicken/paneer and it's not a special menu meal, skip
            if key == "chicken_or_paneer" and not is_special_menu:
                continue

            if rule.unit in ["kg", "liters"]:
                # Convert grams/milliliters to kg or liters
                quantity = (effective_headcount * rule.grams_or_units_per_student) / 1000.0
            else:
                quantity = effective_headcount * rule.grams_or_units_per_student

            base_quantity = (
                (predicted_attendance * rule.grams_or_units_per_student) / 1000.0
                if rule.unit in ["kg", "liters"]
                else predicted_attendance * rule.grams_or_units_per_student
            )

            requirements.append({
                "item_key": key,
                "item_name": rule.name,
                "unit": rule.unit,
                "base_quantity": round(base_quantity, 2),
                "recommended_quantity": round(quantity, 2),
                "buffer_quantity": round(quantity - base_quantity, 2),
                "per_student_consumption": f"{rule.grams_or_units_per_student} {'g/ml' if rule.unit in ['kg', 'liters'] else 'units'}"
            })

        return {
            "predicted_attendance": int(round(predicted_attendance)),
            "buffer_percentage": buffer_percentage,
            "effective_preparation_headcount": int(round(effective_headcount)),
            "meal_type": meal_key,
            "is_special_menu": is_special_menu,
            "ingredients": requirements
        }
