import importlib.util
import sys
from pathlib import Path


def load_job_plugin(path):
    path = Path(path).resolve()

    print(f"Loading job plugin from: {path}")

    sys.path.insert(0, str(path.parent))

    spec = importlib.util.spec_from_file_location("job_plugin", path)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module
