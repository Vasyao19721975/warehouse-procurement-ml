import pandas as pd

from src.inference import build_features, make_recommendations


class DummyModel:
    def predict(self, X):
        return [2.0 for _ in range(len(X))]


def test_build_features():
    new_stock_df = pd.DataFrame({
        "date": pd.to_datetime(["2026-04-22"]),
        "sku_id": ["1001"],
        "product": ["Test product"],
        "stock": [5],
    })

    history_df = pd.DataFrame({
        "date": pd.to_datetime([
            "2026-04-20",
            "2026-04-21",
        ]),
        "sku_id": ["1001", "1001"],
        "sales": [1, 3],
    })

    result = build_features(new_stock_df, history_df)

    assert "lag_1" in result.columns
    assert "lag_2" in result.columns
    assert "rolling_mean_3" in result.columns
    assert result.loc[0, "lag_1"] == 3
    assert result.loc[0, "lag_2"] == 1


def test_make_recommendations():
    features_df = pd.DataFrame({
        "date": pd.to_datetime(["2026-04-22"]),
        "sku_id": ["1001"],
        "product": ["Test product"],
        "stock": [5],
        "lag_1": [3],
        "lag_2": [1],
        "rolling_mean_3": [2],
    })

    result = make_recommendations(features_df, DummyModel())

    assert "predicted_sales" in result.columns
    assert "ml_recommended_order" in result.columns
    assert "safety_stock" in result.columns
    assert "ml_decision" in result.columns