from app.ml.food_calculator import FoodRequirementCalculator, DEFAULT_CONSUMPTION_RULES


def test_food_calculation_lunch():
    calc = FoodRequirementCalculator()
    predicted_attendance = 1247
    result = calc.calculate(
        predicted_attendance=predicted_attendance,
        meal_type="lunch",
        is_special_menu=True,
        buffer_percentage=3.0
    )

    assert result["predicted_attendance"] == 1247
    assert result["buffer_percentage"] == 3.0
    # Effective headcount = 1247 * 1.03 = ~1284.41 -> 1284
    assert result["effective_preparation_headcount"] == 1284

    # Check rice: 120g per student
    # Base: 1247 * 0.120 = 149.64 kg
    # With buffer: 1284.41 * 0.120 = 154.13 kg
    rice_item = next(item for item in result["ingredients"] if item["item_key"] == "rice")
    assert abs(rice_item["base_quantity"] - 149.64) < 0.2
    assert rice_item["recommended_quantity"] > rice_item["base_quantity"]
    assert rice_item["unit"] == "kg"

    # Check roti: 2.5 units per student
    roti_item = next(item for item in result["ingredients"] if item["item_key"] == "roti")
    assert abs(roti_item["base_quantity"] - (1247 * 2.5)) < 1.0
    assert roti_item["unit"] == "units"

    # Special protein item should be present when is_special_menu=True
    protein_item = next((item for item in result["ingredients"] if item["item_key"] == "chicken_or_paneer"), None)
    assert protein_item is not None


def test_food_calculation_no_special():
    calc = FoodRequirementCalculator()
    result = calc.calculate(
        predicted_attendance=1000,
        meal_type="lunch",
        is_special_menu=False
    )
    protein_item = next((item for item in result["ingredients"] if item["item_key"] == "chicken_or_paneer"), None)
    assert protein_item is None
