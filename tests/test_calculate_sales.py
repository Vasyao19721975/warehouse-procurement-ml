import pandas as pd
from src.calculate_sales import build_final_dataset


def test_build_final_dataset():
    stocks_df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-02"],
        "sku_id": [1, 1],
        "product": ["A", "A"],
        "stock": [10, 8],
    })

    supplies_df = pd.DataFrame({
        "date": ["2024-01-02"],
        "sku_id": [1],
        "supply": [0],
    })

    result = build_final_dataset(stocks_df, supplies_df)

    assert not result.empty
    assert "sales" in result.columns
    assert result["sales"].iloc[1] == 2