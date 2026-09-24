import pandas as pd
from pathlib import Path


class DataLoader:

    def __init__(self):
        self.base_path = Path("data/raw")

    def load_fisheries_data(self):
        file_path = self.base_path / "cmfri" / "Table_A-5.5.csv"
        return pd.read_csv(file_path)

    def load_weather_data(self):
        file_path = self.base_path / "weather" / "india_weather_rainfall_data.xlsx"
        return pd.read_excel(file_path)


if __name__ == "__main__":

    loader = DataLoader()

    fisheries_df = loader.load_fisheries_data()
    weather_df = loader.load_weather_data()

    print("=" * 60)
    print("FISHERIES DATA")
    print("=" * 60)

    print(fisheries_df.head())#top 5 rows
    print("\nShape:", fisheries_df.shape)#no.of clms and rows
    print("\nColumns:")
    print(fisheries_df.columns) #no.of clms

    print("\nMissing Values:")
    print(fisheries_df.isnull().sum())

    print("\nData Types:")
    print(fisheries_df.dtypes)

    print("\n")

    print("=" * 60)
    print("WEATHER DATA")
    print("=" * 60)

    print(weather_df.head())
    print("\nShape:", weather_df.shape)
    print("\nColumns:")
    print(weather_df.columns)

    print("\nMissing Values:")
    print(weather_df.isnull().sum())

    print("\nData Types:")
    print(weather_df.dtypes)