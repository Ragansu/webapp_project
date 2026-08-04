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

        json_dir = current_app.config["JSON_DIR"].resolve()

        print("JSON_DIR:", json_dir)
        print("Filename:", filename)
        print("Looking for:", json_dir / filename)
        print("Exists:", (json_dir / filename).exists())

        file_path = json_dir / filename

        if not file_path.exists():
            print("File does not exist:", file_path)
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

        print("RESULTS_DIR:", result_dir)
        print("Folder:", folder)
        print("Exists:", (result_dir / folder).exists())

        if not full_folder_path.is_dir():
            abort(404)

        return safe_send(
            full_folder_path,
            filename,
    )
    
