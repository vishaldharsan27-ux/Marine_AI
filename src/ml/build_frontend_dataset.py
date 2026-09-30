"""
Combines the trained (mock) price model with real district catch data into a
single dataset for the frontend to read. This is the "integration" step:
everything downstream (fish stats table, district view, capacity-based plan)
reads from ONE file produced here rather than touching the model or raw data
directly.

Two data sources, kept honestly distinct in the output:
- price_inr_per_kg / price_inr_per_half_kg: MODEL-PREDICTED, trained on
  SYNTHETIC mock data (see src/ml/generate_mock_price_data.py). Not real
  market observations.
- avg_catch_tonnes_per_year / catch_share_in_district: REAL, from the Kerala
  Fisheries Department's district-wise landing data (2022-23 to 2024-25).

Only species present in BOTH the price model and the real catch data are
included - a species with only one of the two is excluded and reported,
never guessed at or filled in.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL_PATH = Path("src/ml/models/market_price_model_MOCK.joblib")
CATCH_PATH = Path("data/processed/kerala_district_catch.csv")
OUT_PATH = Path("data/processed/frontend_dataset.json")

MONTH_NAMES = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
               7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

DISTRICT_NAMES = {
    "TVPM": "Thiruvananthapuram", "KLM": "Kollam", "ALP": "Alappuzha", "EKM": "Ernakulam",
    "TCR": "Thrissur", "MLPM": "Malappuram", "KKD": "Kozhikode", "KNR": "Kannur", "KSD": "Kasaragod",
}
# your 10 target landing centers, mapped to the district they fall under
DISTRICT_PORTS = {
    "EKM": ["Kochi", "Munambam"],
    "KLM": ["Neendakara"],
    "KKD": ["Beypore", "Puthiyappa"],
}


def predict_prices(species_keys):
    bundle = joblib.load(MODEL_PATH)
    model, features = bundle["model"], bundle["features"]

    rows = []
    for species_key in species_keys:
        for month in range(1, 13):
            row = {f: 0.0 for f in features}
            row["month_sin1"] = np.sin(2 * np.pi * month / 12)
            row["month_cos1"] = np.cos(2 * np.pi * month / 12)
            row["month_sin2"] = np.sin(4 * np.pi * month / 12)
            row["month_cos2"] = np.cos(4 * np.pi * month / 12)
            sp_col = f"sp_{species_key}"
            if sp_col not in row:
                continue  # model was never trained on this species
            row[sp_col] = 1.0
            X = pd.DataFrame([row])[features]
            price = float(np.exp(model.predict(X)[0]))
            rows.append({
                "species_key": species_key,
                "month": month,
                "month_name": MONTH_NAMES[month],
                "price_inr_per_kg": round(price, 1),
                "price_inr_per_half_kg": round(price / 2, 1),
            })
    return rows


def compute_district_shares():
    totals = defaultdict(float)
    district_totals = defaultdict(float)
    years_seen = defaultdict(set)

    with open(CATCH_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = row["species_key"]
            if not key:
                continue
            qty = float(row["landing_qty_tonnes"])
            dk = (row["district"], key)
            totals[dk] += qty
            district_totals[row["district"]] += qty
            years_seen[dk].add(row["year"])

    avg_by_district_species = {}
    for (district, key), total in totals.items():
        n_years = len(years_seen[(district, key)])
        avg_by_district_species[(district, key)] = total / n_years

    district_avg_totals = defaultdict(float)
    for (district, key), avg in avg_by_district_species.items():
        district_avg_totals[district] += avg

    shares = {}
    for (district, key), avg in avg_by_district_species.items():
        district_total = district_avg_totals[district]
        shares[(district, key)] = {
            "avg_catch_tonnes_per_year": round(avg, 1),
            "catch_share_in_district": round(avg / district_total, 4) if district_total > 0 else 0.0,
        }
    return shares


def main():
    shares = compute_district_shares()
    species_with_catch = sorted(set(k for (_, k) in shares.keys()))

    price_bundle = joblib.load(MODEL_PATH)
    species_with_price = sorted(
        f[3:] for f in price_bundle["features"] if f.startswith("sp_")
    )

    species_in_both = sorted(set(species_with_catch) & set(species_with_price))
    only_catch = sorted(set(species_with_catch) - set(species_with_price))
    only_price = sorted(set(species_with_price) - set(species_with_catch))

    price_rows = predict_prices(species_in_both)
    price_by_species_month = {(r["species_key"], r["month"]): r for r in price_rows}

    output = {
        "generated_note": "price = MODEL-PREDICTED from synthetic mock data. catch = REAL Kerala Fisheries Dept data (2022-23 to 2024-25).",
        "species_in_both": species_in_both,
        "excluded_species": {"catch_data_only_no_price_model": only_catch, "price_model_only_no_catch_data": only_price},
        "districts": {},
    }

    for district in sorted(set(d for (d, _) in shares.keys())):
        district_entry = {
            "name": DISTRICT_NAMES[district],
            "target_ports": DISTRICT_PORTS.get(district, []),
            "species": {},
        }
        for species_key in species_in_both:
            share_info = shares.get((district, species_key))
            if not share_info:
                continue
            monthly_prices = {
                MONTH_NAMES[m]: {
                    "price_inr_per_kg": price_by_species_month[(species_key, m)]["price_inr_per_kg"],
                    "price_inr_per_half_kg": price_by_species_month[(species_key, m)]["price_inr_per_half_kg"],
                }
                for m in range(1, 13)
            }
            district_entry["species"][species_key] = {
                **share_info,
                "monthly_prices": monthly_prices,
            }
        output["districts"][district] = district_entry

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {OUT_PATH}")
    print(f"Species in both datasets ({len(species_in_both)}): {species_in_both}")
    print(f"Catch data only, no price model ({len(only_catch)}): {only_catch}")
    print(f"Price model only, no catch data ({len(only_price)}): {only_price}")
    print(f"Districts included: {sorted(output['districts'].keys())}")


if __name__ == "__main__":
    main()
