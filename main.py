from src.ml.load_data import DataLoader
from src.ml.preprocess import DataPreprocessor
from src.ml.feature_engineering import FeatureEngineer
from src.ml.train_model import FishCatchModel


# ============================================================
# 1. LOAD DATA
# ============================================================

loader = DataLoader()

fisheries_df = loader.load_fisheries_data()
weather_df = loader.load_weather_data()


# ============================================================
# 2. INSPECT FISHERIES DATA
# ============================================================

print("\n" + "=" * 60)
print("FISHERIES DATA")
print("=" * 60)

print("\nFirst 5 rows:")
print(fisheries_df.head())

print("\nShape:")
print(fisheries_df.shape)

print("\nColumns:")
print(fisheries_df.columns.tolist())

print("\nMissing Values:")
print(fisheries_df.isnull().sum())

print("\nData Types:")
print(fisheries_df.dtypes)


# ============================================================
# 3. PREPROCESS FISHERIES DATA
# ============================================================

processor = DataPreprocessor(fisheries_df)

clean_df = (
    processor
        .remove_duplicates()
        .handle_missing_values()
        .rename_columns()
        .clean_column_names()
        .get_dataframe()
)


print("\n" + "=" * 60)
print("CLEANED FISHERIES DATA")
print("=" * 60)

print("\nFirst 5 rows:")
print(clean_df.head())

print("\nShape:")
print(clean_df.shape)

print("\nColumns:")
print(clean_df.columns.tolist())


# ============================================================
# 4. FEATURE ENGINEERING
# ============================================================

engineer = FeatureEngineer(clean_df)

ml_df = (
    engineer
        .remove_total_row()
        .convert_to_long_format()
        .get_dataframe()
)


print("\n" + "=" * 60)
print("MACHINE LEARNING DATASET")
print("=" * 60)

print("\nFirst 10 rows:")
print(ml_df.head(10))

print("\nShape:")
print(ml_df.shape)

print("\nColumns:")
print(ml_df.columns.tolist())

print("\nSpecies:")
print(ml_df["species"].unique())

print("\nStates:")
print(ml_df["state"].unique())


# ============================================================
# 5. INSPECT WEATHER DATA
# ============================================================

print("\n" + "=" * 60)
print("WEATHER DATA")
print("=" * 60)

print("\nFirst 5 rows:")
print(weather_df.head())

print("\nShape:")
print(weather_df.shape)

print("\nColumns:")
print(weather_df.columns.tolist())

print("\nMissing Values:")
print(weather_df.isnull().sum())

print("\nData Types:")
print(weather_df.dtypes)


# ============================================================
# 6. CURRENT ML MODEL
# ============================================================

print("\n" + "=" * 60)
print("CURRENT FISH CATCH MODEL")
print("=" * 60)

model = FishCatchModel(ml_df)

(
    model
        .encode_features()
        .split_data()
        .train()
        .evaluate()
)

print("\nCurrent model completed successfully.")