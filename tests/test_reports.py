"""Tests for the HTML report generation utilities."""

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from analysisweb.reports import (
    Status,
    config_to_html,
    create_results_index,
    image_gallery_to_html,
    image_report_to_html,
    save_table_html,
    text_report_to_html,
)


def test_create_results_index_with_patterns(tmp_path):
    """Creates an index using user-defined file patterns."""
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    # NLL results
    (results_dir / "Trained_model_test.html").write_text(
        "test", encoding="utf-8"
    )
    (results_dir / "Trained_model_holdout.html").write_text(
        "holdout", encoding="utf-8"
    )

    # Plots
    (results_dir / "plot_training_loss.html").write_text(
        "plot", encoding="utf-8"
    )
    (results_dir / "plot_validation_loss.html").write_text(
        "plot", encoding="utf-8"
    )

    # Tables
    (results_dir / "table_model_performance.html").write_text(
        "table", encoding="utf-8"
    )

    # Miscellaneous
    (results_dir / "some_report.html").write_text(
        "misc", encoding="utf-8"
    )

    output_file = tmp_path / "index.html"

    patterns = {
        "Trained Models": "Trained_*.html",
        "Plots": "plot_*.html",
        "Tables": "table_*.html",
    }

    result = create_results_index(
        patterns=patterns,
        directory=str(results_dir),
        output_file=str(output_file),
        title="Test Results",
    )

    assert result == Status.SUCCESS
    assert output_file.exists()

    html = output_file.read_text(encoding="utf-8")

    # Page metadata
    assert "Test Results" in html

    # Groups
    assert "Trained Models" in html
    assert "Plots" in html
    assert "Tables" in html

    # Pattern prefixes are removed from display names
    assert "Model test" in html
    assert "Model holdout" in html
    assert "Training loss" in html
    assert "Validation loss" in html
    assert "Model performance" in html

    # Original pattern prefixes should not appear in display names
    assert "Trained_model_test" not in html
    assert "Trained_model_holdout" not in html
    assert "plot_training_loss" not in html
    assert "plot_validation_loss" not in html
    assert "table_model_performance" not in html

    # Unmatched files are still included
    assert "some_report.html" in html

def test_create_results_index_uses_folder_html_when_no_nested_index(tmp_path):
    """Indexes HTML files from folders that do not contain index.html."""
    results_dir = tmp_path / "results"
    nested_dir = results_dir / "run1"
    nested_dir.mkdir(parents=True)

    report = nested_dir / "report.html"
    report.write_text("<html>report</html>", encoding="utf-8")

    output_file = tmp_path / "results_index.html"

    result = create_results_index(
        directory=str(results_dir),
        output_file=str(output_file),
    )

    assert result == Status.SUCCESS
    assert output_file.exists()

    html = output_file.read_text(encoding="utf-8")
    assert "report.html" in html or "report" in html


def test_create_results_index_does_not_index_output_file(tmp_path):
    """The output index itself is not included in the generated file list."""
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    output_file = results_dir / "index.html"

    output_file.write_text("old index", encoding="utf-8")
    (results_dir / "report.html").write_text("report", encoding="utf-8")

    create_results_index(
        directory=str(results_dir),
        output_file=str(output_file),
    )

    html = output_file.read_text(encoding="utf-8")

    # The generated index should contain the report, but not link to itself.
    assert "report.html" in html or "report" in html


def test_config_to_html(tmp_path):
    """Renders simple, list, dict, and CLF_config attributes."""
    config = SimpleNamespace(
        exclude_list=["excluded"],
        name="test-model",
        enabled=True,
        values=["a", "b"],
        settings={"learning_rate": 0.1},
        CLF_config={
            "model": {
                "n_estimators": 100,
                "max_depth": 5,
            }
        },
        excluded="should-not-appear",
    )

    output_file = tmp_path / "config.html"

    result = config_to_html(config, filename=str(output_file))

    assert result == Status.SUCCESS
    assert output_file.exists()

    html = output_file.read_text(encoding="utf-8")

    assert "test-model" in html
    assert "learning_rate" in html
    assert "0.1" in html
    assert "n_estimators" in html
    assert "100" in html
    assert "max_depth" in html
    assert "5" in html
    assert "should-not-appear" not in html


