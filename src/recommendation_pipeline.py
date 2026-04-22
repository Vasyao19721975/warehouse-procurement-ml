import pandas as pd


def build_all_products(final_df: pd.DataFrame, target_days: int) -> pd.DataFrame:
    num_days = final_df["date"].nunique()

    sales_stats = (
        final_df.groupby(["sku_id", "product"], as_index=False)["sales"]
        .sum()
        .rename(columns={"sales": "total_sales"})
    )

    sales_stats["sales_per_day"] = sales_stats["total_sales"] / num_days

    latest_stock = (
        final_df.sort_values("date")
        .groupby("sku_id", as_index=False)
        .last()[["sku_id", "product", "stock"]]
    )

    all_products = pd.merge(
        latest_stock,
        sales_stats[["sku_id", "sales_per_day"]],
        on="sku_id",
        how="left",
    )

    all_products["sales_per_day"] = all_products["sales_per_day"].fillna(0)

    all_products["days_of_stock"] = all_products.apply(
        lambda row: row["stock"] / row["sales_per_day"]
        if row["sales_per_day"] > 0
        else float("inf"),
        axis=1,
    )

    def decide_order(days_of_stock: float) -> str:
        if days_of_stock > 30:
            return "no_order"
        if days_of_stock > 10:
            return "reduce_order"
        if days_of_stock > 5:
            return "normal_order"
        return "increase_order"

    all_products["decision"] = all_products["days_of_stock"].apply(decide_order)

    all_products["recommended_order"] = (
        all_products["sales_per_day"] * target_days
    ) - all_products["stock"]

    all_products["recommended_order"] = all_products["recommended_order"].apply(
        lambda x: max(0, x)
    )

    return all_products