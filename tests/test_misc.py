"""Tests for the application's CLI, configuration loading, and setup."""

import sys
from unittest.mock import ANY

import yaml
import pytest

from analysisweb.app import create_app, load_config
from analysisweb.cli import main

# ==============================================================================
# Tests for CLI entry point main()
# ==============================================================================


def test_main_default_arguments(mock_cli_deps, monkeypatch):
    """Verify main parses required args and uses default port/debug values."""
    test_args = [
        "cli.py",
        "--results-dir",
        "/path/to/results",
        "--json-dir",
        "/path/to/json",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    main()

    # 1. Verify Flask app initialization with defaults
    mock_cli_deps["create_app"].assert_called_once_with(
        "/path/to/results",
        "/path/to/json",
        None,  # default config
    )

    # 2. Verify Timer scheduled the browser launch
    mock_cli_deps["timer"].assert_called_once_with(1.0, ANY)
    mock_cli_deps["timer_inst"].start.assert_called_once()

    # Execute the timer's lambda callback directly to verify browser call
    timer_callback = mock_cli_deps["timer"].call_args[0][1]
    timer_callback()
    mock_cli_deps["browser_open"].assert_called_once_with("http://127.0.0.1:5088")

    # 3. Verify app run called with default port and debug=False
    mock_cli_deps["app"].run.assert_called_once_with(
        host="127.0.0.1",
        port=5088,
        debug=False,
    )


def test_main_custom_arguments(mock_cli_deps, monkeypatch):
    """Verify main handles custom config, port, and debug flags."""
    test_args = [
        "cli.py",
        "--results-dir",
        "/custom/results",
        "--json-dir",
        "/custom/json",
        "--config",
        "/path/to/config.yaml",
        "--port",
        "8080",
        "--debug",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    main()

    # 1. Verify custom config passed to create_app
    mock_cli_deps["create_app"].assert_called_once_with(
        "/custom/results",
        "/custom/json",
        "/path/to/config.yaml",
    )

    # 2. Verify app run called with custom port and debug=True
    mock_cli_deps["app"].run.assert_called_once_with(
        host="127.0.0.1",
        port=8080,
        debug=True,
    )


def test_main_missing_required_arguments(monkeypatch):
    """Verify CLI exits with SystemExit when required arguments are missing."""
    test_args = ["cli.py"]
    monkeypatch.setattr(sys, "argv", test_args)

    with pytest.raises(SystemExit):
        main()


def test_load_config(tmp_path):
    """Verify a YAML configuration file is loaded correctly."""
    config_file = tmp_path / "config.yaml"
    config = {
        "action": [
            {
                "job_plugin": "my_package.jobs.example",
            }
        ]
    }

    config_file.write_text(yaml.safe_dump(config), encoding="utf-8")

    result = load_config(config_file)

    assert result == config


def test_load_config_file_not_found(tmp_path):
    """Verify loading a missing configuration file raises FileNotFoundError."""
    config_file = tmp_path / "missing.yaml"

    with pytest.raises(
        FileNotFoundError,
        match=r"Config file not found: .*missing\.yaml",
    ):
        load_config(config_file)


def test_create_app_without_config(tmp_path, monkeypatch):
    """Verify the app uses empty dashboard settings without a config file."""
    register_routes_called = False

    def fake_register_routes(app): # pylint: disable=unused-argument
        nonlocal register_routes_called
        register_routes_called = True

    monkeypatch.setattr(
        "analysisweb.app.register_routes",
        fake_register_routes,
    )

    results_dir = tmp_path / "results"
    json_dir = tmp_path / "json"

    app = create_app(results_dir, json_dir)

    assert app.config["RESULTS_DIR"] == results_dir
    assert app.config["JSON_DIR"] == json_dir
    assert app.config["DASHBOARD_CONFIG"] == {}
    assert not hasattr(app, "job_backend")
    assert register_routes_called


def test_create_app_with_action_config(tmp_path, monkeypatch):
    """Verify the configured job plugin is loaded when creating the app."""
    config_file = tmp_path / "config.yaml"
    config = {
        "action": [
            {
                "job_plugin": "my_package.jobs.example",
            }
        ]
    }

    config_file.write_text(yaml.safe_dump(config), encoding="utf-8")

    expected_backend = object()
    loaded_plugin_path = None
    register_routes_called = False

    def fake_load_job_plugin(path):
        nonlocal loaded_plugin_path
        loaded_plugin_path = path
        return expected_backend

    def fake_register_routes(app):# pylint: disable=unused-argument
        nonlocal register_routes_called
        register_routes_called = True

    monkeypatch.setattr(
        "analysisweb.app.load_job_plugin",
        fake_load_job_plugin,
    )
    monkeypatch.setattr(
        "analysisweb.app.register_routes",
        fake_register_routes,
    )

    results_dir = tmp_path / "results"
    json_dir = tmp_path / "json"

    app = create_app(
        results_dir,
        json_dir,
        config_file,
    )

    assert app.config["RESULTS_DIR"] == results_dir
    assert app.config["JSON_DIR"] == json_dir
    assert app.config["DASHBOARD_CONFIG"] == config
    assert app.job_backend is expected_backend
    assert loaded_plugin_path == "my_package.jobs.example"
    assert register_routes_called
