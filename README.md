# Smart Marine Fishing Assistant

A data-driven assistant that helps predict fish catch potential across Indian coastal states using historical fisheries statistics and weather/ocean data.

## Project Structure

```
Marine_Fishing_AI/
├── data/
│   ├── raw/                # Untouched source data, exactly as downloaded/received
│   │   ├── cmfri/          # CMFRI-style fisheries catch statistics (Table_A-5.5.csv)
│   │   ├── era5/           # ECMWF ERA5 reanalysis data (ocean/atmosphere variables) — placeholder, populate with future ERA5 downloads
│   │   └── weather/         # Supplementary India weather/rainfall dataset (not ERA5-sourced; kept separate to avoid mislabeling)
│   ├── processed/           # Cleaned, merged, feature-engineered datasets ready for modeling
│   └── master/              # Reserved for a single consolidated "golden" dataset (currently empty, legacy placeholder)
│
├── src/
│   ├── backend/              # API server (FastAPI/uvicorn) exposing predictions and data endpoints — to be implemented
│   ├── ml/                   # Data loading, preprocessing, feature engineering, and model training/inference
│   │   ├── load_data.py
│   │   ├── preprocess.py
│   │   ├── feature_engineering.py
│   │   └── train_model.py
│   ├── frontend/             # User-facing app (web/mobile) — to be implemented
│   └── i18n/                 # Localization/translation resources for supported languages — to be implemented
│
├── models/                   # Serialized/trained model artifacts (e.g. .joblib, .pkl)
├── outputs/                  # Generated reports, plots, prediction exports
├── main.py                   # End-to-end pipeline entry point (load → clean → engineer → train → evaluate)
├── requirements.txt          # Python dependencies
└── README.md
```

## Directory Responsibilities

- **data/raw/** — Immutable source data. Never edit or delete files here; always write derived data to `data/processed/`.
  - **cmfri/** — Fisheries catch statistics (species x state), sourced in the style of CMFRI/DAHD annual reports.
  - **era5/** — Reserved for ERA5 reanalysis data (sea surface temperature, wind, pressure, etc.) used to correlate weather conditions with catch. Currently empty; add downloaded ERA5 files here.
  - **weather/** — India-wide weather/rainfall dataset currently in use. Kept distinct from `era5/` since it is not sourced from ERA5.
- **data/processed/** — Output of the preprocessing/feature-engineering pipeline; safe to regenerate from `data/raw/`.
- **src/ml/** — All existing data science code: `DataLoader`, `DataPreprocessor`, `FeatureEngineer`, and `FishCatchModel` (RandomForest-based catch predictor).
- **src/backend/** — Planned FastAPI service to serve model predictions to the frontend (dependencies already listed in `requirements.txt`).
- **src/frontend/** — Planned client application for end users (fishers/researchers) to interact with predictions.
- **src/i18n/** — Planned translation strings/resources for multi-language support (e.g. regional Indian languages for coastal users).

## Setup Instructions

1. **Create and activate a virtual environment** (a `.venv/` already exists in this repo; recreate if needed):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the ML pipeline** (loads data, cleans it, engineers features, trains and evaluates the model):
   ```bash
   python main.py
   ```

4. **Adding new raw data:** place fisheries tables under `data/raw/cmfri/`, and any ERA5 reanalysis extracts under `data/raw/era5/`. Never overwrite existing raw files — add new dated files instead.

## Notes

- This repository's `.git` history is rooted at the Windows user profile directory (`C:\Users\HP`), not at this project folder. Be cautious with any git operations run from here, as they may pick up unrelated files outside this project.
- `src/backend/`, `src/frontend/`, and `src/i18n/` are currently empty placeholders awaiting implementation of the full-stack assistant.
