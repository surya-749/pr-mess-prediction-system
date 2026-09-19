from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.api.routes import router as ml_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered food demand forecasting engine for college messes using Random Forest Regression.",
    version="1.0.0"
)

# CORS configuration for local React / Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include ML router
app.include_router(ml_router, prefix=settings.API_PREFIX, tags=["ML Engine"])


@app.get("/")
def root():
    return {
        "message": "AI Food Demand Forecasting Engine API",
        "docs": "/docs",
        "endpoints": {
            "predict": f"{settings.API_PREFIX}/predict",
            "train": f"{settings.API_PREFIX}/train",
            "evaluation": f"{settings.API_PREFIX}/evaluation",
            "features": f"{settings.API_PREFIX}/features",
            "model_status": f"{settings.API_PREFIX}/model-status",
            "food_requirement": f"{settings.API_PREFIX}/food-requirement",
            "drift": f"{settings.API_PREFIX}/drift",
            "feedback": f"{settings.API_PREFIX}/feedback",
            "seed_data": f"{settings.API_PREFIX}/seed-data"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
