# AnalysisWeb

[![Tests](https://github.com/Ragansu/webapp_project/actions/workflows/run_pytest.yml/badge.svg)](https://github.com/Ragansu/webapp_project/actions/workflows/run_pytest.yml) [![PyPI version](https://img.shields.io/pypi/v/AnalysisWeb.svg)](https://pypi.org/project/AnalysisWeb/)

**AnalysisWeb** is a lightweight local web dashboard and Python toolkit for managing and visualizing analysis results.

It is designed around a simple workflow:

1. Run an analysis or experiment.
2. Store its results in a structured directory.
3. Generate HTML reports and visualizations.
4. Track the execution status of analysis steps.
5. Browse everything through a local Flask web interface.

The package also provides a `Sequencer` class for building multi-step analysis pipelines with live execution status and persistent run metadata.

---

## Features

- 📊 Local web dashboard for analysis results
- 📁 Automatic indexing of result files
- 🧾 HTML report generation
- 🖼️ Image reports and image galleries
- 📋 DataFrame-to-HTML tables
- ⚙️ Configuration-to-HTML reports
- 🔄 Multi-step analysis sequencing
- 📈 Execution status and timing tracking
- 🧩 Plugin-based job loading
- 💻 Command-line interface
- 🚀 Designed to run locally without a database or external service


## High Level Summary

                 ┌─────────────────────┐
                 │   Analysis Code     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │      Sequencer      │
                 │                     │
                 │  Step 1             │
                 │  Step 2             │
                 │  Step 3             │
                 │  ...                │
                 └──────────┬──────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
       ┌──────────────┐           ┌────────────────┐
       │ JSON Metadata│           │ Result Files   │
       └──────┬───────┘           └────────┬───────┘
              │                            │
              └─────────────┬──────────────┘
                            ▼
                 ┌─────────────────────┐
                 │    Flask Dashboard  │
                 └─────────────────────┘

---

## Installation

### From PyPI

```bash
pip install AnalysisWeb
```
### From Source
```bash
git clone https://github.com/Ragansu/webapp_project.git
cd webapp_project
pip install -e .
```

## Sequencer 

The package consists of the `Sequencer` Class which helps maintain the Json file system required for the index page. For each process (eg. "fit", "valid", "analysis" ...) set the result as a string (eg. "Fitting") use the Sequencer to connect between the processes and update the status. 

## Example usage
```python
from your_project import Model  # Example of a class which handles the main functionalities.
from some_dataset import 

model = Model()

sequencer = Sequencer(
    plots_dir=plots_dir,
    json_dir="json",
)

sequencer.start()

sequencer.add_algorithm(
    model.analyze, train_sets=train_sets
)

sequencer.add_algorithm(model.compute_yield, train_sets=train_sets)

sequencer.add_algorithm(
    model.validation,
    test_sets=test_sets,
)

sequencer.print_sequence()
sequencer.run()
sequencer.end()

```

For more deatils checkout the example scripts at `example`. The scripts include a `job_manager.py` to launch scripts from the action button, `example_project.py` and `run_script.py` to run the jobs and `example_dash.yaml` for the dashboard config. One the run the example python job with

```bash
cd example
python run_scripts --unique-date 20260819_17_29_45
```

The web-app can be lanched from the `example` directory with,

```bash
analysisweb --results-dir ./results/ --json-dir json  --config ./example_dash.yaml 
```

### NOTE : 
In the beging you might be required to create the directories for results and json 
