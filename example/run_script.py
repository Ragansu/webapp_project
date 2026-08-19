"""
run_script.py

Small example script which builds, trains and evaluates a housing
regression model using the example_project.HousingModel and the
analysisweb.Sequencer to stage steps and record results.

This script is intended to be run from the command line. It accepts a
single optional argument --unique-date which is used to namespace
output directories and run metadata.
"""

import os
import argparse
from example_project import HousingModel
from job_manager import get_initial_entry
from analysisweb.sequencer import Sequencer

current_dir = os.path.dirname(os.path.abspath(__file__))


def main():
    """Main entry point for the housing model training script."""
    parser = argparse.ArgumentParser(description="Train the model")
    parser.add_argument(
        "--unique-date",
        type=str,
        default=os.getenv("UNIQUE_TIME_STAMP"),
        help="Unique date stamp for the model",
    )

    parser.add_argument(
        "--ames-housing",
        action="store_true",
        default=False,
        help="Enable Only Testing",
    )

    args = parser.parse_args()

    model = HousingModel(
        data_size=500,
    )

    print("Starting to run")

    initial_entry = get_initial_entry(f"{current_dir}/example_dash.yaml")

    print("Finished getting config")

    initial_entry["date"] = args.unique_date

    plots_dir = f"results/plots_{args.unique_date}"
    if args.ames_housing:
        dataset_name = "ames_housing"
    else:
        dataset_name = "california_housing"

    os.makedirs(plots_dir)

    print(initial_entry)

    sequencer = Sequencer(
        initial_entry=initial_entry,
        plots_dir=plots_dir,
        json_dir="json",
    )

    sequencer.update({"Status": "Update table", "model": "Linear Regression"})

    sequencer.start()

    sequencer.add_algorithm(
        model.load_dataset,
        dataset_name=dataset_name,
    )

    sequencer.add_algorithm(
        model.split_dataset,
        test_size=0.2,
        random_state=42,
    )

    sequencer.add_algorithm(
        model.train_model,
        fit_intercept=True,
    )

    sequencer.add_algorithm(
        model.evaluate_model,
        metric="rmse",
    )

    sequencer.add_algorithm(
        model.plot_results,
        output_dir=plots_dir,
    )

    sequencer.add_algorithm(
        model.save_model,
        output_path=f"{plots_dir}/housing_model.pkl",
    )

    sequencer.print_sequence()
    sequencer.run()
    sequencer.end()


main()
