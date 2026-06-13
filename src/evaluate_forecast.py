from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


BASE_DIR = Path(__file__).resolve().parent.parent

EVALUATION_DIR = BASE_DIR / "data" / "evaluation"
START_STOCK_DIR = EVALUATION_DIR / "start_stock"
END_STOCK_DIR = EVALUATION_DIR / "end_stock"
SUPPLIES_DIR = EVALUATION_DIR / "supplies"

OUTPUT_DIR = BASE_DIR / "outputs"
MODEL_PATH = BASE_DIR / "models" / "model.pkl"

OUTPUT_DIR.mkdir(exist_ok=True)


def find_single_excel_file(folder: Path) -> Path:
    """
    Ищет ровно один Excel-файл в указанной папке.
    Используется для начальных и конечных остатков.
    """
    files = list(folder.glob("*.xlsx")) + list(folder.glob("*.xls"))

    if len(files) == 0:
        raise FileNotFoundError(f"В папке {folder} не найден Excel-файл")

    if len(files) > 1:
        raise ValueError(
            f"В папке {folder} должен быть только один Excel-файл. "
            f"Сейчас найдено файлов: {len(files)}"
        )

    return files[0]


def find_all_excel_files(folder: Path) -> list[Path]:
    """
    Ищет все Excel-файлы в указанной папке.
    Используется для поставок.
    """
    if not folder.exists():
        return []

    return list(folder.glob("*.xlsx")) + list(folder.glob("*.xls"))


def load_excel_file(file_path: Path) -> pd.DataFrame:
    """
    Загружает Excel-файл и приводит названия колонок к нижнему регистру.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    df = pd.read_excel(file_path)
    df.columns = [str(col).strip().lower() for col in df.columns]

    return df


def prepare_stock_file(file_path: Path, stock_column_name: str) -> pd.DataFrame:
    """
    Подготавливает файл остатков.

    Поддерживаемые варианты колонок:
    sku / sku_id
    product
    count / qty

    stock_column_name:
    start_stock или end_stock
    """
    df = load_excel_file(file_path)

    if "sku" in df.columns:
        sku_col = "sku"
    elif "sku_id" in df.columns:
        sku_col = "sku_id"
    else:
        raise ValueError(
            f"В файле {file_path.name} не найдена колонка sku или sku_id. "
            f"Найдены колонки: {list(df.columns)}"
        )

    if "count" in df.columns:
        count_col = "count"
    elif "qty" in df.columns:
        count_col = "qty"
    else:
        raise ValueError(
            f"В файле {file_path.name} не найдена колонка count или qty. "
            f"Найдены колонки: {list(df.columns)}"
        )

    if "product" not in df.columns:
        raise ValueError(
            f"В файле {file_path.name} не найдена колонка product. "
            f"Найдены колонки: {list(df.columns)}"
        )

    df = df.rename(
        columns={
            sku_col: "sku_id",
            count_col: stock_column_name,
        }
    )

    df = df[["sku_id", "product", stock_column_name]]

    df = df.dropna(subset=["sku_id"])

    df = (
        df.groupby(["sku_id", "product"], as_index=False)[stock_column_name]
        .sum()
    )

    return df


def prepare_supply_files(file_paths: list[Path]) -> pd.DataFrame:
    """
    Подготавливает один или несколько файлов поставок.

    Поддерживаемые варианты колонок:
    sku / sku_id
    count / qty

    Если файлов несколько, поставки по одному sku суммируются.
    """
    supply_dfs = []

    for file_path in file_paths:
        df = load_excel_file(file_path)

        if "sku" in df.columns:
            sku_col = "sku"
        elif "sku_id" in df.columns:
            sku_col = "sku_id"
        else:
            print(
                f"Файл поставки {file_path.name} пропущен, "
                f"так как не найдена колонка sku или sku_id. "
                f"Найдены колонки: {list(df.columns)}"
            )
            continue

        if "count" in df.columns:
            count_col = "count"
        elif "qty" in df.columns:
            count_col = "qty"
        else:
            print(
                f"Файл поставки {file_path.name} пропущен, "
                f"так как не найдена колонка count или qty. "
                f"Найдены колонки: {list(df.columns)}"
            )
            continue

        df = df.rename(
            columns={
                sku_col: "sku_id",
                count_col: "supply",
            }
        )

        df = df[["sku_id", "supply"]]
        df = df.dropna(subset=["sku_id"])

        supply_dfs.append(df)

    if not supply_dfs:
        return pd.DataFrame(columns=["sku_id", "supply"])

    supplies = pd.concat(supply_dfs, ignore_index=True)

    supplies = (
        supplies.groupby("sku_id", as_index=False)["supply"]
        .sum()
    )

    return supplies


def calculate_metrics(y_true, y_pred) -> dict:
    """
    Рассчитывает основные метрики качества.
    MAPE считается только по строкам, где фактическое значение больше 0.
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    mae = mean_absolute_error(y_true, y_pred)

    try:
        rmse = mean_squared_error(y_true, y_pred, squared=False)
    except TypeError:
        # Для старых версий scikit-learn
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    non_zero_mask = y_true != 0

    if non_zero_mask.sum() > 0:
        mape = (
            np.mean(
                np.abs(
                    (y_true[non_zero_mask] - y_pred[non_zero_mask])
                    / y_true[non_zero_mask]
                )
            )
            * 100
        )
    else:
        mape = np.nan

    return {
        "MAE": round(float(mae), 4),
        "RMSE": round(float(rmse), 4),
        "MAPE_percent": round(float(mape), 4) if not np.isnan(mape) else None,
    }


