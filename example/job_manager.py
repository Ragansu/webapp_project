"""Job manager module for submitting and managing computational jobs.

This module provides functionality to submit jobs using subprocess and track
their execution status via the Sequencer. It supports job cancellation and
status updates.
"""

import json
import os
import signal
import subprocess

import yaml
from analysisweb.sequencer import Sequencer


current_dir = os.path.dirname(os.path.abspath(__file__))
json_dir = os.path.join(current_dir, "json")


def get_initial_entry(path):
    """Loads initial entry data from YAML config file."""

    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    columns = config["columns"]
    initial_entry = {}
    for col in columns:
        if col["type"] != "action":
            initial_entry[col["key"]] = col["default"]

    return initial_entry


def submit_job(data, unique_date):
    """Submits a job with subprocess and initializes a Sequencer entry."""

    print("data received for job submission:", data)
    print("Unique date for job submission:", unique_date)
    print("json_dir:", json_dir)

    selected_flags = data.get("job_flags", [])

    # Construct the command
    command = f'python "{current_dir}/run_script.py" --unique-date {unique_date} '

    print(f"Selected flags: {selected_flags}")

    for flag in selected_flags:
        command += f" --{flag['key']} {flag['value']}"

    command += f' > "{current_dir}/logs/log_{unique_date}.log" 2>&1'

    print(command)

    process = subprocess.Popen(  # pylint: disable=consider-using-with
        command,
        shell=True,
    )

    print(f"Started process: {process.pid}")

    initial_entry = get_initial_entry(f"{current_dir}/example_dash.yaml")

    initial_entry["pid"] = process.pid
    initial_entry["date"] = unique_date

    _ = Sequencer(initial_entry=initial_entry, json_dir=json_dir)

    return f"Started process: {process.pid}"


def cancel_job(data):
    """cancels a submitted job submitted with subprocess"""
    pid = data.get("pid")
    unique_date = data.get("date")

    entry_file = os.path.join(json_dir, f"{unique_date}.json")

    try:

        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        print(f"No such process with pid {pid}")

    print(f"Updating job status to 'Cancelled' in file:{pid}  {entry_file}")

    with open(entry_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["Status"] = "Cancelled"

    with open(entry_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return f"Cancelled process: {pid}"
