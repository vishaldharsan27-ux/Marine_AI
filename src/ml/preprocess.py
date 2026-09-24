import pandas as pd
class DataPreprocessor:

    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe.copy()

    def remove_duplicates(self):
        self.df = self.df.drop_duplicates()
        return self

    def handle_missing_values(self):
        self.df = self.df.fillna(0)
        return self

    def rename_columns(self):
        column_mapping = {
            "REGION NO. 57 - INDIAN OCEAN EAST - A.P.": "andhra_pradesh",
            "REGION NO. 57 - INDIAN OCEAN EAST - Orissa": "odisha",
            "REGION NO. 57 - INDIAN OCEAN EAST - T.N.": "tamil_nadu",
            "REGION NO. 57 - INDIAN OCEAN EAST - W.B.": "west_bengal",
            "REGION NO. 57 - INDIAN OCEAN EAST - A & N Islands": "andaman_nicobar",
            "REGION NO. 57 - INDIAN OCEAN EAST - Puducherry": "puducherry",

            "REGION NO. 51 - INDIAN OCEAN WEST - Gujarat": "gujarat",
            "REGION NO. 51 - INDIAN OCEAN WEST - Karnataka": "karnataka",
            "REGION NO. 51 - INDIAN OCEAN WEST - Kerala": "kerala",
            "REGION NO. 51 - INDIAN OCEAN WEST - Maharashtra": "maharashtra",
            "REGION NO. 51 - INDIAN OCEAN WEST - Goa": "goa",
            "REGION NO. 51 - INDIAN OCEAN WEST - Lakshadweep": "lakshadweep",
            "REGION NO. 51 - INDIAN OCEAN WEST - Daman & Diu": "daman_diu",

            "REGION NO. 57 - INDIAN OCEAN EAST - Total": "east_total",
            "REGION NO. 51 - INDIAN OCEAN WEST - Total": "west_total",
            "Total for India": "india_total"
        }

        self.df.rename(columns=column_mapping, inplace=True)
        return self

    def clean_column_names(self):
        self.df.columns = (
            self.df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )
        return self

    def get_dataframe(self):
        return self.df