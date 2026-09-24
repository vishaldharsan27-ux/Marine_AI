"""
Combines district-level catch availability (data/processed/kerala_district_catch.csv)
with the one known week of Kerala harbour prices (data/raw/fmpis/kerala_harbour_prices_*.csv)
to answer: "given current prices and historical catch, which fish are most worth
targeting in each district?"

This is explicitly a CURRENT-SNAPSHOT combination, not a seasonal forecast:
- catch side = 3-year (2022-23 to 2024-25) average annual landings per district
- price side = a single week (24-30 Mar 2025) of known Kerala harbour prices

Only species with a confident match in src/i18n/species.json on BOTH sides are
combined - a species present in only one dataset is left out of the ranking
entirely rather than guessed at, and every excluded species is reported so
nothing is silently dropped.
"""

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

SPECIES_DICT_PATH = Path("src/i18n/species.json")
CATCH_PATH = Path("data/processed/kerala_district_catch.csv")
PRICE_PATH = Path("data/raw/fmpis/kerala_harbour_prices_2025-03-24_to_2025-03-30.csv")
OUT_PATH = Path("data/processed/district_profit_signal.csv")


def load_alias_map():
    with open(SPECIES_DICT_PATH, encoding="utf-8") as f:
        species = json.load(f)
    alias_to_key = {}
    for key, entry in species.items():
        for alias in entry.get("aliases", []):
            alias_to_key[alias.strip().lower()] = key
    return alias_to_key, species


def normalize(raw, alias_to_key):
    cleaned = re.sub(r"\s+", " ", raw.replace("\n", " ")).strip()
    return alias_to_key.get(cleaned.lower())


def main():
    alias_to_key, species_dict = load_alias_map()

    # price side: one row per matched species (single week, Kerala harbours)
    price_by_species = {}
    unmatched_price_species = []
    with open(PRICE_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = normalize(row["species_name_raw"], alias_to_key)
            if key:
                price_by_species[key] = float(row["price_inr_per_kg"])
            else:
                unmatched_price_species.append(row["species_name_raw"])

    # catch side: avg tonnes/year per district, already keyed by species_key where matched
    catch_by_district_species = defaultdict(float)
    with open(CATCH_PATH, encoding="utf-8") as f:
        totals = defaultdict(float)
        years_seen = defaultdict(set)
        for row in csv.DictReader(f):
            key = row["species_key"]
            if not key:
                continue
            dk = (row["district"], key)
            totals[dk] += float(row["landing_qty_tonnes"])
            years_seen[dk].add(row["year"])
        for (district, key), total in totals.items():
            catch_by_district_species[(district, key)] = total / len(years_seen[(district, key)])

    # combine: only species present on both sides
    rows = []
    for (district, key), avg_tonnes_per_year in catch_by_district_species.items():
        if key not in price_by_species:
            continue
        price = price_by_species[key]
        annual_value_inr = avg_tonnes_per_year * 1000 * price  # tonnes -> kg
        rows.append({
            "district": district,
            "species_key": key,
            "species_english": species_dict[key]["english"],
            "avg_catch_tonnes_per_year": round(avg_tonnes_per_year, 1),
            "price_inr_per_kg_2025_03_24_30": price,
            "estimated_annual_value_inr": round(annual_value_inr),
        })

    by_district = defaultdict(list)
    for row in rows:
        by_district[row["district"]].append(row)
    for district, drows in by_district.items():
        drows.sort(key=lambda r: -r["estimated_annual_value_inr"])
        for i, row in enumerate(drows, start=1):
            row["rank_in_district"] = i

    all_rows = sorted(rows, key=lambda r: (r["district"], r["rank_in_district"]))
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "district", "rank_in_district", "species_key", "species_english",
            "avg_catch_tonnes_per_year", "price_inr_per_kg_2025_03_24_30", "estimated_annual_value_inr",
        ])
        writer.writeheader()
        writer.writerows(all_rows)

    matched_species = sorted(set(r["species_key"] for r in rows))
    print(f"Wrote {len(all_rows)} rows to {OUT_PATH}")
    print(f"Species matched on both sides ({len(matched_species)}): {matched_species}")
    print(f"Price-side species with no catch-data match, excluded ({len(unmatched_price_species)}): {unmatched_price_species}")
    print()

    print("Top fish by estimated annual value, per district (catch avg x current price):\n")
    for district, drows in sorted(by_district.items()):
        print(f"{district}:")
        for row in sorted(drows, key=lambda r: r["rank_in_district"]):
            print(f"  {row['rank_in_district']}. {row['species_english']:<22} "
                  f"{row['avg_catch_tonnes_per_year']:>8,.1f} t/yr avg  x  Rs.{row['price_inr_per_kg_2025_03_24_30']:>5.0f}/kg  "
                  f"= Rs.{row['estimated_annual_value_inr']:>15,.0f}/yr")
        print()


if __name__ == "__main__":
    main()
