import json
import os
import signal
import subprocess
from analysisweb.sequencer import Sequencer


current_dir = os.path.dirname(os.path.abspath(__file__))
json_dir = os.path.join(current_dir, "json")


def submit_job(data, unique_date):
    """Submits a job via sbatch and initializes a Sequencer entry."""

    print("data received for job submission:", data)

    print("Unique date for job submission:", unique_date)
    print("json_dir:", json_dir)

    selected_flags = data.get("job_flags", [])

    # Construct the command
    command = (
        f'python "{current_dir}/run_script.py" --unique-date {unique_date} '
        f'> "{current_dir}/log_{unique_date}.log" '
        f'2>&1'
    )

    print(f"Selected flags: {selected_flags}")

    for flag in selected_flags:
        command += f" --{flag['key']} {flag['value']}"

    print(command)

    process = subprocess.Popen(
        command,
        shell=True,
    )

    print(f"Started process: {process.pid}")

    initial_entry = {
        "date": unique_date,
        "pid" : process.pid,
        "dataset": "California Housing",
        "model": "Linear Regression",
        "samples": 500,
        "run_time": 0,
        "rmse": "-",
        "status": "Launched",
        "link": "/",
    }

    _ = Sequencer(initial_entry=initial_entry, json_dir=json_dir)

    return f"Started process: {process.pid}"


def cancel_job(data):
    pid = data.get("pid")
    unique_date = data.get("date")

    entry_file = os.path.join(json_dir, f"{unique_date}.json")

    # os.kill(pid, signal.SIGKILL)
    print(f"Updating job status to 'Cancelled' in file:{pid}  {entry_file}")

    with open(entry_file, "r") as f:
        data = json.load(f)

    data["Status"] = "Cancelled"

    with open(entry_file, "w") as f:
        json.dump(data, f, indent=4)

    return "TEST"
