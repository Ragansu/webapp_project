"""Tests for the Sequencer workflow"""

# pylint: disable=protected-access

import json
import os

import pytest

from analysisweb import Status
from analysisweb.sequencer import Sequencer

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def successful_step():
    """Helper function that returns a successful step result."""
    return {"Status": Status.SUCCESS}


def another_successful_step():
    """Another helper function that returns a successful step result."""
    return {"Status": Status.SUCCESS}


# ---------------------------------------------------------------------------
# Initialization / persistence
# ---------------------------------------------------------------------------


def test_sequencer_creates_directories_and_files(tmp_path):
    """Test that Sequencer creates required directories and files."""
    json_dir = tmp_path / "json"
    plots_dir = tmp_path / "plots"

    sequencer = Sequencer(
        json_dir=str(json_dir),
        plots_dir=str(plots_dir),
    )

    assert json_dir.exists()
    assert json_dir.is_dir()

    assert sequencer.entry_file
    assert os.path.exists(sequencer.entry_file)

    assert os.path.exists(sequencer.index_file)


def test_initial_entry_is_persisted(tmp_path):
    """Test that initial entry is persisted to file."""
    json_dir = tmp_path / "json"

    initial_entry = {
        "date": "20260819_10_00_00",
        "run_time": 0,
        "Status": "Launched",
        "link": "/",
        "experiment": "test-run",
    }

    Sequencer(
        json_dir=str(json_dir),
        initial_entry=initial_entry,
    )

    entry_file = json_dir / "20260819_10_00_00.json"

    assert entry_file.exists()

    with entry_file.open(encoding="utf-8") as f:
        data = json.load(f)

    assert data == initial_entry


def test_existing_entry_is_loaded(tmp_path):
    """Test that existing entry is loaded from file."""
    json_dir = tmp_path / "json"
    json_dir.mkdir()

    entry = {
        "date": "20260819_10_00_00",
        "run_time": 123,
        "Status": "Running",
        "link": "/",
        "experiment": "existing",
    }

    entry_file = json_dir / "20260819_10_00_00.json"

    with entry_file.open("w", encoding="utf-8") as f:
        json.dump(entry, f)

    sequencer = Sequencer(
        json_dir=str(json_dir),
        initial_entry=entry,
    )

    entry["Status"] = "Launched"

    assert sequencer._entry_dict == entry

    entry_file.write_text(
        '{"date": "20260819_10_00_00", "run_time": 123',
        encoding="utf-8",
    )

    sequencer.entry_file = entry_file

    with pytest.raises(json.JSONDecodeError):
        sequencer._read_entry()


# ---------------------------------------------------------------------------
# create_substep
# ---------------------------------------------------------------------------


def test_create_substep_uses_function_name():
    """Test that create_substep uses function name as step name."""

    def my_algorithm():
        pass

    step = Sequencer.create_substep(my_algorithm)

    assert (
        step["name"] == "test_create_substep_uses_function_name.<locals>.my_algorithm"
    )

    assert isinstance(step["args"], tuple)
    assert isinstance(step["kwargs"], dict)

    assert step["func"] is my_algorithm
    assert not step["args"]
    assert not step["kwargs"]
    assert step["aux"] is False


def test_create_substep_uses_custom_name():
    """Test that create_substep accepts custom name."""

    def my_algorithm():
        pass

    step = Sequencer.create_substep(
        my_algorithm,
        name="My Algorithm",
    )

    assert step["name"] == "My Algorithm"


def test_create_substep_preserves_args_and_kwargs():
    """Test that create_substep preserves function arguments and keyword arguments."""

    def my_algorithm(a, b, option=None):
        _ = a + b + len(option)

    step = Sequencer.create_substep(
        my_algorithm,
        10,
        20,
        option="hello",
    )

    assert step["func"] is my_algorithm
    assert step["args"] == (10, 20)
    assert step["kwargs"] == {"option": "hello"}


