"""
Trains a RandomForest to predict district-level annual catch quantity
(landing_qty_tonnes) from district + species + year, using the 3 years of
real Kerala Fisheries Dept data (2022-23 to 2024-25).

This is an ANNUAL trend model, not a seasonal forecast - we don't have
month-level data, so it cannot learn monsoon/non-monsoon patterns. What it
CAN learn is cross-sectional structure pooled across all 1,179 district x
species x year rows: which districts run higher for which species, and
whether a given district+species combination is trending up or down year
over year.

Honest backtest: trained on 2022-23 + 2023-24 only, evaluated against the
real, known 2024-25 values - so the reported error is genuine held-out
performance, not a fit-and-report number.
"""

import csv
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, median_absolute_error
from sklearn.preprocessing import LabelEncoder

CATCH_PATH = Path("data/processed/kerala_district_catch.csv")
MODEL_DIR = Path("src/ml/models")

YEAR_TO_ORDINAL = {"2022-23": 0, "2023-24": 1, "2024-25": 2}


def load_rows():
    rows = []
    with open(CATCH_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            species_id = row["species_key"] or row["species_name_raw"]
            rows.append({
                "district": row["district"],
                "species_id": species_id,
                "year": row["year"],
                "qty": float(row["landing_qty_tonnes"]),
            })
    return rows


def main():
    rows = load_rows()

    district_enc = LabelEncoder().fit([r["district"] for r in rows])
    species_enc = LabelEncoder().fit([r["species_id"] for r in rows])

    def to_features(r):
        return [
            district_enc.transform([r["district"]])[0],
            species_enc.transform([r["species_id"]])[0],
            YEAR_TO_ORDINAL[r["year"]],
        ]

    train_rows = [r for r in rows if r["year"] in ("2022-23", "2023-24")]
    test_rows = [r for r in rows if r["year"] == "2024-25"]

    X_train = np.array([to_features(r) for r in train_rows])
    y_train = np.array([r["qty"] for r in train_rows])
    X_test = np.array([to_features(r) for r in test_rows])
    y_test = np.array([r["qty"] for r in test_rows])

    model = RandomForestRegressor(n_estimators=300, random_state=42, min_samples_leaf=2)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    medae = median_absolute_error(y_test, preds)

    print("=== Backtest: trained on 2022-23 + 2023-24, tested against real 2024-25 ===")
    print(f"Train rows: {len(train_rows)}, Test rows: {len(test_rows)}")
    print(f"Mean Absolute Error:   {mae:,.1f} tonnes")
    print(f"Median Absolute Error: {medae:,.1f} tonnes")
    print(f"(for scale: 2024-25 test-set catch values range {y_test.min():.0f} to {y_test.max():,.0f} tonnes,")
    print(f" mean {y_test.mean():,.1f}, median {np.median(y_test):,.1f})")
    print()

    # a few concrete examples: biggest species in EKM, actual vs predicted
    print("Example predictions (Ernakulam district, real 2024-25 vs model prediction):\n")
    examples = [r for r in test_rows if r["district"] == "EKM"]
    examples_with_pred = list(zip(examples, model.predict(np.array([to_features(r) for r in examples]))))
    examples_with_pred.sort(key=lambda t: -t[0]["qty"])
    for r, pred in examples_with_pred[:8]:
        print(f"  {r['species_id']:<22} actual {r['qty']:>10,.0f} t   predicted {pred:>10,.0f} t   "
              f"error {abs(r['qty'] - pred):>9,.0f} t")

    # retrain on all 3 years for the saved artifact
    X_all = np.array([to_features(r) for r in rows])
    y_all = np.array([r["qty"] for r in rows])
    final_model = RandomForestRegressor(n_estimators=300, random_state=42, min_samples_leaf=2)
    final_model.fit(X_all, y_all)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    import joblib
    joblib.dump({
        "model": final_model,
        "district_encoder": district_enc,
        "species_encoder": species_enc,
        "year_to_ordinal": YEAR_TO_ORDINAL,
    }, MODEL_DIR / "kerala_catch_model.joblib")
    print(f"\nSaved final model (trained on all 3 years) to {MODEL_DIR / 'kerala_catch_model.joblib'}")
    print("NOTE: this model predicts ANNUAL catch trend only - it has no season/month awareness.")


if __name__ == "__main__":
    main()
