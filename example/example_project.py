"""Example housing model pipeline.

This module provides a simple HousingModel class that demonstrates
loading a dataset, splitting it, training a linear regression model,
evaluating using RMSE, and saving the trained model.
"""

import time
from pathlib import Path

import numpy as np
from sklearn.datasets import fetch_california_housing, fetch_openml
from sklearn.linear_model import LinearRegression
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

from analysisweb import Status
from analysisweb.reports import image_gallery_to_html


class HousingModel:  # pylint: disable=too-many-instance-attributes
    """Simple pipeline for a housing regression model.

    The class wraps dataset loading, train/test splitting, model
    training, evaluation and saving. It is intended for examples and
    testing rather than production use.

    Attributes
    ----------
    data_size : int
        Maximum number of samples to use when loading the built-in
        California housing dataset.
    x, y : array-like
        Features and target for the dataset.
    x_train, x_test, y_train, y_test : array-like
        Train/test splits.
    model : sklearn estimator
        Trained regression model.
    score : float
        Last evaluated score (RMSE).
    """

    def __init__(self, data_size: int = 500):
        self.data_size = data_size

        self.x = None
        self.y = None

        self.x_train = None
        self.x_test = None
        self.y_train = None
        self.y_test = None

        self.model = None
        self.score = None

    def load_dataset(
        self, dataset_name="california_housing"
    ):  # pylint: disable=no-member
        """Load a dataset by name.

        Parameters
        ----------
        dataset_name : str
            Either "california_housing" (default) or "ames_housing".

        Returns
        -------
        dict
            Status information including sample and feature counts.
        """

        if dataset_name == "ames_housing":
            housing = fetch_openml(name="house_prices", as_frame=True)

            # Keep only numerical features
            x = housing.data.select_dtypes(include="number").iloc[
                : self.data_size
            ]  # pylint: disable=no-member

            self.y = housing.target.iloc[: self.data_size]  # pylint: disable=no-member

            # Replace missing values with the median
            imputer = SimpleImputer(strategy="median")
            self.x = imputer.fit_transform(x)

        else:
            housing = fetch_california_housing(as_frame=True)

            self.x = housing.data.select_dtypes(include="number").iloc[
                : self.data_size
            ]  # pylint: disable=no-member
            self.y = housing.target.iloc[: self.data_size]  # pylint: disable=no-member

        time.sleep(2)

        return {
            "Status": Status.SUCCESS,
            "dataset": dataset_name,
            "samples": len(self.x),
            "features": self.x.shape[1],
        }

    def split_dataset(self, test_size=0.2, random_state=42):
        """Split the loaded dataset into train and test sets.

        Parameters
        ----------
        test_size : float
            Proportion of the dataset to include in the test split.
        random_state : int
            Random seed for reproducibility.

        Returns
        -------
        dict
            Status information.
        """

        (
            self.x_train,
            self.x_test,
            self.y_train,
            self.y_test,
        ) = train_test_split(
            self.x,
            self.y,
            test_size=test_size,
            random_state=random_state,
        )

        time.sleep(2)

        return {
            "Status": Status.SUCCESS,
        }

    def train_model(self, fit_intercept=True):
        """Train a linear regression model on the training split.

        Parameters
        ----------
        fit_intercept : bool
            Whether to calculate the intercept for this model.

        Returns
        -------
        dict
            Status information.
        """

        self.model = LinearRegression(fit_intercept=fit_intercept)

        self.model.fit(
            self.x_train,
            self.y_train,
        )

        time.sleep(4)

        return {
            "Status": Status.SUCCESS,
        }

    def evaluate_model(self, metric="rmse"):
        """Evaluate the trained model on the test set.

        Parameters
        ----------
        metric : str
            Evaluation metric to compute. Only "rmse" is supported.

        Returns
        -------
        dict
            Status and computed metric value.
        """

        predictions = self.model.predict(self.x_test)

        if metric == "rmse":
            self.score = (
                mean_squared_error(
                    self.y_test,
                    predictions,
                )
                ** 0.5
            )
        else:
            raise ValueError(f"Unsupported metric: {metric}")

        time.sleep(3)

        return {
            "Status": Status.SUCCESS,
            "rmse": self.score,
        }

    def plot_results(self, output_dir="results/plots"):
        """Generate diagnostic plots for the trained housing model.

        Parameters
        ----------
        output_dir : str
            Directory where the generated plots will be saved.

        Returns
        -------
        dict
            Status information and paths to the generated plots.
        """
        if self.model is None:
            raise RuntimeError("Model must be trained before plotting.")

        if self.x_test is None or self.y_test is None:
            raise RuntimeError("Dataset must be split before plotting.")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        images = []
        index = 1
        predictions = self.model.predict(self.x_test)
        residuals = self.y_test - predictions

        # ---------------------------------------------------------
        # 1. Actual vs Predicted
        # ---------------------------------------------------------
        plt.figure(figsize=(8, 6))

        plt.scatter(
            self.y_test,
            predictions,
            alpha=0.7,
        )

        min_value = min(self.y_test.min(), predictions.min())
        max_value = max(self.y_test.max(), predictions.max())

        plt.plot(
            [min_value, max_value],
            [min_value, max_value],
            linestyle="--",
        )

        plt.xlabel("Actual House Value")
        plt.ylabel("Predicted House Value")
        plt.title("Actual vs Predicted House Values")

        image_path = "actual_vs_predicted.png"
        plt.savefig(output_dir / image_path, dpi=150)
        plt.close()

        images.append(
            {
                "title": "Actual vs Predicted House Values",
                "file_path": image_path,
                "index": index,
            }
        )
        index = +1

        # ---------------------------------------------------------
        # 2. Residual distribution
        # ---------------------------------------------------------
        plt.figure(figsize=(8, 6))

        plt.hist(
            residuals,
            bins=30,
            edgecolor="black",
        )

        plt.axvline(
            x=0,
            linestyle="--",
        )

        plt.xlabel("Residual")
        plt.ylabel("Frequency")
        plt.title("Distribution of Prediction Errors")

        image_path = "residual_distribution.png"
        plt.savefig(output_dir / image_path, dpi=150)
        plt.close()

        images.append(
            {
                "title": "Distribution of Prediction Errors",
                "file_path": image_path,
                "index": index,
            }
        )
        index = +1

        # ---------------------------------------------------------
        # 3. Feature coefficients
        # ---------------------------------------------------------
        if hasattr(self.model, "coef_"):
            coefficients = np.asarray(self.model.coef_)

            # Use generic names if feature names are unavailable.
            feature_names = getattr(
                self,
                "feature_names",
                [f"Feature {i}" for i in range(len(coefficients))],
            )

            # Sort by absolute coefficient magnitude.
            order = np.argsort(np.abs(coefficients))

            plt.figure(figsize=(9, 6))

            plt.barh(
                np.array(feature_names)[order],
                coefficients[order],
            )

            plt.xlabel("Linear Regression Coefficient")
            plt.ylabel("Feature")
            plt.title("Feature Influence on House Value")

            image_path = "feature_coefficients.png"
            plt.savefig(output_dir / image_path, dpi=150)
            plt.close()

            images.append(
                {
                    "title": "Feature Influence on House Value",
                    "file_path": image_path,
                    "index": index,
                }
            )
            index = +1

        image_gallery_to_html(
            images=images,
            output_file=output_dir / "plots.html",
            file_title="Plots for Housing Model",
        )

        return {"Status": Status.SUCCESS}

    def save_model(
        self,
        output_path="results/housing_model.pkl",
    ):
        """Save the trained model to disk.

        Parameters
        ----------
        output_path : str
            File path where the model will be saved. Parent directories
            will be created if needed.

        Returns
        -------
        dict
            Status information.
        """

        Path(output_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # joblib.dump(self.model, output_path)

        time.sleep(2)

        return {
            "Status": Status.SUCCESS,
        }
