#Feature Engineering is the process of converting raw data into something the model can learn from
import pandas as pd


class FeatureEngineer:

    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe.copy()

    def remove_total_row(self):
        self.df = self.df[self.df["species"] != "Total"]
        return self

    def convert_to_long_format(self):

        state_columns = [
            "andhra_pradesh",
            "odisha",
            "tamil_nadu",
            "west_bengal",
            "andaman_nicobar",
            "puducherry",
            "gujarat",
            "karnataka",
            "kerala",
            "maharashtra",
            "goa",
            "lakshadweep",
            "daman_diu"
        ]

        self.df = self.df.melt(
            id_vars=["species"],
            value_vars=state_columns,
            var_name="state",
            value_name="catch"
        )

        return self

    def get_dataframe(self):
        return self.df