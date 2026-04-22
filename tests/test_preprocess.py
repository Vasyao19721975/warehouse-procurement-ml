import pandas as pd
from src.preprocess import prepare_stocks, prepare_supplies


def test_prepare_stocks():
    df = pd.DataFrame({
        "sku_id": [1, 1],
        "date": ["2024-01-01", "2024-01-02"],
        "stock": [10, 15],
        "product": ["A", "A"]
    })

    result = prepare_stocks(df)

    assert not result.empty
    assert "stock" in result.columns


def test_prepare_supplies():
    df = pd.DataFrame({
        "sku_id": [1],
        "date": ["2024-01-01"],
        "supply": [5],
        "product": ["A"]
    })

    result = prepare_supplies(df)

    assert not result.empty
    assert "supply" in result.columns