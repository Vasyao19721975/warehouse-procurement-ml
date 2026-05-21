import os
import joblib
import pandas as pd

from src.s3_client import upload_inference_artifacts
from src.load_data import load_stocks
from src.preprocess import prepare_stocks, choose_main_stock_snapshot
from src.config import (
    MODEL_PATH,
    FINAL_DATASET_FILE,
    PROCESSED_DATA_DIR,
    OUTPUTS_DIR,
    TARGET_DAYS,
)


INFERENCE_STOCKS_DIR = "data/inference/stocks"
INFERENCE_OUTPUT_FILE = os.path.join(OUTPUTS_DIR, "inference_recommendations.csv")
INFERENCE_HISTORY_FILE = os.path.join(PROCESSED_DATA_DIR, "inference_history.csv")


def load_model():
    return joblib.load(MODEL_PATH)


def load_history():
    if os.path.exists(INFERENCE_HISTORY_FILE):
        history_df = pd.read_csv(INFERENCE_HISTORY_FILE)
        print(f"Загружена обновляемая история: {INFERENCE_HISTORY_FILE}")
    else:
        history_df = pd.read_csv(FINAL_DATASET_FILE)
        print(f"Загружена базовая история: {FINAL_DATASET_FILE}")

    history_df["date"] = pd.to_datetime(history_df["date"])
    history_df["sku_id"] = history_df["sku_id"].astype(str).str.strip()

    return history_df


def load_new_stock():
    stocks = load_stocks(INFERENCE_STOCKS_DIR)
    stocks = prepare_stocks(stocks)
    stocks = choose_main_stock_snapshot(stocks)

    stocks["date"] = pd.to_datetime(stocks["date"])
    stocks["sku_id"] = stocks["sku_id"].astype(str).str.strip()

    return stocks


def build_features(new_stock_df: pd.DataFrame, history_df: pd.DataFrame) -> pd.DataFrame:
    new_stock_df = new_stock_df.copy()
    history_df = history_df.copy()

    new_stock_df["sku_id"] = new_stock_df["sku_id"].astype(str).str.strip()
    history_df["sku_id"] = history_df["sku_id"].astype(str).str.strip()

    lag_features = (
        history_df.sort_values(["sku_id", "date"])
        .groupby("sku_id")["sales"]
        .agg(
            lag_1=lambda x: x.iloc[-1] if len(x) >= 1 else 0,
            lag_2=lambda x: x.iloc[-2] if len(x) >= 2 else 0,
            rolling_mean_3=lambda x: x.tail(3).mean() if len(x) > 0 else 0,
        )
        .reset_index()
    )

    result = new_stock_df.merge(lag_features, on="sku_id", how="left")

    result["lag_1"] = result["lag_1"].fillna(0)
    result["lag_2"] = result["lag_2"].fillna(0)
    result["rolling_mean_3"] = result["rolling_mean_3"].fillna(0)

    return result


def make_recommendations(features_df: pd.DataFrame, model) -> pd.DataFrame:
    result = features_df.copy()

    result["predicted_sales"] = model.predict(
        result[["stock", "lag_1", "lag_2", "rolling_mean_3"]]
    )

    result["safety_stock"] = result["predicted_sales"] * 2

    result["ml_recommended_order"] = (
        result["predicted_sales"] * TARGET_DAYS
        + result["safety_stock"]
        - result["stock"]
    )

    result["ml_recommended_order"] = result["ml_recommended_order"].apply(
        lambda x: max(0, round(x))
    )

    result["days_of_stock_ml"] = result.apply(
        lambda row: row["stock"] / row["predicted_sales"]
        if row["predicted_sales"] > 0
        else float("inf"),
        axis=1,
    )
    
    def decide_ml_order(row):
        if row["ml_recommended_order"] > 0 and row["days_of_stock_ml"] <= 5:
            return "critical_order"
        if row["ml_recommended_order"] > 0:
            return "recommended_order"
        if row["days_of_stock_ml"] <= 5:
            return "low_stock"
        return "no_order"


    result["ml_decision"] = result.apply(decide_ml_order, axis=1)



    return result[
        [
            "date",
            "sku_id",
            "product",
            "stock",
            "lag_1",
            "lag_2",
            "rolling_mean_3",
            "predicted_sales",
            "days_of_stock_ml",
            "ml_recommended_order",
            "safety_stock",
            "ml_decision",
        ]
    ]


