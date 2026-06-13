import os
import shutil
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from src.evaluate_forecast import run_forecast_evaluation
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

EVALUATION_RESULT_FILE = Path(OUTPUTS_DIR) / "evaluation_result.csv"
EVALUATION_METRICS_FILE = Path(OUTPUTS_DIR) / "evaluation_metrics.csv"


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
    
@app.post("/evaluate-forecast")
def evaluate_forecast():
    """
    Запускает проверку качества прогноза.

    Данные берутся из:
    data/evaluation/start_stock/
    data/evaluation/end_stock/
    data/evaluation/supplies/

    Результаты сохраняются в:
    outputs/evaluation_result.csv
    outputs/evaluation_metrics.csv
    """
    result = run_forecast_evaluation()
    return result

@app.get("/evaluation/result")
def download_evaluation_result():
    """
    Скачивание подробного отчёта проверки прогноза.

    Файл содержит:
    фактический расход,
    прогноз модели,
    ошибку,
    уровень ошибки,
    комментарий по каждой товарной позиции.
    """
    if not EVALUATION_RESULT_FILE.exists():
        return {
            "status": "error",
            "message": "Файл evaluation_result.csv не найден. Сначала запустите /evaluate-forecast.",
        }

    return FileResponse(
        path=EVALUATION_RESULT_FILE,
        filename="evaluation_result.csv",
        media_type="text/csv",
    )
    
@app.get("/evaluation/metrics")
def download_evaluation_metrics():
    """
    Скачивание файла с метриками проверки прогноза.

    Файл содержит MAE, RMSE и MAPE
    по прогнозу спроса и расчётному остатку.
    """
    if not EVALUATION_METRICS_FILE.exists():
        return {
            "status": "error",
            "message": "Файл evaluation_metrics.csv не найден. Сначала запустите /evaluate-forecast.",
        }

    return FileResponse(
        path=EVALUATION_METRICS_FILE,
        filename="evaluation_metrics.csv",
        media_type="text/csv",
    )

