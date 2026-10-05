"""
Runs the full data pipeline end to end, in dependency order:

  1. data_pipeline.py            Kerala Fisheries PDFs  -> data/processed/kerala_district_catch.csv
  2. district_species_ranking.py catch                  -> data/processed/district_species_ranking.csv
  3. district_profit_signal.py   catch + FMPIS prices   -> data/processed/district_profit_signal.csv
  4. train_kerala_catch_model.py catch                  -> src/ml/models/kerala_catch_model.joblib
  5. generate_mock_price_data.py SYNTHETIC prices       -> data/mock/mock_monthly_prices.csv
  6. train_price_model.py        mock prices            -> src/ml/models/market_price_model_MOCK.joblib
  7. build_frontend_dataset.py   price model + catch    -> data/processed/frontend_dataset.json

Usage:
  python main.py                 run every step
  python main.py --from 5        start at step 5 (e.g. after changing the mock data)

Then start the app with:  streamlit run src/frontend/app.py
"""

import argparse
import os
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    "data_pipeline.py",
    "district_species_ranking.py",
    "district_profit_signal.py",
    "train_kerala_catch_model.py",
    "generate_mock_price_data.py",
    "train_price_model.py",
    "build_frontend_dataset.py",
]


def main():
    parser = argparse.ArgumentParser(description="Run the Marine Fishing AI data pipeline.")
    parser.add_argument("--from", dest="start", type=int, default=1, choices=range(1, len(STEPS) + 1),
                        help="step number to start from (1-%d)" % len(STEPS))
    args = parser.parse_args()

    # every script uses paths relative to the repo root
    os.chdir(ROOT)
    for n, script in enumerate(STEPS, start=1):
        if n < args.start:
            continue
        print(f"\n{'=' * 60}\n[{n}/{len(STEPS)}] {script}\n{'=' * 60}")
        runpy.run_path(str(ROOT / "src" / "ml" / script), run_name="__main__")

    print("\nPipeline complete. Start the app with:  streamlit run src/frontend/app.py")


if __name__ == "__main__":
    main()
