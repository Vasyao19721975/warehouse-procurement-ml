import pandas as pd
from src.recommendation_pipeline import build_all_products


def test_build_all_products():
    df = pd.DataFrame({
        "sku_id": [1, 1],
        "product": ["A", "A"],
        "date": ["2024-01-01", "2024-01-02"],
        "stock": [10, 8],
        "sales": [2, 3]
    })

    result = build_all_products(df, target_days=7)

    assert not result.empty
    assert "recommended_order" in result.columns
    assert "decision" in result.columns