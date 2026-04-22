import os
from load_data import load_stocks, load_supplies
from preprocess import prepare_stocks, prepare_supplies, choose_main_stock_snapshot
from calculate_sales import build_final_dataset

import pandas as pd


def main():
    stocks_folder = os.path.join("data", "raw", "stocks")
    supplies_folder = os.path.join("data", "raw", "supplies")
    processed_folder = os.path.join("data", "processed")

    os.makedirs(processed_folder, exist_ok=True)

    print("Загрузка остатков...")
    stocks = load_stocks(stocks_folder)
    print(f"Загружено строк остатков: {len(stocks)}")

    print("Загрузка поставок...")
    supplies = load_supplies(supplies_folder)
    print(f"Загружено строк поставок: {len(supplies)}")

    print("Очистка остатков...")
    stocks = prepare_stocks(stocks)

    print("Очистка поставок...")
    supplies = prepare_supplies(supplies)

    print("Выбор основных остатков по дням...")
    stocks_main = choose_main_stock_snapshot(stocks)

    print("Построение финального датасета...")
    final_df = build_final_dataset(stocks_main, supplies)

    stocks.to_csv(os.path.join(processed_folder, "all_stocks_raw.csv"), index=False, encoding="utf-8-sig")
    supplies.to_csv(os.path.join(processed_folder, "all_supplies.csv"), index=False, encoding="utf-8-sig")
    stocks_main.to_csv(os.path.join(processed_folder, "all_stocks_main.csv"), index=False, encoding="utf-8-sig")
    final_df.to_csv(os.path.join(processed_folder, "final_dataset.csv"), index=False, encoding="utf-8-sig")

    print("Готово.")
    print("Файлы сохранены в папке data/processed")
    print(final_df.head(20))


if __name__ == "__main__":
    main()