"""Module for generating HTML reports and managing analysis sequences."""

import os
import glob
from pathlib import Path
from datetime import datetime

import json
import warnings
import logging
from jinja2 import Environment, FileSystemLoader

from .logging_config import setup_logging
from . import Status

setup_logging()
logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore")

now = datetime.now()
formatted_time = now.strftime("%Y%m%d_%H_%M_%S")

current_dir = os.getcwd()

# 3. Join the safe, formatted string
_DEFAULT_SAVE_DIR = os.path.join(current_dir, formatted_time)
repo_dir = os.path.dirname(os.path.abspath(__file__))


def create_results_index(
    directory=_DEFAULT_SAVE_DIR,
    output_file="index.html",
    title="ML Analysis Results Index",
):  # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    """Creates an HTML index page linking to all result files using Jinja2 template."""

    # Setup Jinja2 environment

    root_dir = os.path.dirname(output_file)
    env = Environment(loader=FileSystemLoader(f"{repo_dir}/templates"))

    top_folders = glob.glob(os.path.join(directory, "*/"))
    folders = set(top_folders)  # These paths end with os.sep
    folders.add(directory)
    html_files = set()
    processed_files = set()  # Track files we've already added

    # For each folder, check if it has an index.html
    for folder in folders:
        index_path = os.path.join(folder, "index.html")

        if os.path.exists(index_path) and (index_path != output_file):
            if index_path not in processed_files:
                html_files.add(index_path)
                processed_files.add(index_path)
        else:
            folder_files = glob.glob(os.path.join(folder, "*.html"))
            for file_path in folder_files:
                if file_path not in processed_files:
                    html_files.add(file_path)
                    processed_files.add(file_path)

    list(html_files)
    html_files = sorted(list(html_files))

    # Separate files into categories
    nll_groups = {}
    density_ratios = {}
    misc_files = {}
    index_files = {}

    for file_path in html_files:
        file_name = os.path.basename(file_path)
        relative_path = os.path.relpath(file_path, root_dir)
        logger.debug("Relative Path : %s", relative_path)
        logger.debug("Root Path : %s", root_dir)
        if "NLLs_" in file_name:
            # Extract the base name (without test/holdout and extension)
            base_name = (
                file_name.replace("NLLs_", "")
                .replace("_holdout_", "")
                .replace("_test_", "")
                .replace(".html", "")
            )

            if base_name not in nll_groups:
                nll_groups[base_name] = {}

            if "holdout" in file_name:
                nll_groups[base_name]["holdout"] = relative_path
            elif "test" in file_name:
                nll_groups[base_name]["test"] = relative_path

        elif file_name.endswith("_density_ratios.html"):
            logger.debug("File Name : %s", file_name)
            density_ratios[file_name] = relative_path

        elif file_name.endswith("index.html"):
            parent_folder = os.path.basename(os.path.dirname(relative_path))
            base_name = file_name.replace("index.html", parent_folder)
            logger.debug("Base Name : %s", base_name)
            index_files[base_name] = relative_path
        else:

            base_name = file_name.replace("_", " ").replace(".html", "")
            logger.debug("Base Name : %s", base_name)
            misc_files[base_name] = relative_path

    # Prepare data for template
    template_data = {
        "title": title,
        "html_files": html_files,
        "file_groups": {
            "nll_groups": nll_groups,
            "density_ratios": density_ratios,
            "index_files": index_files,
            "misc_files": misc_files,
        },
        "output_file_stem": Path(output_file).stem,
    }

    # Load and render template
    template = env.get_template("index_template.html")
    html_content = template.render(**template_data)

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("Index created: %s", output_file)
    logger.info("Total files indexed: %s", len(html_files))
    logger.info("NLL groups: %s", len(nll_groups))
    logger.info("Density ratio files: %s", len(density_ratios))
    logger.info("Index files: %s", len(index_files))
    logger.info("Miscellaneous files: %s", len(misc_files))

    return Status.SUCCESS


def config_to_html(config, filename="config_report.html"):
    """Creates an HTML report of the configuration object with compact layout."""

    # Create Jinja2 environment
    env = Environment(loader=FileSystemLoader(f"{repo_dir}/templates"))

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

    return Status.SUCCESS


def text_report_to_html(text, title="Report", filename="text_report.html"):
    """Creates an HTML report with a text block using Jinja2.

    Args:
        text: The text content to include in the report
        title: The title of the report
        filename: The output HTML filename
    """

    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(f"{repo_dir}/templates"))

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
    env = Environment(loader=FileSystemLoader(f"{repo_dir}/templates"))

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
    env = Environment(loader=FileSystemLoader(f"{repo_dir}/templates"))

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
    file_paths,
    titles=None,
    output_file="image_gallery.html",
    file_title="Image Gallery",
    dictionary_data=None,
    index_dir="index.html",
):  # pylint: disable=too-many-arguments,too-many-positional-arguments
    """
    Create an HTML page with multiple base64 images in a gallery layout using Jinja2.

    Args:
        images_data: List of base64 encoded image strings OR BytesIO objects
        titles: List of titles for each image (optional)
        output_file: Output HTML filename
        file_title: Page title
    """

    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(f"{repo_dir}/templates"))

    # Prepare image list
    if titles is None:
        titles = [f"Image {i+1}" for i in range(len(file_paths))]

    images = []
    for i, (file_path, title) in enumerate(zip(file_paths, titles)):
        images.append({"file_path": file_path, "title": title, "index": i + 1})

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
