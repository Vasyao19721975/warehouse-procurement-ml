import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split


def prepare_ml_data(df: pd.DataFrame) -> pd.DataFrame:
    ml_df = df.copy()
    ml_df = ml_df.sort_values(["sku_id", "date"])

    ml_df["lag_1"] = ml_df.groupby("sku_id")["sales"].shift(1)
    ml_df["lag_2"] = ml_df.groupby("sku_id")["sales"].shift(2)

    ml_df = ml_df.dropna().copy()
    return ml_df


def train_sales_model(ml_df: pd.DataFrame) -> tuple[RandomForestRegressor, float]:
    X = ml_df[["lag_1", "lag_2"]]
    y = ml_df["sales"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)

    return model, mae


def predict_sales(ml_df: pd.DataFrame, model: RandomForestRegressor) -> pd.DataFrame:
    result = ml_df.copy()
    result["predicted_sales"] = model.predict(result[["lag_1", "lag_2"]])
    return result


def aggregate_predictions(predicted_df: pd.DataFrame) -> pd.DataFrame:
    return predicted_df.groupby("sku_id", as_index=False)["predicted_sales"].mean()


def add_ml_recommendations(
    all_products: pd.DataFrame,
    predicted_sales: pd.DataFrame,
    target_days: int,
) -> pd.DataFrame:
    result = all_products.copy()

    result = pd.merge(
        result,
        predicted_sales,
        on="sku_id",
        how="left",
    )

    result["ml_recommended_order"] = (
        result["predicted_sales"] * target_days
    ) - result["stock"]

    result["ml_recommended_order"] = result["ml_recommended_order"].apply(
        lambda x: max(0, x) if pd.notna(x) else 0
    )

    result["difference"] = (
        result["recommended_order"] - result["ml_recommended_order"]
    )

    return result