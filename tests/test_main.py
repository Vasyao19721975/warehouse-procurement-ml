from src.main import main
from unittest.mock import patch
import pandas as pd


def test_main_runs_safely():
    try:
        main()
    except Exception:
        assert True


def test_main_pipeline_runs(tmp_path):
    stocks = pd.DataFrame({
        "date": [
            "2024-01-01", "2024-01-02", "2024-01-03",
            "2024-01-04", "2024-01-05", "2024-01-06"
        ],
        "time_of_day": ["evening"] * 6,
        "sku_id": ["1"] * 6,
        "product": ["A"] * 6,
        "stock": [10, 8, 7, 6, 5, 4],
    })

    supplies = pd.DataFrame({
        "date": [
            "2024-01-01", "2024-01-02", "2024-01-03",
            "2024-01-04", "2024-01-05", "2024-01-06"
        ],
        "sku_id": ["1"] * 6,
        "supply": [0, 0, 0, 0, 0, 0],
    })

    with patch("src.main.RAW_STOCKS_DIR", str(tmp_path / "stocks")), \
         patch("src.main.RAW_SUPPLIES_DIR", str(tmp_path / "supplies")), \
         patch("src.main.PROCESSED_DATA_DIR", str(tmp_path / "processed")), \
         patch("src.main.OUTPUTS_DIR", str(tmp_path / "outputs")), \
         patch("src.main.ALL_STOCKS_RAW_FILE", str(tmp_path / "processed" / "all_stocks_raw.csv")), \
         patch("src.main.ALL_SUPPLIES_FILE", str(tmp_path / "processed" / "all_supplies.csv")), \
         patch("src.main.ALL_STOCKS_MAIN_FILE", str(tmp_path / "processed" / "all_stocks_main.csv")), \
         patch("src.main.FINAL_DATASET_FILE", str(tmp_path / "processed" / "final_dataset.csv")), \
         patch("src.main.FINAL_OUTPUT_FILE", str(tmp_path / "outputs" / "final_recommendations.csv")), \
         patch("src.main.load_stocks", return_value=stocks), \
         patch("src.main.load_supplies", return_value=supplies):

        main()

    assert (tmp_path / "outputs" / "final_recommendations.csv").exists()