"""
College Mess Historical Data Generator
Generates realistic multi-semester synthetic attendance datasets adhering to university academic calendar dynamics:
- CAT-1, CAT-2, FAT exam periods and study leaves
- Meal types: breakfast, lunch, snacks, dinner
- Menu types and dish popularity factors (Biryani, Paneer, Chicken, Upma, etc.)
- Hostel population dynamics, weekends, and holidays
- Lag relationships and rolling temporal trends
(PRD Section 5)
"""
from datetime import date, timedelta
import random
from typing import List, Dict, Any
import numpy as np
import pandas as pd


MEAL_CONFIG = {
    "breakfast": {"base_ratio": 0.70, "std": 0.04},
    "lunch": {"base_ratio": 0.85, "std": 0.035},
    "snacks": {"base_ratio": 0.52, "std": 0.05},
    "dinner": {"base_ratio": 0.82, "std": 0.04}
}

MENUS_BY_MEAL = {
    "breakfast": [
        {"menu": "Idli Sambar & Vada", "category": "South Indian", "is_special": False, "popularity": 1.05},
        {"menu": "Aloo Paratha & Curd", "category": "North Indian", "is_special": True, "popularity": 1.15},
        {"menu": "Poha & Boiled Eggs", "category": "Light", "is_special": False, "popularity": 0.95},
        {"menu": "Upma & Chutney", "category": "South Indian", "is_special": False, "popularity": 0.85},
        {"menu": "Puri Bhaji", "category": "North Indian", "is_special": True, "popularity": 1.18},
    ],
    "lunch": [
        {"menu": "Rajma Chawal & Mix Veg", "category": "North Indian", "is_special": False, "popularity": 1.05},
        {"menu": "Chicken Biryani / Paneer Biryani", "category": "Special", "is_special": True, "popularity": 1.25},
        {"menu": "Sambar Rice & Poriyal", "category": "South Indian", "is_special": False, "popularity": 0.92},
        {"menu": "Dal Makhani & Jeera Rice", "category": "North Indian", "is_special": True, "popularity": 1.12},
        {"menu": "Chole Bhature", "category": "North Indian", "is_special": True, "popularity": 1.20},
        {"menu": "Simple Khichdi & Papad", "category": "Light", "is_special": False, "popularity": 0.80},
    ],
    "snacks": [
        {"menu": "Samosa & Masala Chai", "category": "Snack", "is_special": True, "popularity": 1.22},
        {"menu": "Veg Puff & Coffee", "category": "Snack", "is_special": False, "popularity": 1.02},
        {"menu": "Pakora & Green Chutney", "category": "Snack", "is_special": True, "popularity": 1.15},
        {"menu": "Biscuits & Tea", "category": "Light", "is_special": False, "popularity": 0.85},
    ],
    "dinner": [
        {"menu": "Butter Chicken / Paneer Butter Masala & Naan", "category": "Special", "is_special": True, "popularity": 1.28},
        {"menu": "Egg Curry / Malai Kofta & Roti Rice", "category": "Special", "is_special": True, "popularity": 1.16},
        {"menu": "Dal Tadka, Seasonal Sabzi & Chapati", "category": "North Indian", "is_special": False, "popularity": 0.98},
        {"menu": "Rasam, Curd Rice & Potato Roast", "category": "South Indian", "is_special": False, "popularity": 0.90},
        {"menu": "Veg Fried Rice & Manchurian", "category": "Indo-Chinese", "is_special": True, "popularity": 1.18},
    ]
}


