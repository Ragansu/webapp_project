from pathlib import Path

from flask import (
    current_app,
    abort,
    render_template,
    send_from_directory,
)


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


    @app.route("/json/<path:filename>")
    def json_files(filename):

        if not filename.endswith(".json"):
            abort(404)

        return safe_send(
            current_app.config["JSON_DIR"],
            filename,
        )


    @app.route("/result/<folder>/")
    def result_index(folder):

        if not folder.startswith("result_"):
            abort(404)

        result_dir = (
            current_app.config["RESULTS_DIR"]
            / folder
        )

        return safe_send(
            result_dir,
            "index.html",
        )


    @app.route("/result/<folder>/<path:filename>")
    def result_files(folder, filename):

        if not folder.startswith("result_"):
            abort(404)

        result_dir = (
            current_app.config["RESULTS_DIR"]
            / folder
        )

        return safe_send(
            result_dir,
            filename,
        )