def test_create_substep_handles_data_label():
    """Test that create_substep handles data_label parameter."""

    def my_algorithm(data):
        _ = data

    step = Sequencer.create_substep(
        my_algorithm,
        "dataset",
        data_label="training",
    )

    assert step["name"] == (
        "test_create_substep_handles_data_label.<locals>.my_algorithm" "(training)"
    )


def test_create_substep_can_be_auxiliary():
    """Test that create_substep can mark steps as auxiliary."""

    def my_algorithm():
        pass

    step = Sequencer.create_substep(
        my_algorithm,
        aux=True,
    )

    assert step["aux"] is True


# ---------------------------------------------------------------------------
# Adding algorithms / subsequences
# ---------------------------------------------------------------------------


def test_add_algorithm_adds_step(sequencer):
    """Test that add_algorithm adds step to sequencer."""
    sequencer.add_algorithm(successful_step)

    assert len(sequencer.steps) == 1
    assert sequencer.steps[0]["func"] is successful_step


def test_add_algorithm_preserves_arguments(sequencer):
    """Test that add_algorithm preserves function arguments."""
    received = {}

    def algorithm(value, multiplier=1):
        received["value"] = value
        received["multiplier"] = multiplier
        return {"Status": Status.SUCCESS}

    sequencer.add_algorithm(
        algorithm,
        10,
        multiplier=5,
    )

    sequencer.run()

    assert received == {
        "value": 10,
        "multiplier": 5,
    }


def test_add_algorithm_with_name(sequencer):
    """Test that add_algorithm accepts custom name."""
    sequencer.add_algorithm(
        successful_step,
        name="Important Analysis",
    )

    assert sequencer.steps[0]["name"] == "Important Analysis"


def test_add_subsequence(sequencer):
    """Test that add_subsequence adds multiple substeps."""

    def build_subsequence():
        return [
            Sequencer.create_substep(
                successful_step,
                name="Step A",
            ),
            Sequencer.create_substep(
                another_successful_step,
                name="Step B",
            ),
        ]

    sequencer.add_subsequence(build_subsequence)

    assert len(sequencer.steps) == 2
    assert sequencer.steps[0]["name"] == "Step A"
    assert sequencer.steps[1]["name"] == "Step B"


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def test_run_executes_steps_in_order(sequencer):
    """Test that run executes steps in correct order."""
    executed = []

    def step_a():
        executed.append("a")
        return {"Status": Status.SUCCESS}

    def step_b():
        executed.append("b")
        return {"Status": Status.SUCCESS}

    def step_c():
        executed.append("c")
        return {"Status": Status.SUCCESS}

    sequencer.add_algorithm(step_a)
    sequencer.add_algorithm(step_b)
    sequencer.add_algorithm(step_c)

    sequencer.run()

    assert executed == ["a", "b", "c"]


def test_run_executes_all_steps(sequencer):
    """Test that run executes all added steps."""
    counter = {"value": 0}

    def step():
        counter["value"] += 1
        return {"Status": Status.SUCCESS}

    for _ in range(5):
        sequencer.add_algorithm(step)

    sequencer.run()

    assert counter["value"] == 5


def test_run_passes_step_arguments(sequencer):
    """Test that run passes arguments to step functions."""
    result = {}

    def algorithm(a, b, multiplier=1):
        result["value"] = (a + b) * multiplier
        return {"Status": Status.SUCCESS}

    sequencer.add_algorithm(
        algorithm,
        2,
        3,
        multiplier=10,
    )

    sequencer.run()

    assert result["value"] == 50


# ---------------------------------------------------------------------------
# Failure handling
# ---------------------------------------------------------------------------


def test_failed_step_raises_exception(sequencer):
    """Test that failed step raises exception."""

    def broken_algorithm():
        raise RuntimeError("boom")

    sequencer.add_algorithm(broken_algorithm)

    with pytest.raises(RuntimeError, match="boom"):
        sequencer.run()


