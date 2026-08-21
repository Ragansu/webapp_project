import sys
import pytest
from unittest.mock import ANY
from analysisweb.cli import (
    main,
)  # Adjust import if main is in a different file (e.g., analysisweb.main)

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
