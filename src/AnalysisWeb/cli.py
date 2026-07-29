import argparse
import threading
import webbrowser

from .app import create_app


def main():

    parser = argparse.ArgumentParser(
        description="Launch AnalysisWeb dashboard"
    )

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
        "--port",
        default=5088,
        type=int,
        help="Web port",
    )

    args = parser.parse_args()


    app = create_app(
        results_dir=args.results_dir,
        json_dir=args.json_dir,
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
    )