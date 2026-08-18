"""Route definitions for the analysis web application."""

import logging
import subprocess
from datetime import datetime
from pathlib import Path

from flask import (
    abort,
    current_app,
    jsonify,
    render_template,
    request,
    send_from_directory,
)

from .logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def safe_send(directory: Path, filename: str):
    """Safely send a file from a directory without allowing path traversal."""

    directory = directory.resolve()
    requested = (directory / filename).resolve()

    # prevent ../ escapes
    if directory not in requested.parents:
        abort(403)

    if not requested.exists():
        abort(404)

    return send_from_directory(
        directory,
        filename,
    )


def register_routes(app):
    """Register all application routes on the provided Flask app."""

    @app.route("/")
    def home():
        """Render the main dashboard page."""

        return render_template(
            "index.html",
            config=current_app.config["DASHBOARD_CONFIG"],
        )

    @app.route("/action-modal")
    def action_modal():
        """Render the action modal template."""
        return render_template("action_modal.html")

    @app.route("/json/<path:filename>")
    def json_files(filename):
        """Serve a JSON file from the configured JSON directory."""

        json_dir = current_app.config["JSON_DIR"].resolve()
        file_path = json_dir / filename
        exists = file_path.exists()

        if app.debug:
            logger.verbose("JSON_DIR: %s", json_dir)
            logger.verbose("Filename: %s", filename)
            logger.verbose("Looking for: %s", file_path)
            logger.verbose("Exists: %s", exists)

        if not file_path.exists():
            logger.error("File does not exist: %s", file_path)
            abort(404)

        return send_from_directory(
            json_dir,
            filename,
        )

    @app.route("/<folder>/<path:filename>")
    def result_files(folder, filename):
        """Serve a file from a result folder after validating the path."""

        if not folder.startswith("result_"):
            abort(404)

        result_dir = current_app.config["RESULTS_DIR"].resolve()
        full_folder_path = result_dir / folder
        exists = full_folder_path.exists()

        if app.debug:
            logger.verbose("RESULTS_DIR: %s", result_dir)
            logger.verbose("Folder: %s", folder)
            logger.verbose("Exists: %s", exists)

        if not full_folder_path.is_dir():
            abort(404)

        return safe_send(
            full_folder_path,
            filename,
        )

    @app.route("/send_sbatch_job", methods=["POST"])
    def send_sbatch_job():
        """Submit a Slurm batch job using the configured backend."""
        data = request.get_json()
        now = datetime.now()
        date_str = now.strftime("%Y%m%d_%H_%M_%S")

        try:
            result = current_app.job_backend.submit_job(data, date_str)

            return jsonify({"status": "success", "output": result})
        except subprocess.CalledProcessError as exc:
            return jsonify({"status": "error", "output": exc.stderr}), 500

    @app.route("/cancel_sbatch_job", methods=["POST"])
    def cancel_sbatch_job():
        """Cancel a submitted Slurm batch job."""
        data = request.get_json()

        try:
            result = current_app.job_backend.cancel_job(data)

            return jsonify(
                {
                    "status": "success",
                    "output": result,
                }
            )

        except subprocess.CalledProcessError as exc:
            return jsonify({"status": "error", "output": exc.stderr.strip()}), 500
