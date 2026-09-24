"""
Ingests the Kerala Fisheries Department district-wise marine fish landing
PDFs (data/raw/kerala_fisheries_dept/) and produces a clean, deduplicated
catch table at data/processed/kerala_district_catch.csv.

Species names are normalized against src/i18n/species.json so that raw
spelling variants across years (e.g. "Oil Sardine" / "Oil Sardines") collapse
into one canonical species. Rows with no match are kept under their raw name
and flagged unmatched=True rather than silently dropped or guessed at.

This is a descriptive/historical pipeline, not a predictive model: only
2022-23 through 2024-25 (3 yearly snapshots, district-level) currently exist
as real data, which is not enough to train or validate a predictive model.
Price and effort-hours are not available from this source at all.
"""

import csv
import json
import re
from pathlib import Path

import pdfplumber

RAW_DIR = Path("data/raw/kerala_fisheries_dept")
PROCESSED_DIR = Path("data/processed")
SPECIES_DICT_PATH = Path("src/i18n/species.json")

YEAR_FILES = {
    "2022-23": RAW_DIR / "kerala_district_catch_2022-23.pdf",
    "2023-24": RAW_DIR / "kerala_district_catch_2023-24.pdf",
    "2024-25": RAW_DIR / "kerala_district_catch_2024-25.pdf",
}

# normalize whatever district header variant appears (code or full name) to one canonical code
DISTRICT_MAP = {
    "TVPM": "TVPM", "THIRUVANANTHAPURAM": "TVPM",
    "KLM": "KLM", "KOLLAM": "KLM",
    "ALP": "ALP", "ALAPPUZHA": "ALP",
    "EKM": "EKM", "ERNAKULAM": "EKM",
    "TCR": "TCR", "THRISSUR": "TCR",
    "MLPM": "MLPM", "MALAPPURAM": "MLPM",
    "KKD": "KKD", "KOZHIKODE": "KKD",
    "KNR": "KNR", "KANNUR": "KNR",
    "KSD": "KSD", "KASARGOD": "KSD", "KASARAGOD": "KSD",
}


def load_species_dictionary():
    with open(SPECIES_DICT_PATH, encoding="utf-8") as f:
        species = json.load(f)
    alias_to_key = {}
    for key, entry in species.items():
        for alias in entry.get("aliases", []):
            alias_to_key[alias.strip().lower()] = key
    return alias_to_key


def normalize_species_name(raw_name, alias_to_key):
    cleaned = re.sub(r"\s+", " ", raw_name.replace("\n", " ")).strip()
    key = alias_to_key.get(cleaned.lower())
    return cleaned, key


def extract_year(path, year):
    rows = []
    with pdfplumber.open(path) as pdf:
        header_seen = False
        district_cols = None
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if row is None or not any(row):
                        continue
                    cell0 = (row[0] or "").strip()

                    if not header_seen and cell0.upper().replace(".", "").replace(" ", "") in ("SLNO",):
                        district_cols = []
                        for i, cell in enumerate(row):
                            if not cell:
                                continue
                            key = cell.strip().upper().replace(".", "")
                            if key in DISTRICT_MAP:
                                district_cols.append((i, DISTRICT_MAP[key]))
                        header_seen = True
                        continue

                    if not header_seen:
                        continue
                    if cell0.upper() in ("SL NO", "SLNO", "TOTAL", ""):
                        continue
                    if len(row) < 2 or not row[1]:
                        continue

                    species_raw = row[1].strip()
                    if not species_raw or species_raw.upper() == "TOTAL":
                        continue

                    for idx, district_code in district_cols:
                        if idx >= len(row):
                            continue
                        val = (row[idx] or "").strip().replace(",", "")
                        if val in ("", "-"):
                            continue
                        try:
                            qty = float(val)
                        except ValueError:
                            continue
                        rows.append({
                            "year": year,
                            "district": district_code,
                            "species_name_raw": species_raw,
                            "landing_qty_tonnes": qty,
                        })
    return rows


def main():
    alias_to_key = load_species_dictionary()

    all_rows = []
    for year, path in YEAR_FILES.items():
        all_rows.extend(extract_year(path, year))

    unmatched_species = set()
    for row in all_rows:
        cleaned, key = normalize_species_name(row["species_name_raw"], alias_to_key)
        row["species_name_raw"] = cleaned
        row["species_key"] = key or ""
        if key is None:
            unmatched_species.add(cleaned)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "kerala_district_catch.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["year", "district", "species_name_raw", "species_key", "landing_qty_tonnes"])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} rows to {out_path}")
    print(f"Years: {sorted(set(r['year'] for r in all_rows))}")
    print(f"Districts: {sorted(set(r['district'] for r in all_rows))}")
    print(f"Species matched to species.json: {len(set(r['species_key'] for r in all_rows if r['species_key']))}")
    print(f"Unmatched raw species names ({len(unmatched_species)}): {sorted(unmatched_species)}")


if __name__ == "__main__":
    main()
