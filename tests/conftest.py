import pytest

from analysisweb.sequencer import Sequencer


@pytest.fixture
def sequencer(tmp_path):
    """Create an isolated Sequencer using pytest's temporary directory."""
    json_dir = tmp_path / "json"
    plots_dir = tmp_path / "plots"

    return Sequencer(
        json_dir=str(json_dir),
        plots_dir=str(plots_dir),
    )