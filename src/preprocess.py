import pandas as pd


def prepare_stocks(stocks_df: pd.DataFrame) -> pd.DataFrame:
    stocks_df = stocks_df.copy()

    stocks_df["sku_id"] = stocks_df["sku_id"].astype(str).str.strip()
    stocks_df["product"] = stocks_df["product"].astype(str).str.strip()
    stocks_df["stock"] = pd.to_numeric(stocks_df["stock"], errors="coerce").fillna(0)

    stocks_df = stocks_df.dropna(subset=["date", "sku_id"])
    stocks_df = stocks_df.drop_duplicates()

    return stocks_df


def prepare_supplies(supplies_df: pd.DataFrame) -> pd.DataFrame:
    supplies_df = supplies_df.copy()

    supplies_df["sku_id"] = supplies_df["sku_id"].astype(str).str.strip()
    supplies_df["supply"] = pd.to_numeric(supplies_df["supply"], errors="coerce").fillna(0)

    supplies_df = supplies_df.dropna(subset=["date", "sku_id"])
    supplies_df = supplies_df.groupby(["date", "sku_id"], as_index=False)["supply"].sum()

    return supplies_df


def choose_main_stock_snapshot(stocks_df: pd.DataFrame) -> pd.DataFrame:
    """
    Если за один день есть и утро, и вечер,
    берем вечер как основной остаток.
    Если вечера нет — берем то, что есть.
    """
    stocks_df = stocks_df.copy()

    priority = {"evening": 2, "morning": 1, "unknown": 0}
    stocks_df["priority"] = stocks_df["time_of_day"].map(priority).fillna(0)

    stocks_df = stocks_df.sort_values(["date", "sku_id", "priority"])
    stocks_df = stocks_df.groupby(["date", "sku_id"], as_index=False).last()

    stocks_df = stocks_df.drop(columns=["priority"])

    return stocks_df