"""
Generates a SYNTHETIC monthly price dataset for prototype/demo purposes only.

Why this exists: real price data is limited to a single week (24-30 Mar 2025,
from FMPIS). That's not enough to show any seasonal pattern, and training a
"market analysis" model on one data point per species would just memorize
constants. This script generates a full 12-month synthetic series so there's
an actual season signal to build and demo the pipeline against.

THIS IS NOT REAL DATA. Every row is tagged is_synthetic=True and this file
lives under data/mock/, never data/raw/ or data/processed/, so it can never
be confused with real observations downstream.

Method (documented, not hidden): each species' real known price (from the
one real FMPIS week we have, used as an anchor) is scaled by a monthly
multiplier reflecting Kerala's well-known trawling ban (mechanized boats
banned ~June-July each year, sharply reducing supply and raising prices),
with gradual recovery through August, a post-monsoon supply peak
(Sept-Nov, prices ease), and a moderate rest-of-year baseline. Small random
noise (+/-5%, fixed seed for reproducibility) is added per month so the
series isn't perfectly deterministic. This pattern is a documented modeling
ASSUMPTION grounded in known fishing-ban timing, not measured real data.
"""

import csv
import random
from pathlib import Path

OUT_PATH = Path("data/mock/mock_monthly_prices.csv")

# real anchor prices, Rs/kg, from the one real FMPIS week we have
# (Kerala fishing harbours, 24-30 Mar 2025)
REAL_ANCHOR_PRICES = {
    "oil_sardine": 38,
    "indian_mackerel": 136,
    "indian_squid": 276,
    "penaeid_prawn": 119,
    "ribbon_fish": 145,
    "crab": 157,
    "cuttlefish": 288,
}

# month -> price multiplier vs. anchor. 1=Jan ... 12=Dec.
# Documented assumption: Kerala trawling ban ~June-July (mechanized boats
# grounded -> supply drops -> prices rise), gradual August recovery,
# post-monsoon catch peak Sept-Nov (supply up -> prices ease), moderate
# baseline the rest of the year.
MONTH_MULTIPLIER = {
    1: 1.00, 2: 1.00, 3: 1.00, 4: 1.05, 5: 1.10,
    6: 1.45, 7: 1.40, 8: 1.15,
    9: 0.88, 10: 0.85, 11: 0.90, 12: 0.95,
}

MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


def main():
    random.seed(42)  # reproducible mock data
    rows = []
    for species_key, anchor_price in REAL_ANCHOR_PRICES.items():
        for month in range(1, 13):
            multiplier = MONTH_MULTIPLIER[month]
            noise = random.uniform(-0.05, 0.05)
            price = round(anchor_price * multiplier * (1 + noise), 1)
            rows.append({
                "species_key": species_key,
                "month": month,
                "month_name": MONTH_NAMES[month],
                "price_inr_per_kg": price,
                "is_synthetic": True,
                "anchor_price_real": anchor_price,
                "assumption": "Kerala trawling-ban seasonal pattern (documented, not measured)",
            })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} SYNTHETIC rows to {OUT_PATH}")
    print(f"Species: {list(REAL_ANCHOR_PRICES.keys())}")
    print("\nSample - Indian Mackerel across the year (anchor Rs.136/kg):")
    for r in rows:
        if r["species_key"] == "indian_mackerel":
            print(f"  {r['month_name']}: Rs.{r['price_inr_per_kg']}/kg")


if __name__ == "__main__":
    main()
