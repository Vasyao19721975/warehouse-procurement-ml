import pandas as pd
from src.load_data import load_stocks, load_supplies


def test_load_stocks(tmp_path):
    folder = tmp_path / "stocks"
    folder.mkdir()

    file = folder / "остатки_утро_01.01.2024.xlsx"

    df = pd.DataFrame({
        "sku_id": [1],
        "product": ["A"],
        "qty": [10],
    })

    df.to_excel(file, index=False)

    result = load_stocks(str(folder))

    assert not result.empty
    assert "stock" in result.columns
    assert "date" in result.columns
    assert "time_of_day" in result.columns


def test_load_supplies(tmp_path):
    folder = tmp_path / "supplies"
    folder.mkdir()

    file = folder / "поставки_01.01.2024.xlsx"

    df = pd.DataFrame({
        "sku_id": [1],
        "count": [5],
    })

    df.to_excel(file, index=False)

    result = load_supplies(str(folder))

    assert not result.empty
    assert "supply" in result.columns
    assert "date" in result.columns