def update_history(
    history_df: pd.DataFrame,
    new_stock_df: pd.DataFrame,
    recommendations: pd.DataFrame,
) -> pd.DataFrame:
    history_df = history_df.copy()
    new_stock_df = new_stock_df.copy()
    recommendations = recommendations.copy()

    new_stock_df["sku_id"] = new_stock_df["sku_id"].astype(str).str.strip()
    history_df["sku_id"] = history_df["sku_id"].astype(str).str.strip()
    recommendations["sku_id"] = recommendations["sku_id"].astype(str).str.strip()

    previous_stock = (
        history_df.sort_values(["sku_id", "date"])
        .groupby("sku_id", as_index=False)
        .last()[["sku_id", "stock"]]
        .rename(columns={"stock": "prev_stock"})
    )

    new_rows = new_stock_df.merge(previous_stock, on="sku_id", how="left")
    new_rows = new_rows.merge(
        recommendations[["sku_id", "predicted_sales"]],
        on="sku_id",
        how="left",
    )

    new_rows["prev_stock"] = new_rows["prev_stock"].fillna(new_rows["stock"])

    # В inference-режиме поставки неизвестны, поэтому ставим 0.
    new_rows["supply"] = 0

    # Восстановление продаж по изменению остатка:
    # если остаток уменьшился — считаем это продажами.
    # если остаток вырос — это могла быть поставка, но в inference поставки неизвестны.
    new_rows["sales"] = new_rows["prev_stock"] - new_rows["stock"]
    new_rows["sales"] = new_rows["sales"].apply(lambda x: max(0, x))

    # Если продажи восстановить нельзя, используем прогноз как приближение.
    new_rows["sales"] = new_rows.apply(
        lambda row: row["predicted_sales"]
        if row["sales"] == 0 and pd.notna(row["predicted_sales"])
        else row["sales"],
        axis=1,
    )

    new_rows = new_rows[
        [
            "date",
            "time_of_day",
            "sku_id",
            "product",
            "stock",
            "supply",
            "prev_stock",
            "sales",
        ]
    ]

    updated_history = pd.concat([history_df, new_rows], ignore_index=True)

    updated_history = updated_history.drop_duplicates(
        subset=["date", "sku_id"],
        keep="last",
    )

    updated_history = updated_history.sort_values(["date", "sku_id"])

    return updated_history


def run_inference():
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

    model = load_model()
    history_df = load_history()
    new_stock_df = load_new_stock()

    features_df = build_features(new_stock_df, history_df)
    recommendations = make_recommendations(features_df, model)

    recommendations.to_csv(
        INFERENCE_OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    updated_history = update_history(
        history_df=history_df,
        new_stock_df=new_stock_df,
        recommendations=recommendations,
    )

    updated_history.to_csv(
        INFERENCE_HISTORY_FILE,
        index=False,
        encoding="utf-8-sig",
    )
    
    from src.config import RUN_DATE
    
    recommendation_date = (
    RUN_DATE
    if RUN_DATE != "manual_run"
    else str(recommendations["date"].max().date())
    )

    upload_inference_artifacts(
    recommendations_path=INFERENCE_OUTPUT_FILE,
    history_path=INFERENCE_HISTORY_FILE,
    recommendation_date=recommendation_date,
    )

    print(f"Рекомендации сохранены: {INFERENCE_OUTPUT_FILE}")
    print(f"История обновлена: {INFERENCE_HISTORY_FILE}")
    print(recommendations.head(20))


if __name__ == "__main__":
    run_inference()