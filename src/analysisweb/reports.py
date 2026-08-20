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
    return Environment(
        loader=FileSystemLoader(f"{repo_dir}/templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )

def display_name(file_path, pattern):
    file_name = os.path.basename(file_path)

    if file_name == "index.html":
        name = os.path.basename(os.path.dirname(file_path))
    else:
        name = file_name.removesuffix(".html")
        pattern_stem = pattern.removesuffix(".html")

        prefix, _, suffix = pattern_stem.partition("*")

        if prefix and name.startswith(prefix):
            name = name[len(prefix):]

        if suffix and name.endswith(suffix):
            name = name[:-len(suffix)]

        name = name.replace("_", " ")
        name = name[:1].upper() + name[1:]

    return name.strip()


def create_results_index(
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
        group_files = []

        for file_path in html_files:
            file_name = os.path.basename(file_path)

            if not fnmatch.fnmatch(file_name, pattern):
                continue

            relative_path = os.path.relpath(file_path, root_dir)

            # Remove the matched pattern prefix/suffix from display name.
            name = file_name.removesuffix(".html")
            pattern_stem = pattern.removesuffix(".html")

            prefix, _, suffix = pattern_stem.partition("*")

            if prefix and name.startswith(prefix):
                name = name[len(prefix):]

            if suffix and name.endswith(suffix):
                name = name[:-len(suffix)]

            name = name.replace("_", " ")
            name = name[:1].upper() + name[1:]

            group_files.append(
                {
                    "name": name.strip(),
                    "path": relative_path,
                }
            )

            processed_files.add(file_path)

        if group_files:
            file_groups[group_name] = sorted(
                group_files,
                key=lambda item: item["name"],
            )

    # ---------------------------------------------------------
    # 3. Anything that didn't match a pattern goes into
    #    "Other Reports".
    # ---------------------------------------------------------
    misc_files = []

    for file_path in html_files:
        if file_path in processed_files:
            continue

        relative_path = os.path.relpath(file_path, root_dir)

        misc_files.append(
            {
                "name": (
                    os.path.basename(file_path)
                    .removesuffix(".html")
                    .replace("_", " ")
                ),
                "path": relative_path,
            }
        )

    if misc_files:
        file_groups["Other Reports"] = sorted(
            misc_files,
            key=lambda item: item["name"],
        )

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
            if attr_name == "CLF_config":
                # Flatten CLF_config dictionary with prefixed keys
                for key, value in attr_value.items():
                    prefixed_key = f"CLF_config.{key}"
                    dict_attrs[prefixed_key] = prefixed_key
                    dictionary_data[prefixed_key] = value
            else:
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

    if os.path.exists(filename) and os.path.exists(data_file):
        try:
            # Load existing sections
            with open(data_file, "r", encoding="utf-8") as f:
                sections = json.load(f)

            # Check if section with same title already exists
            existing_titles = [s.get("title") for s in sections]
            if title in existing_titles:
                # Update existing section
                for i, section in enumerate(sections):
                    if section.get("title") == title:
                        sections[i] = new_section
                        break
            else:
                # Append new section
                sections.append(new_section)

        except (json.JSONDecodeError, FileNotFoundError):
            # Start fresh if data file is corrupted
            sections = [new_section]
    else:
        # Start fresh
        sections = [new_section]

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
    index_dir="index.html",
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
        index_dir: Path or filename used for the gallery index link.

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
        "index_dir": index_dir,
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
