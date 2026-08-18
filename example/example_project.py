from analysisweb import Status
import time

from pathlib import Path

import time

from sklearn.datasets import fetch_california_housing
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split


class HousingModel:
    def __init__(self, data_size: int = 500):
        self.data_size = data_size

        self.X = None
        self.y = None

        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None

        self.model = None
        self.score = None

    def load_dataset(self, dataset_name="california_housing"):
        housing = fetch_california_housing(as_frame=True)

        self.X = housing.data.iloc[:self.data_size]
        self.y = housing.target.iloc[:self.data_size]

        time.sleep(2)

        return {
            "Status": Status.SUCCESS,
            "dataset": dataset_name,
            "samples": len(self.X),
            "features": self.X.shape[1],
        }

    def split_dataset(self, test_size=0.2, random_state=42):
        (
            self.X_train,
            self.X_test,
            self.y_train,
            self.y_test,
        ) = train_test_split(
            self.X,
            self.y,
            test_size=test_size,
            random_state=random_state,
        )

        time.sleep(2)

        return {
            "Status": Status.SUCCESS,
        }

    def train_model(self, fit_intercept=True):
        self.model = LinearRegression(
            fit_intercept=fit_intercept
        )

        self.model.fit(
            self.X_train,
            self.y_train,
        )

        time.sleep(4)

        return {
            "Status": Status.SUCCESS,
        }

    def evaluate_model(self, metric="rmse"):
        predictions = self.model.predict(self.X_test)

        if metric == "rmse":
            self.score = mean_squared_error(
                self.y_test,
                predictions,
            ) ** 0.5
        else:
            raise ValueError(f"Unsupported metric: {metric}")

        time.sleep(3)

        return {
            "Status": Status.SUCCESS,
            "rmse": self.score,
        }

    def save_model(
        self,
        output_path="results/housing_model.pkl",
    ):
        Path(output_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # joblib.dump(self.model, output_path)

        time.sleep(2)

        return {
            "Status": Status.SUCCESS,
        }