import pandas as pd
from src.ml_pipeline import prepare_ml_data, train_sales_model


def test_prepare_ml_data():
    df = pd.DataFrame({
        "sku_id": [1, 1, 1],
        "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "sales": [5, 6, 7]
    })

    result = prepare_ml_data(df)

    assert not result.empty
    assert "lag_1" in result.columns
    assert "lag_2" in result.columns


def test_train_sales_model():
    df = pd.DataFrame({
        "sku_id": [1, 1, 1, 1],
        "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
        "sales": [5, 6, 7, 8]
    })

    df = prepare_ml_data(df)

    model, mae = train_sales_model(df)

    assert model is not None
    assert mae >= 0