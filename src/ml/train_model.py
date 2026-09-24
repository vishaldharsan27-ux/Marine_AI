from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error


class FishCatchModel:

    def __init__(self, dataframe):
        self.df = dataframe.copy()

    def encode_features(self):
        """
        Convert text columns into numerical values.
        Example:
            Sardine -> 0
            Tuna -> 1

            Kerala -> 0
            Goa -> 1
        """

        self.species_encoder = LabelEncoder()
        self.state_encoder = LabelEncoder()

        self.df["species"] = self.species_encoder.fit_transform(self.df["species"])
        self.df["state"] = self.state_encoder.fit_transform(self.df["state"])

        return self

    def split_data(self):
        """
        Split the dataset into:
        X -> Features
        y -> Target
        """

        X = self.df[["species", "state"]]
        y = self.df["catch"]

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42
        )

        return self

    def train(self):
        """
        Train the Random Forest model.
        """

        self.model = RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )

        self.model.fit(self.X_train, self.y_train)

        return self

    def evaluate(self):
        """
        Evaluate the model using Mean Absolute Error.
        """

        predictions = self.model.predict(self.X_test)

        error = mean_absolute_error(
            self.y_test,
            predictions
        )

        print("\nModel Evaluation")
        print("----------------")
        print(f"Mean Absolute Error: {error:.2f}")

        return self

    def predict(self, species, state):
        """
        Predict catch for a given species and state.
        """

        # Convert text into numbers
        species = self.species_encoder.transform([species])[0]
        state = self.state_encoder.transform([state])[0]

        sample = [[species, state]]

        prediction = self.model.predict(sample)

        return prediction[0]