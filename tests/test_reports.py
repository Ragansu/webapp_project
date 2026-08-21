"""Tests for the HTML report generation utilities."""

import os
import json
import logging
from types import SimpleNamespace

import pandas as pd
import pytest

from analysisweb.reports import (
    config_to_html,
    display_name,
    create_results_index,
    image_gallery_to_html,
    image_report_to_html,
    save_table_html,
    text_report_to_html,
)


@pytest.mark.parametrize(
    "file_path, pattern, expected",
    [
        # Case 1: Special handling for index.html (uses parent directory name)
        ("reports/subfolder/index.html", "*.html", "Subfolder"),
        ("/var/www/my_project/index.html", "index.html", "My project"),
        # Case 2: Standard file name formatting (underscores to spaces, title case)
        ("my_test_report.html", "*.html", "My test report"),
        # Case 3: Pattern prefix stripping
        ("report_sales_data.html", "report_*.html", "Sales data"),
        ("model_evaluation_metrics.html", "model_*.html", "Evaluation metrics"),
        # Case 4: Pattern suffix stripping
        ("data_summary_v1.html", "*_v1.html", "Data summary"),
        # Case 5: Combined prefix and suffix stripping
        (
            "metrics_classification_v2.html",
            "metrics_*_v2.html",
            "Classification",
        ),
        # Case 6: Exact pattern stem with wildcard (Fixed from previous test failure)
        ("analytics.html", "analytics*.html", "Analytics"),
        ("analytics_report.html", "analytics*.html", "Report"),
        # Case 7: Edge case - leading spaces / whitespace stripping
        ("_unnamed_report.html", "_*.html", "Unnamed report"),
    ],
)


# ==============================================================================
# Tests for display_name
# ==============================================================================


def test_display_name(file_path, pattern, expected):
    """Verify display_name transforms file paths and pattern stems correctly."""
    assert display_name(file_path, pattern) == expected


# ==============================================================================
# Tests for create_results_index
# ==============================================================================


def test_create_results_index_basic_flow(tmp_path, mock_template_env):
    """Test full file indexing, pattern matching, grouping, and template context."""
    _, mock_template = mock_template_env

    save_dir = tmp_path / "results"
    save_dir.mkdir()

    (save_dir / "report_summary.html").touch()
    (save_dir / "model_accuracy.html").touch()
    (save_dir / "random_file.html").touch()

    subfolder_a = save_dir / "subfolder_a"
    subfolder_a.mkdir()
    (subfolder_a / "index.html").touch()
    (subfolder_a / "ignore_me.html").touch()

    subfolder_b = save_dir / "subfolder_b"
    subfolder_b.mkdir()
    (subfolder_b / "deep_report.html").touch()

    output_index = str(save_dir / "index.html")

    custom_patterns = {
        "Reports": "report_*.html",
        "Models": "model_*.html",
    }

    create_results_index(
        patterns=custom_patterns,
        directory=str(save_dir),
        output_file=output_index,
        title="Custom Test Title",
    )

    assert os.path.exists(output_index)
    with open(output_index, "r", encoding="utf-8") as f:
        assert f.read() == "<html><body>Mocked Index</body></html>"

    mock_template.render.assert_called_once()
    render_kwargs = mock_template.render.call_args.kwargs

    assert render_kwargs["title"] == "Custom Test Title"
    assert render_kwargs["output_file_stem"] == "index"

    groups = render_kwargs["file_groups"]

    assert "Indexes" in groups
    assert groups["Indexes"][0]["name"] == "Subfolder a"

    assert "Reports" in groups
    assert groups["Reports"][0]["name"] == "Summary"

    assert "Models" in groups
    assert groups["Models"][0]["name"] == "Accuracy"

    assert "Other Reports" in groups
    unmatched_names = [f["name"] for f in groups["Other Reports"]]
    assert "Random file" in unmatched_names
    assert "Deep report" in unmatched_names


def test_create_results_index_excludes_output_file(tmp_path, mock_template_env):
    """Ensure the generated output index file itself is never indexed."""
    _, mock_template = mock_template_env

    output_index = str(tmp_path / "index.html")

    create_results_index(
        directory=str(tmp_path),
        output_file=output_index,
    )

    render_kwargs = mock_template.render.call_args.kwargs
    indexed_files = render_kwargs["html_files"]

    assert output_index not in indexed_files


def test_create_results_index_non_existent_directory(tmp_path, mock_template_env):
    """Test execution when target directory does not exist."""
    _, mock_template = mock_template_env

    non_existent_dir = str(tmp_path / "does_not_exist")
    output_index = str(tmp_path / "index.html")

    create_results_index(
        directory=non_existent_dir,
        output_file=output_index,
    )

    render_kwargs = mock_template.render.call_args.kwargs

    assert len(render_kwargs["html_files"]) == 0
    assert len(render_kwargs["file_groups"]) == 0


def test_create_results_index_logger_output(tmp_path, mock_template_env, caplog):
    """Verify logger info output messages using pytest caplog fixture."""
    _, _ = mock_template_env

    (tmp_path / "report_a.html").touch()
    (tmp_path / "report_b.html").touch()
    output_index = str(tmp_path / "index.html")

    with caplog.at_level(logging.INFO):
        create_results_index(
            patterns={"Reports": "report_*.html"},
            directory=str(tmp_path),
            output_file=output_index,
        )

    assert f"Index created: {output_index}" in caplog.text
    assert "Total files indexed: 2" in caplog.text
    assert "Groups: 1" in caplog.text


def test_create_results_index_excludes_output_file(tmp_path, mock_template_env):
    """Ensure the generated output index file itself is never indexed."""
    _, mock_template = mock_template_env

    output_index = str(tmp_path / "index.html")

    # Run index creation on empty directory where output_file sits
    create_results_index(
        directory=str(tmp_path),
        output_file=output_index,
    )

    render_kwargs = mock_template.render.call_args.kwargs
    indexed_files = render_kwargs["html_files"]

    # Verify output_file path was discarded
    assert output_index not in indexed_files


def test_create_results_index_uses_folder_html_when_no_nested_index(tmp_path):
    """Indexes HTML files from folders that do not contain index.html."""
    results_dir = tmp_path / "results"
    nested_dir = results_dir / "run1"
    nested_dir.mkdir(parents=True)

    report = nested_dir / "report.html"
    report.write_text("<html>report</html>", encoding="utf-8")

    output_file = tmp_path / "results_index.html"

    create_results_index(
        directory=str(results_dir),
        output_file=str(output_file),
    )

    assert output_file.exists()

    html = output_file.read_text(encoding="utf-8")
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

    config_to_html(config, filename=str(output_file))

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

    config_to_html(config, filename=str(output_file))

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

    # Place index inside tmp_path so relative paths are cleanly resolved
    results_dir = tmp_path / "results"
    results_dir.mkdir()

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
