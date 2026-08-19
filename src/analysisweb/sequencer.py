"""Utilities for tracking a multi-step analysis run and state updates in JSON/CSV.

This module defines a lightweight task sequencer that stores metadata for each run,
tracks the status of execution steps, and logs timing information for plots or
reports.
"""

import os
import csv
from datetime import datetime
import json

import logging

from .reports import create_results_index, text_report_to_html
from . import Status

logger = logging.getLogger(__name__)


class Sequencer:  # pylint: disable=too-many-instance-attributes,too-many-branches
    """Manage a sequence of analysis steps and persist run metadata.

    The sequencer stores a run entry as JSON, records timing information,
    and exposes helpers for creating, printing, and running a step list.
    """

    def __init__(self, json_dir, plots_dir=None, initial_entry=None):
        """Initialize a sequencer and create its backing files.

        Args:
            json_dir: Directory used to store run metadata JSON files.
            plots_dir: Optional directory for plots and time-record logging.
            initial_entry: Optional dictionary used as the initial run entry.
        """
        if initial_entry is None:
            now = datetime.now()
            initial_entry = {
                "date": now.strftime("%Y%m%d_%H_%M_%S"),
                "run_time": 0,
                "Status": "Launched",
                "link": "/",
            }

        self.free_keys = set(initial_entry.keys()) - {"date", "link"}

        os.makedirs(json_dir, exist_ok=True)
        if plots_dir is not None:
            os.makedirs(plots_dir, exist_ok=True)

        self.entry_file = os.path.join(json_dir, f"{initial_entry['date']}.json")
        self.index_file = os.path.join(json_dir, "index.json")

        self.__entry_dict__ = initial_entry

        self.steps = []

        self.start_time = 0
        self.last_time_stamp = datetime.now()

        # Load existing entry if it exists
        if os.path.exists(self.entry_file):
            self._read_entry()

        self.plots_dir = plots_dir
        # Plot handling (unchanged)
        if plots_dir is not None:
            self.__entry_dict__["link"] = os.path.basename(plots_dir) + "/index.html"
            self.output_html = os.path.join(plots_dir, "index.html")
            self.timerecord = os.path.join(plots_dir, "time_record.csv")
            self.fieldnames = ["status", "time", "duration"]

        self._write_entry()
        self._update_index()

    # ------------------------
    # Internal helpers
    # ------------------------

    def _read_entry(self):
        """Load an existing run entry from disk into the in-memory metadata dict."""
        try:
            with open(self.entry_file, "r", encoding="utf-8") as f:
                self.__entry_dict__ = json.load(f)
        except Exception as e:
            logger.error("Failed to read entry JSON: %s", e)
            raise e

    def _write_entry(self):
        """Persist the current run state to the JSON entry file."""
        try:
            with open(self.entry_file, "w", encoding="utf-8") as f:
                json.dump(self.__entry_dict__, f, indent=2)
        except Exception as e:
            logger.error("Failed to write entry JSON: %s", e)
            raise e

    def _update_index(self):
        """Add the current entry filename to the index and keep entries newest-first."""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, "r", encoding="utf-8") as f:
                    index = json.load(f)
            else:
                index = []

            filename = os.path.basename(self.entry_file)
            if filename not in index:
                index.append(filename)

            # newest first (by filename / date)
            index = sorted(index, reverse=True)

            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2)

        except Exception as e:
            logger.error("Failed to update index.json: %s", e)
            raise e

    # ------------------------
    # Public update hook
    # ------------------------

    def update(self, result={"Status": ""}):
        """Refresh the run record and append a time-stamp entry to the CSV log.

        Args:
            status: A status string describing the current execution state.
        """
        now = datetime.now()
        if self.start_time:
            self.__entry_dict__["run_time"] = (now - self.start_time).total_seconds()

        result_keys = set(result.keys())

        for key in result_keys & self.free_keys:
            self.__entry_dict__[key] = result[key]

        self._write_entry()

        # Regenerate HTML if needed
        if self.plots_dir is not None and os.path.exists(self.plots_dir):
            try:
                create_results_index(
                    self.plots_dir,
                    self.output_html,
                    title=os.path.basename(self.plots_dir),
                )
            except Exception as e:
                logger.error("Failed to regenerate HTML: %s", e)
                raise e

        # Append time record (unchanged CSV logging)
        try:

            duration = now - self.last_time_stamp

            # Convert timedelta to HH:MM:SS
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            record = {
                "status": self.__entry_dict__["Status"],
                "time": now.strftime("%H:%M:%S"),
                "duration": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            }

            self.last_time_stamp = now

            file_exists = os.path.exists(self.timerecord)
            with open(self.timerecord, "a", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(record)

        except Exception as e:
            logger.error("Failed to log time record: %s", e)
            raise e

    @staticmethod
    def create_substep(func, *args, name=None, aux=False, **kwargs):
        """Create a dict representing a single step in the execution sequence."""
        if "data_label" in kwargs:
            data_label = f"({kwargs['data_label']})"

        else:
            data_label = ""

        substep = {
            "name": name or func.__qualname__ + data_label,
            "aux": aux,
            "func": func,
            "args": args,
            "kwargs": kwargs,
        }
        return substep

    def run_step(self, step):
        """Execute a single step and update the run metadata with its final status."""
        func = step["func"]
        args = step["args"]
        kwargs = step["kwargs"]
        name = step["name"]
        result = {"Status": ""}

        try:
            result = func(*args, **kwargs)  # Assuming func returns a Status enum
            status = result["Status"].value + " | " + name

        except Exception as e:
            logger.error("Error during %s: %s", name, e)
            status = Status.FAILED.value + " | " + name

            raise e
        finally:
            result["Status"] = status
            self.update(result=result)

    def add_subsequence(self, func, *args, **kwargs):
        """Append a list of substeps returned by a factory function to the sequence."""
        subsequence = func(*args, **kwargs)
        self.steps.extend(subsequence)

    def add_algorithm(self, func, *args, name=None, aux=False, **kwargs):
        """Append a single algorithm step, optionally marked as auxiliary."""
        self.steps.append(
            self.create_substep(func, *args, name=name, aux=aux, **kwargs)
        )

    def print_sequence(self):
        """Print and return a formatted summary of the queued execution sequence."""
        width = 85
        title = "Sequence to be executed"
        header = [
            "┌" + "─" * (width) + "┐",
            f"│{title.center(width)}│",
            "│" + "─" * width + "│",
        ]

        main_steps = [step for step in (self.steps) if not step["aux"]]

        steps = [
            f"│ Step - {i:3} {step['name']}".ljust(width) + " │"
            for i, step in enumerate(main_steps)
        ]

        footer = ["└" + "─" * width + "┘\n"]

        sequence_str = "\n".join(header + steps + footer)

        print(sequence_str)

        text_report_to_html(
            text=sequence_str,
            filename=os.path.join(self.plots_dir, "sequence_report.html"),
            title="Execution Sequence",
        )

        return sequence_str

    def run(self):
        """Execute all queued steps in order and update the overall run state."""
        self.update({"Status": "Running"})
        for step in self.steps:
            self.run_step(step)

    def start(self):
        """Start timing for the full sequence and mark the run as setting up."""

        self.update({"Status": "Setting Up"})
        self.start_time = datetime.now()

    def end(self):
        """Mark the sequence as completed."""
        self.update({"Status": "Completed"})

    def cancel(self):
        """Mark the sequence as cancelled."""
        self.update({"Status": "Cancelled"})