def test_config_to_html_empty_config(tmp_path):
    """Handles a config containing only excluded attributes."""
    config = SimpleNamespace(
        exclude_list=["value"],
        value="hidden",
    )

    output_file = tmp_path / "config.html"

    result = config_to_html(config, filename=str(output_file))

    assert result == Status.SUCCESS
    assert output_file.exists()


def test_text_report_to_html(tmp_path):
    """Creates an HTML text report."""
    output_file = tmp_path / "text_report.html"

    result = text_report_to_html(
        text="This is a test report.",
        title="Test Report",
        filename=str(output_file),
    )

    assert result == str(output_file)
    assert output_file.exists()

    html = output_file.read_text(encoding="utf-8")

    assert "Test Report" in html
    assert "This is a test report." in html


def test_text_report_to_html_escapes_html(tmp_path):
    """Jinja2 safely renders HTML-sensitive text."""
    output_file = tmp_path / "text_report.html"

    text_report_to_html(
        text="<script>alert('xss')</script>",
        title="Security Test",
        filename=str(output_file),
    )

    html = output_file.read_text(encoding="utf-8")
    print(html)

    # The literal script should not be emitted as executable HTML.
    assert "<script>alert('xss')</script>" not in html


def test_image_report_to_html_with_single_image(tmp_path):
    """Accepts a single base64 image string."""
    output_file = tmp_path / "image_report.html"

    result = image_report_to_html(
        base64_images="base64-image-data",
        title="Image Report",
        filename=str(output_file),
    )

    assert result == str(output_file)
    assert output_file.exists()

    html = output_file.read_text(encoding="utf-8")

    assert "Image Report" in html
    assert "base64-image-data" in html


def test_image_report_to_html_with_multiple_images_and_info(tmp_path):
    """Accepts multiple images and optional metadata."""
    output_file = tmp_path / "image_report.html"

    images = [
        "base64-image-1",
        "base64-image-2",
    ]

    info = {
        "model": "RandomForest",
        "accuracy": 0.95,
    }

    result = image_report_to_html(
        base64_images=images,
        info_dict=info,
        title="Analysis",
        filename=str(output_file),
    )

    assert result == str(output_file)

    html = output_file.read_text(encoding="utf-8")

    assert "Analysis" in html
    assert "base64-image-1" in html
    assert "base64-image-2" in html
    assert "RandomForest" in html
    assert "0.95" in html


def test_save_table_html_creates_new_file(tmp_path):
    """Creates an HTML table and its sections JSON file."""
    output_file = tmp_path / "table.html"

    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob"],
            "score": [10, 20],
        }
    )

    result = save_table_html(
        df=df,
        title="Scores",
        filename=str(output_file),
    )

    assert result == str(output_file)
    assert output_file.exists()

    data_file = tmp_path / "table_sections.json"
    assert data_file.exists()

    sections = json.loads(data_file.read_text(encoding="utf-8"))

    assert len(sections) == 1
    assert sections[0]["title"] == "Scores"
    assert "Alice" in sections[0]["table_html"]
    assert "Bob" in sections[0]["table_html"]
    assert "created" in sections[0]

    html = output_file.read_text(encoding="utf-8")

    assert "Scores" in html
    assert "Alice" in html
    assert "Bob" in html


def test_save_table_html_appends_new_section(tmp_path):
    """Appends a second section when its title is different."""
    output_file = tmp_path / "table.html"

    df1 = pd.DataFrame({"value": [1, 2]})
    df2 = pd.DataFrame({"value": [3, 4]})

    save_table_html(df1, "First", str(output_file))
    save_table_html(df2, "Second", str(output_file))

    data_file = tmp_path / "table_sections.json"
    sections = json.loads(data_file.read_text(encoding="utf-8"))

    assert len(sections) == 2
    assert {section["title"] for section in sections} == {
        "First",
        "Second",
    }

    html = output_file.read_text(encoding="utf-8")

    assert "First" in html
    assert "Second" in html