def generate_college_mess_dataset(
    start_date: date = date(2025, 7, 1),
    num_days: int = 400,
    base_population: int = 1600,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a chronological multi-semester dataset for a college mess.
    Includes 2 full semesters with CAT-1, CAT-2, and FAT exam schedules.
    """
    random.seed(seed)
    np.random.seed(seed)

    records: List[Dict[str, Any]] = []

    # Simulation timeline structure:
    # Days 0 - 150: Semester 1 (Autumn)
    #   - Days 35 - 42: CAT-1
    #   - Days 85 - 92: CAT-2
    #   - Days 135 - 147: FAT (Final Assessment Test)
    # Days 151 - 180: Winter Vacation / Break (low attendance)
    # Days 181 - 330: Semester 2 (Winter/Spring)
    #   - Days 215 - 222: CAT-1
    #   - Days 265 - 272: CAT-2
    #   - Days 315 - 327: FAT
    # Days 331 - 400: Summer Break / Early Autumn start

    for day_idx in range(num_days):
        current_date = start_date + timedelta(days=day_idx)
        dow = current_date.weekday()  # 0: Mon ... 6: Sun
        is_weekend = dow in (5, 6)

        # Academic timeline markers
        sem_day = day_idx % 180
        semester = 1 if day_idx < 180 else 2

        # Check vacations
        is_vacation = (148 <= sem_day <= 180) or (day_idx >= 328 and day_idx <= 365)
        
        # Check Exams
        is_cat1 = False
        is_cat2 = False
        is_fat = False

        if 35 <= sem_day <= 42 or (sem_day >= 35 and sem_day <= 42):
            is_cat1 = True
        elif 85 <= sem_day <= 92:
            is_cat2 = True
        elif 135 <= sem_day <= 147:
            is_fat = True

        is_exam = is_cat1 or is_cat2 or is_fat

        # Calculate days to nearest upcoming exam
        if sem_day < 35:
            days_to_exam = 35 - sem_day
            days_after_exam = sem_day
        elif sem_day <= 42:
            days_to_exam = 0
            days_after_exam = 0
        elif sem_day < 85:
            days_to_exam = 85 - sem_day
            days_after_exam = sem_day - 42
        elif sem_day <= 92:
            days_to_exam = 0
            days_after_exam = 0
        elif sem_day < 135:
            days_to_exam = 135 - sem_day
            days_after_exam = sem_day - 92
        elif sem_day <= 147:
            days_to_exam = 0
            days_after_exam = 0
        else:
            days_to_exam = 35 + (180 - sem_day)
            days_after_exam = sem_day - 147

        # Random holidays (e.g. national holidays, festival days)
        is_holiday = False
        if not is_weekend and random.random() < 0.04 and not is_exam and not is_vacation:
            is_holiday = True

        # Campus student population modeling
        if is_vacation:
            on_campus_ratio = random.uniform(0.18, 0.28)
        elif is_fat:
            # Gradually empties during FAT
            fat_progress = (sem_day - 135) / 12.0
            on_campus_ratio = max(0.40, 0.95 - (fat_progress * 0.45))
        elif is_weekend or is_holiday:
            on_campus_ratio = random.uniform(0.72, 0.82)
        elif is_cat1 or is_cat2:
            on_campus_ratio = random.uniform(0.94, 0.99)
        else:
            on_campus_ratio = random.uniform(0.92, 0.98)

        expected_students = int(base_population * on_campus_ratio)
        class_attendance_ratio = 0.0 if (is_weekend or is_holiday or is_vacation or is_exam) else random.uniform(0.85, 0.95)

        for meal_type in ["breakfast", "lunch", "snacks", "dinner"]:
            cfg = MEAL_CONFIG[meal_type]
            menu_choices = MENUS_BY_MEAL[meal_type]
            menu_item = random.choice(menu_choices)

            # Base attendance ratio
            meal_ratio = cfg["base_ratio"]

            # Menu popularity multiplier
            meal_ratio *= menu_item["popularity"]

            # Weekend effect
            if is_weekend:
                if meal_type == "breakfast":
                    meal_ratio *= 0.72  # Students sleep in
                elif meal_type == "lunch":
                    meal_ratio *= 0.88  # Outings / Swiggy
                elif meal_type == "snacks":
                    meal_ratio *= 0.90
                elif meal_type == "dinner":
                    meal_ratio *= 0.85  # Weekend dinner outside

            # Exam effect
            if is_exam:
                if meal_type == "breakfast":
                    meal_ratio *= 0.82  # Late-night study sessions cause missed breakfast
                elif meal_type == "lunch":
                    meal_ratio *= 0.88
                elif meal_type == "snacks":
                    meal_ratio *= 1.12  # Library break snacks increase!
                elif meal_type == "dinner":
                    meal_ratio *= 0.90

            # Holiday effect
            if is_holiday:
                meal_ratio *= 0.80

            # Add gaussian noise (e.g. +/- 3.5%)
            noise = np.random.normal(0, cfg["std"])
            final_ratio = np.clip(meal_ratio + noise, 0.15, 0.98)

            actual_attendance = int(round(expected_students * final_ratio))
            # Clamp between realistic bounds
            actual_attendance = max(10, min(actual_attendance, base_population))

            records.append({
                "date": current_date.isoformat(),
                "day_index": day_idx,
                "semester": semester,
                "academic_week": (sem_day // 7) + 1,
                "day_of_week": dow,
                "is_weekend": int(is_weekend),
                "is_holiday": int(is_holiday),
                "is_cat1": int(is_cat1),
                "is_cat2": int(is_cat2),
                "is_fat": int(is_fat),
                "is_exam": int(is_exam),
                "days_to_exam": int(days_to_exam),
                "days_after_exam": int(days_after_exam),
                "meal_type": meal_type,
                "menu_name": menu_item["menu"],
                "dish_category": menu_item["category"],
                "is_special_dish": int(menu_item["is_special"]),
                "historical_menu_popularity": float(menu_item["popularity"]),
                "total_hostel_population": base_population,
                "expected_students": expected_students,
                "expected_class_attendance": int(expected_students * class_attendance_ratio),
                "actual_attendance": actual_attendance
            })

    df = pd.DataFrame(records)
    # Sort strictly chronologically by date and meal order
    meal_order = {"breakfast": 0, "lunch": 1, "snacks": 2, "dinner": 3}
    df["meal_order"] = df["meal_type"].map(meal_order)
    df = df.sort_values(by=["day_index", "meal_order"]).reset_index(drop=True)
    df = df.drop(columns=["meal_order"])
    return df
