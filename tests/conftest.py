"""Configs for pytests"""

from types import SimpleNamespace


import pytest
from flask import Flask

from analysisweb.sequencer import Sequencer
from analysisweb.routes import register_routes


@pytest.fixture
def app(tmp_path):
    """Create a Flask application configured for testing."""
    flask_app = Flask(
        __name__,
        template_folder=str(tmp_path / "templates"),
    )

    results_dir = tmp_path / "results"
    json_dir = tmp_path / "json"

    results_dir.mkdir()
    json_dir.mkdir()

    flask_app.config.update(
        TESTING=True,
        JSON_DIR=json_dir,
        RESULTS_DIR=results_dir,
        DASHBOARD_CONFIG={"test": True},
    )

    flask_app.job_backend = SimpleNamespace()

    # Minimal templates required by the routes.
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir(exist_ok=True)

    (templates_dir / "index.html").write_text(
        "<html><body>Dashboard {{ config.test }}</body></html>",
        encoding="utf-8",
    )

    (templates_dir / "action_modal.html").write_text(
        "<html><body>Action Modal</body></html>",
        encoding="utf-8",
    )

    register_routes(flask_app)

    return flask_app


@pytest.fixture
def client(app): # pylint: disable=redefined-outer-name
    """Return a Flask test client."""
    return app.test_client()


@pytest.fixture
def sequencer(tmp_path):
    """Create an isolated Sequencer using pytest's temporary directory."""
    json_dir = tmp_path / "json"
    plots_dir = tmp_path / "plots"

    return Sequencer(
        json_dir=str(json_dir),
        plots_dir=str(plots_dir),
    )