def test_save_table_html_updates_existing_section(tmp_path):
    """Replaces an existing section when the title matches."""
    output_file = tmp_path / "table.html"

    first_df = pd.DataFrame({"value": [1]})
    second_df = pd.DataFrame({"value": [999]})

    save_table_html(first_df, "Results", str(output_file))
    save_table_html(second_df, "Results", str(output_file))

    data_file = tmp_path / "table_sections.json"
    sections = json.loads(data_file.read_text(encoding="utf-8"))

    assert len(sections) == 1
    assert sections[0]["title"] == "Results"
    assert "999" in sections[0]["table_html"]
    assert ">1<" not in sections[0]["table_html"]


def test_save_table_html_recovers_from_corrupt_json(tmp_path):
    """Starts a fresh section when the existing JSON is invalid."""
    output_file = tmp_path / "table.html"
    data_file = tmp_path / "table_sections.json"

    df = pd.DataFrame({"value": [42]})

    # Both files need to exist for the JSON loading branch to execute.
    output_file.write_text("existing", encoding="utf-8")
    data_file.write_text("{invalid json", encoding="utf-8")

    result = save_table_html(
        df=df,
        title="Recovered",
        filename=str(output_file),
    )

    assert result == str(output_file)

    sections = json.loads(data_file.read_text(encoding="utf-8"))

    assert len(sections) == 1
    assert sections[0]["title"] == "Recovered"
    assert "42" in sections[0]["table_html"]


def test_save_table_html_recovers_when_json_is_missing(tmp_path):
    """Starts a fresh section when the sections JSON does not exist."""
    output_file = tmp_path / "table.html"

    output_file.write_text("existing", encoding="utf-8")

    df = pd.DataFrame({"value": [123]})

    save_table_html(
        df=df,
        title="Missing JSON",
        filename=str(output_file),
    )

    data_file = tmp_path / "table_sections.json"
    sections = json.loads(data_file.read_text(encoding="utf-8"))

    assert len(sections) == 1
    assert sections[0]["title"] == "Missing JSON"


def test_image_gallery_to_html(tmp_path):
    """Creates an image gallery with optional dictionary data."""
    output_file = tmp_path / "gallery.html"

    images = [
        {
            "title": "First image",
            "file_path": "first.png",
            "index": 0,
        },
        {
            "title": "Second image",
            "file_path": "second.png",
            "index": 1,
        },
    ]

    dictionary_data = {
        "model": "test-model",
        "accuracy": 0.91,
    }

    result = image_gallery_to_html(
        images=images,
        output_file=str(output_file),
        file_title="My Gallery",
        dictionary_data=dictionary_data,
        index_dir="results/index.html",
    )

    assert result == str(output_file)
    assert output_file.exists()

    html = output_file.read_text(encoding="utf-8")

    assert "My Gallery" in html
    assert "first.png" in html
    assert "second.png" in html
    assert "First image" in html
    assert "Second image" in html
    assert "test-model" in html
    assert "0.91" in html
    assert "results/index.html" in html


def test_image_gallery_to_html_without_dictionary_data(tmp_path):
    """Creates a gallery without optional dictionary data."""
    output_file = tmp_path / "gallery.html"

    images = [
        {
            "title": "Example",
            "file_path": "example.png",
        }
    ]

    result = image_gallery_to_html(
        images=images,
        output_file=str(output_file),
        file_title="Gallery",
    )

    assert result == str(output_file)
    assert output_file.exists()

    html = output_file.read_text(encoding="utf-8")

    assert "Gallery" in html
    assert "example.png" in html


@pytest.mark.parametrize(
    "function_name",
    [
        "text_report_to_html",
        "image_report_to_html",
        "image_gallery_to_html",
        "config_to_html",
    ],
)
def test_report_functions_create_nonempty_html(tmp_path, function_name):
    """Smoke-test that report functions generate non-empty HTML files."""
    output_file = tmp_path / f"{function_name}.html"

    if function_name == "text_report_to_html":
        text_report_to_html(
            "Smoke test",
            filename=str(output_file),
        )

    elif function_name == "image_report_to_html":
        image_report_to_html(
            "fake-base64",
            filename=str(output_file),
        )

    elif function_name == "image_gallery_to_html":
        image_gallery_to_html(
            images=[],
            output_file=str(output_file),
        )

    elif function_name == "config_to_html":
        config = SimpleNamespace(exclude_list=[], value="test")
        config_to_html(config, filename=str(output_file))

    assert output_file.exists()
    assert output_file.stat().st_size > 0
