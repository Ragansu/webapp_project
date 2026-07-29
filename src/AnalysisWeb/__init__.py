import os
from datetime import datetime
import resource
import warnings
import logging

from .logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore")

now = datetime.now()
formatted_time = now.strftime("%Y%m%d_%H_%M_%S")

current_dir = os.getcwd()

# 3. Join the safe, formatted string
_DEFAULT_SAVE_DIR = os.path.join(current_dir, formatted_time)
repo_dir = os.path.dirname(os.path.abspath(__file__))

def set_default_save_dir(file_loc):
    "To set the default save_dir"
    global _DEFAULT_SAVE_DIR
    if os.path.exists(file_loc):
        _DEFAULT_SAVE_DIR = file_loc


def get_default_save_dir():
    "To get the default save_dir"
    return _DEFAULT_SAVE_DIR


def get_memory_usage(stage=""):
    # Max RSS (Linux KB → MB)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    peak_mb = usage.ru_maxrss / 1024

    # Current RSS
    current_mb = None
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                current_kb = int(line.split()[1])
                current_mb = current_kb / 1024
            if line.startswith("VmHWM:"):  # high-water mark (another peak measure)
                pass

    # System total RAM
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemTotal:"):
                total_kb = int(line.split()[1])
                break
    total_mb = total_kb / 1024

    logger.info(
        f"[{stage}] Current RAM: {current_mb:.2f} MB | "
        f"Peak RAM: {peak_mb:.2f} MB | "
        f"System RAM: {total_mb:.2f} MB"
    )


def memory_usage(func):
    def wrapper(*args, **kwargs):
        get_memory_usage(stage=f"Before {func.__name__}")
        result = func(*args, **kwargs)
        get_memory_usage(stage=f"After  {func.__name__}")
        return result

    return wrapper

