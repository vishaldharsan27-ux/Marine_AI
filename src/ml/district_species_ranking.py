"""
Reads data/processed/kerala_district_catch.csv (produced by data_pipeline.py)
and answers: "which species has been caught the most, in which district?"

This is a historical/descriptive summary over 3 real yearly snapshots
(2022-23 to 2024-25), not a predictive model - 3 data points per
district/species is not enough to fit or validate a predictive model on.

Output: data/processed/district_species_ranking.csv, one row per
district+species with total and average tonnes across the 3 years, ranked
within each district by total tonnes descending.
"""

import csv
from collections import defaultdict
from pathlib import Path

IN_PATH = Path("data/processed/kerala_district_catch.csv")
OUT_PATH = Path("data/processed/district_species_ranking.csv")


def main():
    totals = defaultdict(float)
    year_counts = defaultdict(set)

    with open(IN_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # use the canonical species_key when we have one, otherwise fall
            # back to the raw name so unmatched species are still counted
            species_label = row["species_key"] or row["species_name_raw"]
            key = (row["district"], species_label)
            totals[key] += float(row["landing_qty_tonnes"])
            year_counts[key].add(row["year"])

    rows = []
    for (district, species), total in totals.items():
        n_years = len(year_counts[(district, species)])
        rows.append({
            "district": district,
            "species": species,
            "total_qty_tonnes_2022_25": round(total, 1),
            "avg_qty_tonnes_per_year": round(total / n_years, 1),
            "years_observed": n_years,
        })

    # rank within each district by total tonnes, descending
    by_district = defaultdict(list)
    for row in rows:
        by_district[row["district"]].append(row)
    for district, drows in by_district.items():
        drows.sort(key=lambda r: -r["total_qty_tonnes_2022_25"])
        for i, row in enumerate(drows, start=1):
            row["rank_in_district"] = i

    all_rows = sorted(rows, key=lambda r: (r["district"], r["rank_in_district"]))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "district", "rank_in_district", "species",
            "total_qty_tonnes_2022_25", "avg_qty_tonnes_per_year", "years_observed",
        ])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} rows to {OUT_PATH}\n")

    print("Top 5 species by district (2022-23 to 2024-25 total landings):\n")
    for district, drows in sorted(by_district.items()):
        print(f"{district}:")
        for row in sorted(drows, key=lambda r: r["rank_in_district"])[:5]:
            print(f"  {row['rank_in_district']}. {row['species']:<20} {row['total_qty_tonnes_2022_25']:>10,.1f} t total  ({row['avg_qty_tonnes_per_year']:>8,.1f} t/yr avg, {row['years_observed']}/3 years)")
        print()


if __name__ == "__main__":
    main()
