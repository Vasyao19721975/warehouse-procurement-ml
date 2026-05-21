import os
import shutil
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse

from src.main import main as run_training_pipeline
from src.inference import run_inference
from src.config import (
    MODEL_PATH,
    OUTPUTS_DIR,
)
from src.inference import (
    INFERENCE_STOCKS_DIR,
    INFERENCE_OUTPUT_FILE,
)


app = FastAPI(
    title="Warehouse Procurement ML API",
    description="API for warehouse demand prediction and procurement recommendations",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Warehouse Procurement ML API is running"
    }


@app.get("/health")
def health():
    latest_exists = os.path.exists(INFERENCE_OUTPUT_FILE)

    return {
        "status": "ok",
        "model_exists": os.path.exists(MODEL_PATH),
        "model_path": MODEL_PATH,
        "latest_recommendations_exists": latest_exists,
        "latest_recommendations_path": INFERENCE_OUTPUT_FILE,
    }


@app.post("/run-training")
def run_training():
    try:
        run_training_pipeline()

        return {
            "status": "ok",
            "message": "Training pipeline finished successfully.",
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


@app.post("/upload-stock-and-inference")
def upload_stock_and_inference(file: UploadFile = File(...)):
    try:
        inference_dir = Path(INFERENCE_STOCKS_DIR)
        inference_dir.mkdir(parents=True, exist_ok=True)

        for old_file in inference_dir.glob("*.xlsx"):
            old_file.unlink()

        uploaded_file_path = inference_dir / file.filename

        with open(uploaded_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        run_inference()

        return {
            "status": "ok",
            "message": "Файл остатков загружен, inference выполнен, рекомендации сформированы и отправлены в MinIO.",
            "uploaded_file": file.filename,
            "latest_recommendations": INFERENCE_OUTPUT_FILE,
        }

    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }


@app.get("/recommendations/latest")
def get_latest_recommendations():
    if not os.path.exists(INFERENCE_OUTPUT_FILE):
        return {
            "status": "error",
            "message": "Latest recommendations file not found. Run inference first.",
        }

    return FileResponse(
        path=INFERENCE_OUTPUT_FILE,
        filename="latest_recommendations.csv",
        media_type="text/csv",
    )


@app.get("/recommendations/latest-json")
def get_latest_recommendations_json(limit: int = 20):
    if not os.path.exists(INFERENCE_OUTPUT_FILE):
        return {
            "status": "error",
            "message": "Latest recommendations file not found. Run inference first.",
        }

    df = pd.read_csv(INFERENCE_OUTPUT_FILE)

    return {
        "status": "ok",
        "count": len(df),
        "items": df.head(limit).to_dict(orient="records"),
    }