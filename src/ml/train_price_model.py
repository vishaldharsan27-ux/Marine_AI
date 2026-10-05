"""
Trains the market price model on SYNTHETIC mock data - a local copy of
notebooks/train_market_price_model.ipynb so the model can be rebuilt without Colab.

Reads data/mock/mock_monthly_prices.csv (built by generate_mock_price_data.py).
Model: linear regression on log(price) with 2 month harmonics + one-hot species.
Output: src/ml/models/market_price_model_MOCK.joblib, read by build_frontend_dataset.py.

The _MOCK suffix is intentional - keep it until this is retrained on real prices.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

DATA_PATH = Path("data/mock/mock_monthly_prices.csv")
MODEL_PATH = Path("src/ml/models/market_price_model_MOCK.joblib")
HOLDOUT_MONTHS = [6, 9, 12]
TARGET = "price_inr_per_kg"


def build_features(df):
    df = df.copy()
    df["month_sin1"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos1"] = np.cos(2 * np.pi * df["month"] / 12)
    df["month_sin2"] = np.sin(4 * np.pi * df["month"] / 12)
    df["month_cos2"] = np.cos(4 * np.pi * df["month"] / 12)
    species_dummies = pd.get_dummies(df["species_key"], prefix="sp")
    df = pd.concat([df, species_dummies], axis=1)
    features = ["month_sin1", "month_cos1", "month_sin2", "month_cos2"] + list(species_dummies.columns)
    return df, features


def main():
    df = pd.read_csv(DATA_PATH)
    assert df["is_synthetic"].all(), "Expected every row to be flagged synthetic"
    df, features = build_features(df)

    train_df = df[~df["month"].isin(HOLDOUT_MONTHS)]
    test_df = df[df["month"].isin(HOLDOUT_MONTHS)]
    model = LinearRegression().fit(train_df[features], np.log(train_df[TARGET]))
    preds = np.exp(model.predict(test_df[features]))
    print(f"Holdout MAE (months {HOLDOUT_MONTHS}): Rs.{mean_absolute_error(test_df[TARGET], preds):.1f}/kg")

    final_model = LinearRegression().fit(df[features], np.log(df[TARGET]))
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "model": final_model,
        "features": features,
        "target_transform": "log",
        "trained_on": "SYNTHETIC mock data - data/mock/mock_monthly_prices.csv",
    }, MODEL_PATH)
    print(f"Saved {MODEL_PATH}")


if __name__ == "__main__":
    main()