def test_failed_step_updates_status(sequencer):
    """Test that failed step updates status in entry."""

    def broken_algorithm():
        raise RuntimeError("boom")

    sequencer.add_algorithm(
        broken_algorithm,
        name="Broken Step",
    )

    with pytest.raises(RuntimeError, match="boom"):
        sequencer.run()

    entry = sequencer._entry_dict

    assert entry["Status"] == f"{Status.FAILED.value} | Broken Step"


def test_failure_stops_following_steps(sequencer):
    """Test that failure stops execution of following steps."""
    executed = []

    def first():
        executed.append("first")
        return {"Status": Status.SUCCESS}

    def broken():
        executed.append("broken")
        raise RuntimeError("boom")

    def third():
        executed.append("third")
        return {"Status": Status.SUCCESS}

    sequencer.add_algorithm(first)
    sequencer.add_algorithm(broken)
    sequencer.add_algorithm(third)

    with pytest.raises(RuntimeError, match="boom"):
        sequencer.run()

    assert executed == [
        "first",
        "broken",
    ]


# ---------------------------------------------------------------------------
# Status lifecycle
# ---------------------------------------------------------------------------


def test_start_sets_setting_up(sequencer):
    """Test that start() sets status to 'Setting Up'."""
    sequencer.start()

    entry = sequencer._entry_dict

    assert entry["Status"] == "Setting Up"


def test_start_initializes_start_time(sequencer):
    """Test that start() initializes start_time."""
    assert sequencer.start_time == 0

    sequencer.start()

    assert sequencer.start_time != 0


def test_run_sets_running_before_steps(sequencer):
    """Test that run() sets status to 'Running' before executing steps."""
    observed_statuses = []

    def step():
        observed_statuses.append(sequencer._entry_dict["Status"])
        return {"Status": Status.SUCCESS}

    sequencer.add_algorithm(step)
    sequencer.run()

    assert observed_statuses == ["Running"]


def test_end_sets_completed(sequencer):
    """Test that end() sets status to 'Completed'."""
    sequencer.end()

    entry = sequencer._entry_dict

    assert entry["Status"] == "Completed"


def test_cancel_sets_cancelled(sequencer):
    """Test that cancel() sets status to 'Cancelled'."""
    sequencer.cancel()

    entry = sequencer._entry_dict

    assert entry["Status"] == "Cancelled"


# ---------------------------------------------------------------------------
# Update / persistence
# ---------------------------------------------------------------------------


def test_update_persists_status(sequencer):
    """Test that update() persists status to file."""
    sequencer.update({"Status": "Running"})

    with open(sequencer.entry_file, encoding="utf-8") as f:
        entry = json.load(f)

    assert entry["Status"] == "Running"


def test_update_persists_free_keys(sequencer):
    """Test that update() persists free keys to file."""
    # "run_time" is part of free_keys because it is present in the
    # initial entry.
    sequencer.update({"run_time": 123})

    with open(sequencer.entry_file, encoding="utf-8") as f:
        entry = json.load(f)

    assert entry["run_time"] == 123


def test_update_does_not_add_unknown_keys(sequencer):
    """Test that update() does not persist unknown keys."""
    sequencer.update(
        {
            "Status": "Running",
            "something_unknown": "hello",
        }
    )

    entry = sequencer._entry_dict

    assert entry["Status"] == "Running"
    assert "something_unknown" not in entry


# ---------------------------------------------------------------------------
# Index handling
# ---------------------------------------------------------------------------


def test_index_contains_entry(sequencer):
    """Test that index file contains entry reference."""
    with open(sequencer.index_file, encoding="utf-8") as f:
        index = json.load(f)

    assert os.path.basename(sequencer.entry_file) in index


