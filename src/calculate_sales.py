import pandas as pd


def build_final_dataset(stocks_df: pd.DataFrame, supplies_df: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(
        stocks_df,
        supplies_df,
        on=["date", "sku_id"],
        how="left"
    )

    df["supply"] = df["supply"].fillna(0)

    df = df.sort_values(["sku_id", "date"]).reset_index(drop=True)
    df["prev_stock"] = df.groupby("sku_id")["stock"].shift(1)

    df["sales"] = df["prev_stock"] - df["stock"] + df["supply"]
    df["sales"] = df["sales"].fillna(0)
    df["sales"] = df["sales"].clip(lower=0)

    return df