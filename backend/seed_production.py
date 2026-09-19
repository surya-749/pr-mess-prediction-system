"""
Initial Database Seeder and Baseline Model Trainer
"""
import sys
sys.path.insert(0, 'backend')

from app.core.database import SessionLocal, Base, engine
from app.models.schemas import AttendanceORM, FeedbackORM
from app.ml.data_generator import generate_college_mess_dataset
from app.ml.model_trainer import ModelTrainer
from app.ml.model_registry import ModelRegistry


def seed():
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear old data
    db.query(AttendanceORM).delete()
    db.query(FeedbackORM).delete()
    db.commit()

    print("Generating 320 days of multi-semester college mess records (CAT-1, CAT-2, FAT, vacations)...")
    df = generate_college_mess_dataset(num_days=320, base_population=1600, seed=42)

    records = [
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
    db.bulk_save_objects(records)
    db.commit()
    print(f"Stored {len(records)} meal records in database.")

    print("Training baseline Random Forest Regression model with rolling chronological CV...")
    trainer = ModelTrainer()
    train_res = trainer.train_and_tune(df, tune_hyperparameters=True, n_iter_search=6)

    registry = ModelRegistry()
    version_tag = registry.save_model(
        model=train_res["model"],
        version_tag="RF-v1.0",
        metrics=train_res["metrics"],
        hyperparameters=train_res["best_params"],
        feature_importances=train_res["feature_importances"],
        training_records_count=len(df),
        make_active=True
    )
    print(f"Saved active model {version_tag} to registry.")
    print("Metrics:", train_res["metrics"])

    print("Pre-populating recent post-meal evaluation feedback records...")
    for rec in train_res["eval_records"][-45:]:
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
            notes="Biometric turnstile verification"
        ))
    db.commit()
    db.close()
    print("Seeding completed successfully!")


if __name__ == "__main__":
    seed()