def test_index_does_not_duplicate_entry(tmp_path):
    """Test that index file does not duplicate entry references."""
    json_dir = tmp_path / "json"

    initial_entry = {
        "date": "20260819_10_00_00",
        "run_time": 0,
        "Status": "Launched",
        "link": "/",
    }

    Sequencer(
        json_dir=str(json_dir),
        initial_entry=initial_entry,
    )

    Sequencer(
        json_dir=str(json_dir),
        initial_entry=initial_entry,
    )

    with open(json_dir / "index.json", encoding="utf-8") as f:
        index = json.load(f)

    assert index.count("20260819_10_00_00.json") == 1


# ---------------------------------------------------------------------------
# Sequence printing
# ---------------------------------------------------------------------------


def test_print_sequence_contains_main_steps(sequencer):
    """Test that print_sequence includes main steps."""
    sequencer.add_algorithm(
        successful_step,
        name="Step A",
    )

    sequencer.add_algorithm(
        another_successful_step,
        name="Step B",
    )

    output = sequencer.print_sequence()

    assert "Step A" in output
    assert "Step B" in output


def test_print_sequence_excludes_auxiliary_steps(sequencer):
    """Test that print_sequence excludes auxiliary steps."""
    sequencer.add_algorithm(
        successful_step,
        name="Main Step",
    )

    sequencer.add_algorithm(
        another_successful_step,
        name="Auxiliary Step",
        aux=True,
    )

    output = sequencer.print_sequence()

    assert "Main Step" in output
    assert "Auxiliary Step" not in output


# ---------------------------------------------------------------------------
# Timing / CSV
# ---------------------------------------------------------------------------


def test_update_creates_time_record(sequencer):
    """Test that update() creates time record file."""
    sequencer.update({"Status": "Running"})

    assert os.path.exists(sequencer.timerecord)


def test_time_record_contains_header(sequencer):
    """Test that time record contains proper header."""
    sequencer.update({"Status": "Running"})

    with open(sequencer.timerecord, encoding="utf-8") as f:
        lines = f.readlines()

    assert lines[0].strip() == "status,time,duration"


def test_time_record_contains_status(sequencer):
    """Test that time record contains status information."""
    sequencer.update({"Status": "Running"})

    with open(sequencer.timerecord, encoding="utf-8") as f:
        contents = f.read()

    assert "Running" in contents


def test_update_records_multiple_status_changes(sequencer):
    """Test that time record contains multiple status changes."""
    sequencer.update({"Status": "Running"})
    sequencer.update({"Status": "Processing"})
    sequencer.update({"Status": "Completed"})

    with open(sequencer.timerecord, encoding="utf-8") as f:
        lines = f.readlines()

    # Header + 3 records
    assert len(lines) == 4

    assert "Running" in lines[1]
    assert "Processing" in lines[2]
    assert "Completed" in lines[3]


# ---------------------------------------------------------------------------
# Full lifecycle
# ---------------------------------------------------------------------------


def test_full_sequence_lifecycle(sequencer):
    """Test full lifecycle of sequencer from start to end."""
    executed = []

    def prepare():
        executed.append("prepare")
        return {"Status": Status.SUCCESS}

    def analyze():
        executed.append("analyze")
        return {"Status": Status.SUCCESS}

    def auxilary():
        executed.append("auxilary")

    def report():
        executed.append("report")
        return {"Status": Status.SUCCESS}

    sequencer.add_algorithm(
        prepare,
        name="Prepare",
    )

    sequencer.add_algorithm(
        analyze,
        name="Analyze",
    )

    sequencer.add_algorithm(
        auxilary,
        aux=True,
        name="auxilary",
    )

    sequencer.add_algorithm(
        report,
        name="Report",
    )

    sequencer.start()
    sequencer.run()
    sequencer.end()

    assert executed == [
        "prepare",
        "analyze",
        "auxilary",
        "report",
    ]

    assert sequencer._entry_dict["Status"] == "Completed"
