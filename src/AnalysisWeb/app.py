#!/usr/bin/python3

import os
from flask import Flask, send_from_directory, abort, request, jsonify
import argparse
from importlib.resources import files

# Define absolute paths to your directories
TEMPLATES_DIR = files("AnalysisWeb") / "templates"
STATIC_DIR = files("AnalysisWeb") / "static"

parser = argparse.ArgumentParser()
parser.add_argument(
    "--results-dir",
    default=os.getcwd(),
    help="Path to all the result pages",
)

parser.add_argument(
    "--csv-dir",
    default=STATIC_DIR,
    help="Path to all the result pages",
)

app = Flask(__name__)
args, _ = parser.parse_known_args()

RESULTS_DIR = args.results_dir
CSV_DIR = args.csv_dir

os.makedirs(RESULTS_DIR, exist_ok=True)


# Serve main HTML page
@app.route("/")
def home():
    """Links the home page or index page"""

    return send_from_directory(TEMPLATES_DIR, "index.html")


# Serve static files (CSS, JS, etc.)
@app.route("/static/<path:filename>")
def serve_static(filename):
    """Links the static folder"""
    return send_from_directory(STATIC_DIR, filename)


@app.route("/style.css")
def serve_css():
    """Links the style.css"""
    return send_from_directory(STATIC_DIR, "style.css")


# Serve CSV files directly from static
@app.route("/<filename>")
def serve_root_files(filename):
    """Links the csv tables for the index page"""
    if filename.endswith(".csv"):
        return send_from_directory(CSV_DIR, filename)
    abort(404)


# Serve result files from results/result_* folders
@app.route("/<folder>/<path:filename>")
def serve_result_direct(folder, filename):
    """Links the results folders for accesing the results"""
    if not folder.startswith("result_"):
        abort(404)

    folder_path = os.path.join(RESULTS_DIR, folder)
    file_path = os.path.join(folder_path, filename)

    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(folder_path, filename)


@app.route("/<folder>/")
def serve_result_index(folder):
    """Links folders starting with 'result_' in the results folder for accesing the results"""
    if not folder.startswith("result_"):
        abort(404)

    folder_path = os.path.join(RESULTS_DIR, folder)
    file_path = os.path.join(folder_path, "index.html")

    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(folder_path, "index.html")


@app.route("/debug-paths")
def debug_paths():
    """Debug endpoint to see where files are located"""
    import AnalysisWeb  # your actual package name
    from importlib.resources import files

    debug_info = {
        "current_working_directory": os.getcwd(),
        "script_directory": os.path.dirname(os.path.abspath(__file__)),
        "package_location": os.path.dirname(AnalysisWeb.__file__),
        "templates_path": str(files("AnalysisWeb") / "templates"),
        "static_path": str(files("AnalysisWeb") / "static"),
        "templates_exists": os.path.exists(str(files("AnalysisWeb") / "templates")),
        "static_exists": os.path.exists(str(files("AnalysisWeb") / "static")),
    }

    # List files in package directory
    try:
        package_files = os.listdir(os.path.dirname(AnalysisWeb.__file__))
        debug_info["package_files"] = package_files
    except Exception as e:
        debug_info["package_files_error"] = str(e)

    return jsonify(debug_info)


if __name__ == "__main__":
    app.run(debug=True)
