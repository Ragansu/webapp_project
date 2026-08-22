"""Module for generating HTML reports and managing analysis sequences."""

import os
import glob
from pathlib import Path
from datetime import datetime

import json
import warnings
import logging
import fnmatch
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore")

now = datetime.now()
formatted_time = now.strftime("%Y%m%d_%H_%M_%S")

current_dir = os.getcwd()

# 3. Join the safe, formatted string
_DEFAULT_SAVE_DIR = os.path.join(current_dir, formatted_time)
repo_dir = os.path.dirname(os.path.abspath(__file__))


def _get_template_environment():
    """Create and configure the Jinja2 environment used by report templates."""
    return Environment(
        loader=FileSystemLoader(f"{repo_dir}/templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )


def _display_name(file_path, pattern):
    """Create a human-readable display name from a report file path.

    Removes the HTML extension and any matching wildcard prefix or suffix,
    then replaces underscores with spaces and capitalizes the result.

    Args:
        file_path: Path to the report file.
        pattern: File-matching pattern used to identify the report.

    Returns:
        The formatted display name, or an empty string if no name is available.
    """

    file_name = os.path.basename(file_path)

    # 1. Determine base name stem
    if file_name == "index.html":
        name = os.path.basename(os.path.dirname(file_path))
    else:
        name = file_name.removesuffix(".html")

        # Only strip prefix/suffix if pattern actually contains a wildcard '*'
        if "*" in pattern:
            pattern_stem = pattern.removesuffix(".html")
            prefix, _, suffix = pattern_stem.partition("*")

            if prefix and name.startswith(prefix) and len(name) > len(prefix):
                name = name[len(prefix) :]

            if suffix and name.endswith(suffix):
                name = name[: -len(suffix)]

    # 2. Normalize underscores and whitespace
    name = name.replace("_", " ").strip()

    # 3. Capitalize first letter safely (or return empty string if empty)
    return name.capitalize() if name else ""


def _get_files_dict(file_paths, processed_files, root_dir, pattern):
    """Build report file dictionaries for files not already processed."""
    files = []

    for file_path in file_paths:

        if not fnmatch.fnmatch(os.path.basename(file_path), pattern):
            continue
        if file_path in processed_files:
            continue

        files.append(
            {
                "name": _display_name(file_path, pattern),
                "path": os.path.relpath(file_path, root_dir),
            }
        )

    return sorted(files, key=lambda item: item["name"])


def create_results_index(  # pylint: disable=too-many-locals
    patterns=None,
    directory=_DEFAULT_SAVE_DIR,
    output_file="index.html",
    title="ML Analysis Results Index",
):
    """Create an HTML index using user-defined file patterns."""

    env = _get_template_environment()
    root_dir = os.path.dirname(output_file)

    # ---------------------------------------------------------
    # 1. Collect the files that should actually be indexed.
    # ---------------------------------------------------------
    html_files = set()

    if patterns is None:
        patterns = {}

    patterns = {
        "Indexes": "index.html",
        **patterns,
    }

    # Files directly in the root directory.
    for file_path in glob.glob(os.path.join(directory, "*.html")):
        html_files.add(file_path)

    # Check each immediate subfolder.
    top_folders = glob.glob(os.path.join(directory, "*/"))

    for folder in top_folders:
        index_path = os.path.join(folder, "index.html")

        if os.path.exists(index_path):
            # If the folder has an index, only show the index.
            html_files.add(index_path)
        else:
            # Otherwise show all HTML files in that folder.
            for file_path in glob.glob(os.path.join(folder, "*.html")):
                html_files.add(file_path)

    # Never include the index we're generating.
    html_files.discard(output_file)

    html_files = sorted(html_files)

    # ---------------------------------------------------------
    # 2. Apply patterns to the collected files.
    # ---------------------------------------------------------
    file_groups = {}
    processed_files = set()

    for group_name, pattern in patterns.items():

        group_files = _get_files_dict(html_files, processed_files, root_dir, pattern)

        if group_files:
            file_groups[group_name] = group_files

    # ---------------------------------------------------------
    # 3. Anything that didn't match a pattern goes into
    #    "Other Reports".
    # ---------------------------------------------------------
    misc_files = _get_files_dict(html_files, processed_files, root_dir, "*.html")

    if misc_files:
        file_groups["Other Reports"] = misc_files

    # ---------------------------------------------------------
    # 4. Render template.
    # ---------------------------------------------------------
    template_data = {
        "title": title,
        "html_files": html_files,
        "file_groups": file_groups,
        "output_file_stem": Path(output_file).stem,
    }

    template = env.get_template("index_template.html")
    html_content = template.render(**template_data)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("Index created: %s", output_file)
    logger.info("Total files indexed: %s", len(html_files))
    logger.info("Groups: %s", len(file_groups))


def config_to_html(config, filename="config_report.html"):
    """Creates an HTML report of the configuration object with compact layout."""

    # Create Jinja2 environment
    env = _get_template_environment()

    # Prepare data for template
    list_attrs = []
    simple_attrs = []  # List of tuples (name, value)
    dict_attrs = {}
    dictionary_data = {}

    for attr_name, attr_value in vars(config).items():
        if attr_name in config.exclude_list:
            continue

        if isinstance(attr_value, list):
            list_attrs.append((attr_name, attr_value))

        elif isinstance(attr_value, dict):
            # Store other dictionaries as-is
            dict_attrs[attr_name] = attr_name
            dictionary_data[attr_name] = attr_value

        else:
            simple_attrs.append((attr_name, attr_value))

    # Render template
    template = env.get_template("config_template.html")
    html_content = template.render(
        simple_attrs=simple_attrs,
        list_attrs=list_attrs,
        dict_attrs=dict_attrs,
        dictionary_data=dictionary_data,
    )

    # Save to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)


def text_report_to_html(text, title="Report", filename="text_report.html"):
    """Creates an HTML report with a text block using Jinja2.

    Args:
        text: The text content to include in the report
        title: The title of the report
        filename: The output HTML filename
    """

    # Setup Jinja2 environment
    env = _get_template_environment()

    # Prepare data for template
    template_data = {
        "title": title,
        "text": text,
    }

    # Load and render template
    template = env.get_template("text_report_template.html")
    html_content = template.render(**template_data)

    # Write to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filename


def image_report_to_html(
    base64_images,
    info_dict=None,
    title="Analysis Results",
    filename="image_report.html",
):
    """Creates an HTML report with base64 images and optional dictionary information using Jinja2.

    Args:
        base64_images: A single base64 image string or list of base64 image strings
        info_dict: Optional dictionary with information to display
        title: Report title
        filename: Output HTML filename
    """

    # Setup Jinja2 environment
    env = _get_template_environment()

    # Handle single image or list of images
    if isinstance(base64_images, str):
        base64_images = [base64_images]

    # Prepare data for template
    template_data = {
        "title": title,
        "base64_images": base64_images,
        "info_dict": info_dict,
    }

    # Load and render template
    template = env.get_template("image_report_template.html")
    html_content = template.render(**template_data)

    # Write to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filename


def save_table_html(df, title, filename):
    """Saves a DataFrame as an HTML file using Jinja2 templates for clean appending."""

    # Setup Jinja2 environment
    env = _get_template_environment()

    # Generate table HTML
    table_html = df.to_html(
        index=False, border=0, justify="center", classes="dataframe"
    )

    # Data file to store sections
    data_file = os.path.splitext(filename)[0] + "_sections.json"

    # Create new section
    new_section = {
        "title": title,
        "table_html": table_html,
        "created": datetime.now().isoformat(),
    }

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            sections = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        sections = []

    # Find existing section by title
    existing_index = next(
        (i for i, section in enumerate(sections) if section.get("title") == title),
        None,
    )

    if existing_index is not None:
        sections[existing_index] = new_section
    else:
        sections.append(new_section)

    # Save sections to data file
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(sections, f, indent=2)

    # Render template with all sections
    template_data = {
        "sections": sections,
        "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    template = env.get_template("table_section_template.html")
    html_content = template.render(**template_data)

    # Write HTML file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filename


def image_gallery_to_html(
    images,
    output_file="image_gallery.html",
    file_title="Image Gallery",
    dictionary_data=None,
):  # pylint: disable=too-many-arguments,too-many-positional-arguments
    """
    Generate an HTML image gallery page from a list of image entries.

    Args:
        images: A list of dictionaries describing each image. Each item should
            include at least a file path or source and optional metadata such as
            title, caption, and index.
        output_file: Name or path of the generated HTML output file.
        file_title: Title displayed on the rendered gallery page.
        dictionary_data: Optional additional metadata to pass to the template.

    Example:
        ```python
        images = []
        image_path = "actual_vs_predicted.png"
        plt.savefig(output_dir / image_path, dpi=150)
        plt.close()

        images.append(
            {
                "title": "Actual vs Predicted House Values",
                "file_path": image_path,
                "index": 0,
            }
        )

        image_gallery_to_html(
            images=images,
            output_file="image_gallery.html",
            file_title="Image Gallery",
        )
        ```
    """

    # Setup Jinja2 environment
    env = _get_template_environment()

    # Prepare template data
    template_data = {
        "file_title": file_title,
        "images": images,
        "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if dictionary_data:
        template_data["dictionary_data"] = dictionary_data

    # Load and render template
    template = env.get_template("image_gallery_template.html")
    html_content = template.render(**template_data)

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_file
