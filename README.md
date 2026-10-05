# Smart Marine Fishing Assistant

A district-level fishing assistant for Kerala fishermen. For a chosen season, district and boat capacity it shows:

- **Live sea conditions** - waves, swell, wind, currents, tides and a 7-day outlook (Open-Meteo)
- **Official alerts** - IMD / INCOIS warnings from the NDMA Sachet feed, matched to the district
- **Fish-gathering zones** - today's INCOIS Potential Fishing Zones on a map, coloured by sea state
- **Catch plan** - typical species mix (real catch data) x predicted price = estimated trip value

Available in English, Malayalam and Tamil.

> **Data honesty:** catch data is REAL (Kerala Fisheries Dept, 2022-23 to 2024-25). Prices are
> MODEL-PREDICTED from SYNTHETIC data anchored on one real week of FMPIS prices - a prototype,
> not real market history. The app labels both throughout.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
streamlit run src/frontend/app.py
```

The app only needs `data/processed/frontend_dataset.json` and `src/i18n/species.json`, both committed.
To rebuild everything from raw data:

```bash
python main.py              # all 7 steps
python main.py --from 5     # only the price model + frontend dataset
```

## Pipeline

| Step | Script (`src/ml/`) | Reads | Writes |
|---|---|---|---|
| 1 | `data_pipeline.py` | Kerala Fisheries Dept PDFs | `data/processed/kerala_district_catch.csv` |
| 2 | `district_species_ranking.py` | catch | `data/processed/district_species_ranking.csv` |
| 3 | `district_profit_signal.py` | catch + FMPIS week | `data/processed/district_profit_signal.csv` |
| 4 | `train_kerala_catch_model.py` | catch | `src/ml/models/kerala_catch_model.joblib` |
| 5 | `generate_mock_price_data.py` | FMPIS anchor prices | `data/mock/mock_monthly_prices.csv` (SYNTHETIC) |
| 6 | `train_price_model.py` | mock prices | `src/ml/models/market_price_model_MOCK.joblib` |
| 7 | `build_frontend_dataset.py` | price model + catch | `data/processed/frontend_dataset.json` |

`notebooks/train_market_price_model.ipynb` is the Colab version of step 6.

## Project structure

```
Marine_Fishing_AI/
├── data/
│   ├── raw/                  # Source data, never edited
│   │   ├── kerala_fisheries_dept/   # District catch PDFs 2022-23 to 2024-25
│   │   ├── fmpis/                   # FMPIS weekly harbour prices (24-30 Mar 2025)
│   │   ├── cmfri/                   # CMFRI Table A-5.5, state-level catch
│   │   └── weather/                 # India weather/rainfall xlsx (local only, not in git)
│   ├── mock/                 # SYNTHETIC data - never mix with raw/processed
│   └── processed/            # Pipeline outputs, safe to regenerate
├── notebooks/                # Colab training notebook
├── src/
│   ├── ml/                   # Pipeline scripts and trained models
│   ├── frontend/             # Streamlit app
│   │   ├── app.py            # UI
│   │   ├── sea_weather.py    # Open-Meteo marine + forecast
│   │   ├── official_alerts.py# NDMA Sachet CAP feed (IMD / INCOIS)
│   │   └── fishing_zones.py  # INCOIS PFZ WFS
│   └── i18n/species.json     # Species names: scientific / English / Malayalam / Tamil
├── main.py                   # Runs the whole pipeline
└── requirements.txt
```

## Known gaps

- **Tamil Nadu** - no district catch data yet; all district data is Kerala only.
- **Prices** - synthetic until a real multi-month price series is available.
- **Translations** - Malayalam and Tamil text has not been reviewed by a native speaker.
- **Official alerts** - only the Kerala Sachet feed is wired in.
