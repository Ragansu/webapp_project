"""Command-line entry point for launching the AnalysisWeb dashboard."""

import argparse
import threading
import webbrowser

from .app import create_app


def main():
    """Parse CLI arguments and start the dashboard web application."""

    parser = argparse.ArgumentParser(description="Launch AnalysisWeb dashboard")

    parser.add_argument(
        "--results-dir",
        required=True,
        help="Directory containing result_* folders",
    )

    parser.add_argument(
        "--json-dir",
        required=True,
        help="Directory containing JSON files",
    )

    parser.add_argument(
        "--config",
        default=None,
        help="Dashboard configuration YAML file",
    )

    parser.add_argument(
        "--port",
        default=5088,
        type=int,
        help="Web port",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode",
    )

    args = parser.parse_args()

    app = create_app(
        args.results_dir,
        args.json_dir,
        args.config,
    )

    url = f"http://127.0.0.1:{args.port}"

    print()
    print("AnalysisWeb running:")
    print(url)
    print()

    threading.Timer(
        1.0,
        lambda: webbrowser.open(url),
    ).start()

    app.run(
        host="127.0.0.1",
        port=args.port,
        debug=args.debug,
    )