@app.get("/recommendations-view", response_class=HTMLResponse)
def recommendations_view(status: str = "all"):
    """
    Простая HTML-страница для просмотра рекомендаций по закупке.

    status:
    - all
    - no_order
    - recommended_order
    - critical_order

    limit:
    - количество строк для отображения на странице
    """
    if not os.path.exists(INFERENCE_OUTPUT_FILE):
        return HTMLResponse(
            content="""
            <html>
                <head>
                    <meta charset="utf-8">
                    <title>Рекомендации не найдены</title>
                </head>
                <body>
                    <h2>Файл рекомендаций не найден</h2>
                    <p>Сначала запустите inference через /upload-stock-and-inference.</p>
                </body>
            </html>
            """,
            status_code=404,
        )

    df = pd.read_csv(INFERENCE_OUTPUT_FILE)

    status_column = "ml_decision"

    if status_column not in df.columns:
        return HTMLResponse(
            content=f"""
            <html>
                <head>
                    <meta charset="utf-8">
                    <title>Ошибка структуры файла</title>
                </head>
                <body>
                    <h2>В файле не найдена колонка ml_decision</h2>
                    <p>Найдены колонки:</p>
                    <pre>{list(df.columns)}</pre>
                </body>
            </html>
            """,
            status_code=500,
        )

    total_count = len(df)
    no_order_count = int((df[status_column] == "no_order").sum())
    recommended_count = int((df[status_column] == "recommended_order").sum())
    critical_count = int((df[status_column] == "critical_order").sum())

    if status != "all":
        df = df[df[status_column] == status]

    # Сортируем так, чтобы товары к закупке были выше
    if "ml_recommended_order" in df.columns:
        df = df.sort_values(
            by="ml_recommended_order",
            ascending=False,
        )

    columns_to_show = [
        "sku_id",
        "product",
        "stock",
        "predicted_sales",
        "days_of_stock_ml",
        "safety_stock",
        "ml_recommended_order",
        "ml_decision",
    ]

    existing_columns = [column for column in columns_to_show if column in df.columns]
    df_view = df[existing_columns].copy()

    rename_columns = {
        "sku_id": "SKU",
        "product": "Товар",
        "stock": "Остаток",
        "predicted_sales": "Прогноз спроса",
        "days_of_stock_ml": "Запас в днях",
        "safety_stock": "Страховой запас",
        "ml_recommended_order": "Рекомендовано закупить",
        "ml_decision": "Решение",
    }

    df_view = df_view.rename(columns=rename_columns)

    table_html = df_view.to_html(
        index=False,
        classes="data-table",
        border=0,
    )

    html = f"""
    <html>
        <head>
            <meta charset="utf-8">
            <title>Рекомендации по закупке</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 30px;
                    background-color: #f4f6f8;
                    color: #222;
                }}

                h1 {{
                    margin-bottom: 5px;
                }}

                .subtitle {{
                    color: #666;
                    margin-bottom: 25px;
                }}

                .cards {{
                    display: flex;
                    gap: 15px;
                    margin-bottom: 20px;
                    flex-wrap: wrap;
                }}

                .card {{
                    background: white;
                    padding: 16px 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    min-width: 190px;
                }}

                .card-title {{
                    font-size: 14px;
                    color: #666;
                }}

                .card-value {{
                    font-size: 28px;
                    font-weight: bold;
                    margin-top: 6px;
                }}

                .filters {{
                    margin: 20px 0;
                }}

                .filters a {{
                    display: inline-block;
                    padding: 9px 13px;
                    margin-right: 8px;
                    background: #ffffff;
                    border-radius: 6px;
                    text-decoration: none;
                    color: #222;
                    border: 1px solid #ccc;
                }}

                .filters a:hover {{
                    background: #e8eef7;
                }}

                .active {{
                    background: #2f6fed !important;
                    color: white !important;
                    border-color: #2f6fed !important;
                }}

                table.data-table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    font-size: 14px;
                }}

                table.data-table th {{
                    background: #1f2937;
                    color: white;
                    padding: 10px;
                    text-align: left;
                    position: sticky;
                    top: 0;
                }}

                table.data-table td {{
                    padding: 8px 10px;
                    border-bottom: 1px solid #ddd;
                }}

                table.data-table tr:hover {{
                    background: #f0f4ff;
                }}

                .note {{
                    margin-top: 15px;
                    color: #666;
                    font-size: 14px;
                }}

                .status {{
                    margin: 15px 0;
                    font-weight: bold;
                }}
            </style>
        </head>

        <body>
            <h1>Рекомендации по закупке</h1>
            <div class="subtitle">
                Просмотр результата ML-прогноза из файла inference_recommendations.csv
            </div>

            <div class="cards">
                <div class="card">
                    <div class="card-title">Всего товаров</div>
                    <div class="card-value">{total_count}</div>
                </div>

                <div class="card">
                    <div class="card-title">Без закупки</div>
                    <div class="card-value">{no_order_count}</div>
                </div>

                <div class="card">
                    <div class="card-title">Рекомендуется закупка</div>
                    <div class="card-value">{recommended_count}</div>
                </div>

                <div class="card">
                    <div class="card-title">Критическая закупка</div>
                    <div class="card-value">{critical_count}</div>
                </div>
            </div>

            <div class="filters">
                <a class="{ 'active' if status == 'all' else '' }" href="/recommendations-view?status=all">Все</a>
                <a class="{ 'active' if status == 'no_order' else '' }" href="/recommendations-view?status=no_order">no_order</a>
                <a class="{ 'active' if status == 'recommended_order' else '' }" href="/recommendations-view?status=recommended_order">recommended_order</a>
                <a class="{ 'active' if status == 'critical_order' else '' }" href="/recommendations-view?status=critical_order">critical_order</a>
            </div>

            <div class="status">
                Текущий фильтр: {status}. Отображается строк: {len(df_view)}
            </div>

            {table_html}

            <div class="note">
                Отображаются все строки выбранного фильтра.
                Полный CSV доступен через endpoint /recommendations/latest.
            </div>
        </body>
    </html>
    """

    return HTMLResponse(content=html)