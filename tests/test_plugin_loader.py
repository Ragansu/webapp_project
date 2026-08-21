import sys
from pathlib import Path
import pytest
from analysisweb.plugin_loader import load_job_plugin


# ==============================================================================
# Tests for load_job_plugin
# ==============================================================================

def test_load_job_plugin_success(tmp_path, cleanup_plugin_imports):
    """Verify load_job_plugin dynamically loads a valid Python file as a module."""

    # Create a temporary plugin file
    plugin_file = tmp_path / "my_plugin.py"
    plugin_file.write_text(
        'PLUGIN_NAME = "CustomJob"\ndef run():\n    return "Job Executed"\n',
        encoding="utf-8",
    )

    module = load_job_plugin(plugin_file)

    # 1. Assert module attributes
    assert hasattr(module, "PLUGIN_NAME")
    assert module.PLUGIN_NAME == "CustomJob"
    assert hasattr(module, "run")
    assert module.run() == "Job Executed"

    # 2. Assert parent directory was added to sys.path
    assert str(tmp_path.resolve()) == sys.path[0]


def test_load_job_plugin_file_not_found(tmp_path, cleanup_plugin_imports):
    """Verify loading a non-existent plugin path raises FileNotFoundError / AttributeError on exec."""

    non_existent_file = tmp_path / "missing_plugin.py"

    with pytest.raises((FileNotFoundError, AttributeError)):
        load_job_plugin(non_existent_file)


def test_load_job_plugin_accepts_string_path(tmp_path, cleanup_plugin_imports):
    """Verify the function accepts string paths in addition to Path objects."""

    plugin_file = tmp_path / "str_plugin.py"
    plugin_file.write_text('STATUS = "active"\n', encoding="utf-8")

    # Pass as a raw string
    module = load_job_plugin(str(plugin_file))

    assert module.STATUS == "active"