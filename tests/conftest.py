"""Configs for pytests"""
import sys
from types import SimpleNamespace

import pytest
from unittest.mock import MagicMock, patch
from flask import Flask

from analysisweb.sequencer import Sequencer
from analysisweb.routes import register_routes

@pytest.fixture
def mock_cli_deps():
    """Mocks external dependencies for the main CLI entry point."""
    with patch("analysisweb.cli.create_app") as mock_create_app, \
         patch("analysisweb.cli.threading.Timer") as mock_timer, \
         patch("analysisweb.cli.webbrowser.open") as mock_browser_open:

        # Mock app instance returned by create_app
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        # Mock Timer object returned when instantiated
        mock_timer_inst = MagicMock()
        mock_timer.return_value = mock_timer_inst

        yield {
            "create_app": mock_create_app,
            "app": mock_app,
            "timer": mock_timer,
            "timer_inst": mock_timer_inst,
            "browser_open": mock_browser_open,
        }

@pytest.fixture
def mock_template_env():
    """Fixture to mock Jinja2 environment and template rendering."""
    with patch("analysisweb.reports._get_template_environment") as mock_get_env:
        mock_env = MagicMock()
        mock_template = MagicMock()

        # Mock template render output
        mock_template.render.return_value = "<html><body>Mocked Index</body></html>"
        mock_env.get_template.return_value = mock_template
        mock_get_env.return_value = mock_env

        yield mock_get_env, mock_template


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
def client(app):  # pylint: disable=redefined-outer-name
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

@pytest.fixture
def cleanup_plugin_imports():
    """Fixture to ensure dynamic imports and sys.path modifications are cleaned up."""
    original_path = list(sys.path)
    yield
    # Restore original sys.path
    sys.path[:] = original_path
    # Remove dynamically loaded plugin from sys.modules if present
    sys.modules.pop("job_plugin", None)