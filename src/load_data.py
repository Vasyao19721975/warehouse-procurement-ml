import pandas as pd
import os
import re


def extract_date(filename: str):
    match = re.search(r'(\d{2}\.\d{2}\.\d{4})', filename)
    if match:
        return pd.to_datetime(match.group(1), dayfirst=True)
    return None


def detect_stock_time(filename: str):
    name = filename.lower()
    if "утро" in name or "аутро" in name:
        return "morning"
    if "вечер" in name:
        return "evening"
    return "unknown"


def load_stocks(folder_path: str) -> pd.DataFrame:
    all_data = []

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".xlsx"):
            full_path = os.path.join(folder_path, file_name)
            df = pd.read_excel(full_path)

            df.columns = [col.strip().lower() for col in df.columns]

            if not {"sku_id", "product", "qty"}.issubset(df.columns):
                print(f"Пропущен файл остатков {file_name}: нет нужных столбцов")
                continue

            df["date"] = extract_date(file_name)
            df["time_of_day"] = detect_stock_time(file_name)
            df = df.rename(columns={"qty": "stock"})

            all_data.append(df[["date", "time_of_day", "sku_id", "product", "stock"]])

    if not all_data:
        return pd.DataFrame(columns=["date", "time_of_day", "sku_id", "product", "stock"])

    result = pd.concat(all_data, ignore_index=True)
    return result


def load_supplies(folder_path: str) -> pd.DataFrame:
    all_data = []

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".xlsx"):
            full_path = os.path.join(folder_path, file_name)
            df = pd.read_excel(full_path)

            df.columns = [col.strip().lower() for col in df.columns]

            if not {"sku_id", "count"}.issubset(df.columns):
                print(f"Пропущен файл поставок {file_name}: нет нужных столбцов")
                continue

            df["date"] = extract_date(file_name)
            df = df.rename(columns={"count": "supply"})

            all_data.append(df[["date", "sku_id", "supply"]])

    if not all_data:
        return pd.DataFrame(columns=["date", "sku_id", "supply"])

    result = pd.concat(all_data, ignore_index=True)
    return result