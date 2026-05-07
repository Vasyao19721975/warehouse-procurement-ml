import shutil
from pathlib import Path
from fastapi import UploadFile, File
from src.main import main as run_pipeline_main
from src.config import RAW_STOCKS_DIR
from src.main import main as run_pipeline_main
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

@app.post("/run-pipeline")
def run_pipeline():
    try:
        run_pipeline_main()

        return {
            "status": "ok",
            "message": "ML pipeline successfully finished. Artifacts uploaded to MinIO.",
            "artifacts": [
                "models/model.pkl",
                "outputs/final_recommendations.csv",
            ],
        }

    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }
        
@app.post("/upload-stock-and-run")
def upload_stock_and_run(file: UploadFile = File(...)):
    try:
        input_dir = Path("input")
        input_dir.mkdir(exist_ok=True)

        raw_stocks_dir = Path(RAW_STOCKS_DIR)
        raw_stocks_dir.mkdir(parents=True, exist_ok=True)

        input_file_path = input_dir / file.filename
        raw_file_path = raw_stocks_dir / file.filename

        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        shutil.copy(input_file_path, raw_file_path)

        run_pipeline_main()

        return {
            "status": "ok",
            "message": "Файл остатков загружен, pipeline выполнен, результат отправлен в MinIO.",
            "uploaded_file": file.filename,
            "artifacts": [
                "models/model.pkl",
                "outputs/final_recommendations.csv",
            ],
        }

    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }