import os

from src.load_data import load_stocks, load_supplies
from src.preprocess import prepare_stocks, prepare_supplies, choose_main_stock_snapshot
from src.calculate_sales import build_final_dataset
from src.recommendation_pipeline import build_all_products
from src.ml_pipeline import (
    prepare_ml_data,
    train_sales_model,
    predict_sales,
    aggregate_predictions,
    add_ml_recommendations,
)
from src.config import (
    RAW_STOCKS_DIR,
    RAW_SUPPLIES_DIR,
    PROCESSED_DATA_DIR,
    OUTPUTS_DIR,
    ALL_STOCKS_RAW_FILE,
    ALL_SUPPLIES_FILE,
    ALL_STOCKS_MAIN_FILE,
    FINAL_DATASET_FILE,
    FINAL_OUTPUT_FILE,
    TARGET_DAYS,
)


def main():
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    print("Загрузка остатков...")
    stocks = load_stocks(RAW_STOCKS_DIR)
    print(f"Загружено строк остатков: {len(stocks)}")

    print("Загрузка поставок...")
    supplies = load_supplies(RAW_SUPPLIES_DIR)
    print(f"Загружено строк поставок: {len(supplies)}")

    print("Очистка остатков...")
    stocks = prepare_stocks(stocks)

    print("Очистка поставок...")
    supplies = prepare_supplies(supplies)

    print("Выбор основных остатков по дням...")
    stocks_main = choose_main_stock_snapshot(stocks)

    print("Построение финального датасета...")
    final_df = build_final_dataset(stocks_main, supplies)

    print("Построение рекомендаций по закупке...")
    all_products = build_all_products(final_df, TARGET_DAYS)

    print("Подготовка данных для ML...")
    ml_df = prepare_ml_data(final_df)

    print("Обучение ML модели...")
    model, mae = train_sales_model(ml_df)
    print(f"MAE модели: {mae:.4f}")

    print("Прогноз продаж через ML...")
    predicted_df = predict_sales(ml_df, model)
    predicted_sales = aggregate_predictions(predicted_df)

    print("Формирование ML-рекомендаций...")
    all_products = add_ml_recommendations(
        all_products=all_products,
        predicted_sales=predicted_sales,
        target_days=TARGET_DAYS,
    )

    stocks.to_csv(ALL_STOCKS_RAW_FILE, index=False, encoding="utf-8-sig")
    supplies.to_csv(ALL_SUPPLIES_FILE, index=False, encoding="utf-8-sig")
    stocks_main.to_csv(ALL_STOCKS_MAIN_FILE, index=False, encoding="utf-8-sig")
    final_df.to_csv(FINAL_DATASET_FILE, index=False, encoding="utf-8-sig")
    all_products.to_csv(FINAL_OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("Готово.")
    print(f"Файлы сохранены в: {PROCESSED_DATA_DIR}")
    print(f"Итоговые рекомендации сохранены в: {FINAL_OUTPUT_FILE}")
    print(all_products.head(20))


if __name__ == "__main__":
    main()