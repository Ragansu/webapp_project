from pathlib import Path

from flask import Flask
import yaml

from .routes import register_routes
from .plugin_loader import load_job_plugin


PACKAGE_DIR = Path(__file__).parent



def load_config(filename):

    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {filename}"
        )

    with open(path) as f:
        return yaml.safe_load(f)

def create_app(
    results_dir,
    json_dir,
    config_file=None,
):
    app = Flask(
        __name__,
        template_folder=str(PACKAGE_DIR / "templates"),
        static_folder=str(PACKAGE_DIR / "static"),
    )

    app.config["RESULTS_DIR"] = Path(results_dir)
    app.config["JSON_DIR"] = Path(json_dir)


    if config_file:
        app.config["DASHBOARD_CONFIG"] = load_config(
            config_file
        )
    else:
        app.config["DASHBOARD_CONFIG"] = {}


    backend_path = (
        app.config["DASHBOARD_CONFIG"]
        ["jobs"]
        ["backend"]
    )

    app.job_backend = load_job_plugin(backend_path)

    register_routes(app)

    return app