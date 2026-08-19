# AnalysisWeb Package

<!-- [![Documentation Status](https://readthedocs.org/projects/black-swan-pkg/badge/?version=latest)](https://black-swan-pkg.readthedocs.io/en/latest/?badge=latest) -->

you can install this package by 
```shell
pip install AnalysisWeb
```

The package consists of 5 function :

* 1 `create_results_index`: Creates an HTML index page linking to all result files.
* 2 `config_to_html` : Creates an HTML report of the configuration object with compact layout.
* 3 `image_report_to_html` : Creates an HTML report with a base64 image and dictionary information.
* 4 `save_table_html` : Saves a DataFrame as an HTML file using template markers for clean appending
* 5 `image_gallery_to_html` : Create an HTML page with multiple base64 images in a gallery layout.

Use the functions above to create the `*.html` pages for each run 

## Sequencer 

The package consists of the `Sequencer` Class which helps maintain the CSV file system required for the index page

For each process (eg. "fit", "valid", "analysis" ...) set the result as a string (eg. "Fitting") use the Sequencer to connect between the processes and update the status. 

### Example usage
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

## Web APP
you can launch the webapp with 

```bash
analysisweb --results-dir ./results/ --json-dir json_file/ --config ./static/dashboard.yaml
```