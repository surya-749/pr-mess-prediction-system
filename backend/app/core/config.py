import os
from dataclasses import dataclass


@dataclass
class Settings:
    PROJECT_NAME: str = "AI Food Demand Forecasting Engine"
    API_PREFIX: str = "/ml"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mess_forecast.db")

    # ML Config
    BASE_STUDENT_POPULATION: int = 1600
    CHRONOLOGICAL_TEST_SIZE: float = 0.20
    DEFAULT_BUFFER_PERCENTAGE: float = 3.0


settings = Settings()
