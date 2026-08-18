import os
import argparse 
from analysisweb.sequencer import Sequencer
from analysisweb.reports import text_report_to_html
from example_project import HousingModel

parser = argparse.ArgumentParser(description="Train the model")
parser.add_argument(
    "--unique-date",
    type=str,
    default=os.getenv("UNIQUE_TIME_STAMP"),
    help="Unique date stamp for the model",
)

model = HousingModel(
    data_size=500,
)

args = parser.parse_args()

initial_entry = {
    "date": args.unique_date,
    "pid" : 0,
    "dataset": "California Housing",
    "model": "Linear Regression",
    "samples": 500,
    "run_time": 0,
    "rmse": "-",
    "Status": "Launched",
    "link": "/",
}

plots_dir = f"results/plots_{args.unique_date}"

os.makedirs(plots_dir)

sequencer = Sequencer(
    initial_entry=initial_entry,
    plots_dir=plots_dir,
    json_dir="json",
)


sequencer.start()

sequencer.add_algorithm(
    model.load_dataset,
    dataset_name="california_housing",
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
    model.save_model,
    output_path="results/housing_model.pkl",
)

str_sq = sequencer.print_sequence()
text_report_to_html(
    text=str_sq,
    filename=os.path.join(plots_dir, "sequence_report.html"),
    title="Execution Sequence",
)
sequencer.run()

sequencer.end()
