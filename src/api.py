import os
import joblib
import pandas as pd

from fastapi import FastAPI
from pydantic import BaseModel

from src.config import MODEL_PATH

app = FastAPI(
    title="Warehouse Procurement ML API",
    description="API for warehouse demand prediction and procurement recommendations",
    version="1.0.0",
)


class PredictionRequest(BaseModel):
    lag_1: float
    lag_2: float
    stock: float
    target_days: int = 7


@app.get("/")
def root():
    return {
        "message": "Warehouse Procurement ML API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_exists": os.path.exists(MODEL_PATH),
        "model_path": MODEL_PATH,
    }


@app.post("/predict")
def predict(request: PredictionRequest):
    if not os.path.exists(MODEL_PATH):
        return {
            "status": "error",
            "message": "Model file not found. Run training pipeline first."
        }

    model = joblib.load(MODEL_PATH)

    features = pd.DataFrame([{
        "lag_1": request.lag_1,
        "lag_2": request.lag_2,
    }])

    predicted_sales = float(model.predict(features)[0])

    ml_recommended_order = max(
        0,
        predicted_sales * request.target_days - request.stock
    )

    return {
        "status": "ok",
        "predicted_sales": predicted_sales,
        "ml_recommended_order": ml_recommended_order,
    }