def build_model_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Формирует признаки для модели.

    В твоём проекте по сводке модель использует:
    stock, lag_1, lag_2, rolling_mean_3.

    Для проверки мы берём текущий остаток как stock.
    Исторические лаги пока заполняем нулями, чтобы проверить сам механизм evaluation.
    После первого успешного запуска можно будет улучшить этот блок через final_dataset.csv.
    """
    df["stock"] = df["start_stock"]

    df["lag_1"] = 0
    df["lag_2"] = 0
    df["rolling_mean_3"] = 0

    features = df[["stock", "lag_1", "lag_2", "rolling_mean_3"]]

    return features


def run_forecast_evaluation() -> dict:
    """
    Главная функция проверки прогноза.

    Логика:
    начальные остатки + поставки - конечные остатки = фактические продажи

    Затем:
    прогноз модели сравнивается с фактическими продажами.
    """
    start_stock_file = find_single_excel_file(START_STOCK_DIR)
    end_stock_file = find_single_excel_file(END_STOCK_DIR)
    supply_files = find_all_excel_files(SUPPLIES_DIR)

    print(f"Файл начальных остатков: {start_stock_file.name}")
    print(f"Файл конечных остатков: {end_stock_file.name}")

    if supply_files:
        print("Файлы поставок:")
        for file_path in supply_files:
            print(f"- {file_path.name}")
    else:
        print("Файлы поставок не найдены. Поставки будут считаться равными 0.")

    start_stock = prepare_stock_file(start_stock_file, "start_stock")
    end_stock = prepare_stock_file(end_stock_file, "end_stock")
    supplies = prepare_supply_files(supply_files)

    df = start_stock.merge(
        end_stock[["sku_id", "end_stock"]],
        on="sku_id",
        how="inner",
    )

    df = df.merge(
        supplies,
        on="sku_id",
        how="left",
    )

    df["supply"] = df["supply"].fillna(0)

    # Фактические продажи / расход товара за период
    df["actual_sales_raw"] = (
        df["start_stock"] + df["supply"] - df["end_stock"]
    )

    # Проблема данных: остаток вырос больше, чем позволяют указанные поставки
    df["data_issue"] = df["actual_sales_raw"] < 0

    # Для расчёта метрик отрицательные продажи заменяем на 0
    df["actual_sales"] = df["actual_sales_raw"].clip(lower=0)

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Модель не найдена: {MODEL_PATH}")

    model = joblib.load(MODEL_PATH)

    features = build_model_features(df)

    predicted_sales = model.predict(features)

    df["predicted_sales"] = np.maximum(predicted_sales, 0).round(2)

    df["predicted_end_stock"] = (
        df["start_stock"] + df["supply"] - df["predicted_sales"]
    )

    df["predicted_end_stock"] = df["predicted_end_stock"].clip(lower=0).round(2)

    df["abs_error"] = (
        df["actual_sales"] - df["predicted_sales"]
    ).abs().round(2)
    
    def define_error_level(row):
        if row["data_issue"]:
            return "data_issue"

        if row["abs_error"] <= 1:
            return "good"

        if row["abs_error"] <= 5:
            return "medium"
        
        return "bad"


    def define_comment(row):
        if row["data_issue"]:
            return "Возможная проблема входных данных"

        if row["abs_error"] <= 1:
            return "Корректный прогноз"

        if row["abs_error"] <= 5:
         return "Повышенная ошибка прогноза"

        return "Значительное отклонение прогноза"


    df["error_level"] = df.apply(define_error_level, axis=1)
    df["comment"] = df.apply(define_comment, axis=1)

    sales_metrics = calculate_metrics(
        df["actual_sales"],
        df["predicted_sales"],
    )

    stock_metrics = calculate_metrics(
        df["end_stock"],
        df["predicted_end_stock"],
    )

    metrics_df = pd.DataFrame(
        [
            {
                "target": "sales",
                **sales_metrics,
            },
            {
                "target": "stock",
                **stock_metrics,
            },
        ]
    )

    result_columns = [
    "sku_id",
    "product",
    "start_stock",
    "supply",
    "end_stock",
    "actual_sales_raw",
    "data_issue",
    "actual_sales",
    "predicted_sales",
    "predicted_end_stock",
    "abs_error",
    "error_level",
    "comment",
    ]

    result_df = df[result_columns]

    evaluation_result_path = OUTPUT_DIR / "evaluation_result.csv"
    evaluation_metrics_path = OUTPUT_DIR / "evaluation_metrics.csv"

    result_df.to_csv(
        evaluation_result_path,
        index=False,
        encoding="utf-8-sig",
    )

    metrics_df.to_csv(
        evaluation_metrics_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("\nПроверка завершена.")
    print(f"Строк в отчёте: {len(result_df)}")
    print(f"Строк с проблемами данных: {int(result_df['data_issue'].sum())}")
    print(f"Файл результата: {evaluation_result_path}")
    print(f"Файл метрик: {evaluation_metrics_path}")

    print("\nМетрики:")
    print(metrics_df)

    return {
        "status": "success",
        "message": "Forecast evaluation completed",
        "rows_count": int(len(result_df)),
        "problem_rows_count": int(result_df["data_issue"].sum()),
        "evaluation_result_file": str(evaluation_result_path),
        "evaluation_metrics_file": str(evaluation_metrics_path),
        "metrics": metrics_df.to_dict(orient="records"),
    }


if __name__ == "__main__":
    run_forecast_evaluation()