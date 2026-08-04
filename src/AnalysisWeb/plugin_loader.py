
import importlib.util


def load_job_plugin(path):

    spec = importlib.util.spec_from_file_location(
        "job_plugin",
        path
    )

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module