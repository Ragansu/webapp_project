from pathlib import Path

from flask import Flask

from .routes import register_routes


PACKAGE_DIR = Path(__file__).parent


def create_app(results_dir, json_dir):

    app = Flask(
        __name__,
        template_folder=str(PACKAGE_DIR / "templates"),
        static_folder=str(PACKAGE_DIR / "static"),
    )

    app.config["RESULTS_DIR"] = Path(results_dir).resolve()
    app.config["JSON_DIR"] = Path(json_dir).resolve()

    app.config["RESULTS_DIR"].mkdir(
        parents=True,
        exist_ok=True,
    )

    app.config["JSON_DIR"].mkdir(
        parents=True,
        exist_ok=True,
    )

    register_routes(app)

    return app