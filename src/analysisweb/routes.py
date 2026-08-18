from pathlib import Path
import subprocess

from flask import (
    current_app,
    abort,
    render_template,
    send_from_directory,
    request,
    jsonify,
)

from datetime import datetime
import logging
from .logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def safe_send(directory: Path, filename: str):

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

    @app.route("/")
    def home():

        return render_template(
            "index.html",
            config=current_app.config["DASHBOARD_CONFIG"],
        )

    @app.route("/action-modal")
    def action_modal():
        return render_template("action_modal.html")

    @app.route("/json/<path:filename>")
    def json_files(filename):

        json_dir = current_app.config["JSON_DIR"].resolve()
        file_path = json_dir / filename
        isExists = file_path.exists()

        if app.debug:
            logger.verbose(f"JSON_DIR: %s", json_dir)
            logger.verbose(f"Filename: %s", filename)
            logger.verbose(f"Looking for: {file_path}")
            logger.verbose(f"Exists: {isExists}")

        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            abort(404)

        return send_from_directory(
            json_dir,
            filename,
        )

    @app.route("/<folder>/<path:filename>")
    def result_files(folder, filename):

        if not folder.startswith("result_"):
            abort(404)

        result_dir = current_app.config["RESULTS_DIR"].resolve()
        full_folder_path = result_dir / folder
        isExists = full_folder_path.exists()

        if app.debug:
            logger.verbose(f"RESULTS_DIR: {result_dir}")
            logger.verbose(f"Folder: {folder}")
            logger.verbose(f"Exists: {isExists}")

        if not full_folder_path.is_dir():
            abort(404)

        return safe_send(
            full_folder_path,
            filename,
        )

    @app.route("/send_sbatch_job", methods=["POST"])
    def send_sbatch_job():
        data = request.get_json()
        now = datetime.now()
        date_str = now.strftime("%Y%m%d_%H_%M_%S")

        try:
            result = current_app.job_backend.submit_job(data, date_str)

            return jsonify({"status": "success", "output": result})
        except subprocess.CalledProcessError as e:
            return jsonify({"status": "error", "output": e.stderr}), 500

    @app.route("/cancel_sbatch_job", methods=["POST"])
    def cancel_sbatch_job():
        data = request.get_json()

        try:
            result = current_app.job_backend.cancel_job(data)

            return jsonify(
                {
                    "status": "success",
                    "output": result,
                }
            )

        except subprocess.CalledProcessError as e:
            return jsonify({"status": "error", "output": e.stderr.strip()}), 500
