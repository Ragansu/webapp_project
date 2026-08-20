"""Tests for the Flask analysis application routes."""

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from flask import Flask

from analysisweb.routes import register_routes, safe_send


@pytest.fixture
def app(tmp_path):
    """Create a Flask application configured for testing."""
    app = Flask(
        __name__,
        template_folder=str(tmp_path / "templates"),
    )

    results_dir = tmp_path / "results"
    json_dir = tmp_path / "json"

    results_dir.mkdir()
    json_dir.mkdir()

    app.config.update(
        TESTING=True,
        JSON_DIR=json_dir,
        RESULTS_DIR=results_dir,
        DASHBOARD_CONFIG={"test": True},
    )

    app.job_backend = SimpleNamespace()

    # Minimal templates required by the routes.
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir(exist_ok=True)

    (templates_dir / "index.html").write_text(
        "<html><body>Dashboard {{ config.test }}</body></html>",
        encoding="utf-8",
    )

    (templates_dir / "action_modal.html").write_text(
        "<html><body>Action Modal</body></html>",
        encoding="utf-8",
    )

    register_routes(app)

    return app


@pytest.fixture
def client(app):
    """Return a Flask test client."""
    return app.test_client()


# ---------------------------------------------------------------------------
# safe_send
# ---------------------------------------------------------------------------


def test_safe_send_existing_file(tmp_path):
    """safe_send serves an existing file."""
    directory = tmp_path / "files"
    directory.mkdir()

    test_file = directory / "report.html"
    test_file.write_text("hello", encoding="utf-8")

    app = Flask(__name__)

    @app.route("/files/<path:filename>")
    def serve_file(filename):
        return safe_send(directory, filename)

    client = app.test_client()

    response = client.get("/files/report.html")

    assert response.status_code == 200
    assert response.data == b"hello"


def test_safe_send_missing_file(tmp_path):
    """safe_send returns 404 for a missing file."""
    directory = tmp_path / "files"
    directory.mkdir()

    app = Flask(__name__)

    with app.test_request_context():
        with pytest.raises(Exception) as exc_info:
            safe_send(directory, "missing.html")

    assert exc_info.value.code == 404


def test_safe_send_blocks_parent_traversal(tmp_path):
    """safe_send rejects ../ path traversal."""
    directory = tmp_path / "files"
    directory.mkdir()

    secret = tmp_path / "secret.txt"
    secret.write_text("secret", encoding="utf-8")

    app = Flask(__name__)

    with app.test_request_context():
        with pytest.raises(Exception) as exc_info:
            safe_send(directory, "../secret.txt")

    assert exc_info.value.code == 403


def test_safe_send_blocks_absolute_path(tmp_path):
    """safe_send rejects absolute paths outside the directory."""
    directory = tmp_path / "files"
    directory.mkdir()

    secret = tmp_path / "secret.txt"
    secret.write_text("secret", encoding="utf-8")

    app = Flask(__name__)

    with app.test_request_context():
        with pytest.raises(Exception) as exc_info:
            safe_send(directory, str(secret))

    assert exc_info.value.code == 403


def test_safe_send_allows_nested_file(tmp_path):
    """safe_send serves files inside nested directories."""
    directory = tmp_path / "files"
    nested = directory / "reports"
    nested.mkdir(parents=True)

    report = nested / "result.html"
    report.write_text("nested report", encoding="utf-8")

    app = Flask(__name__)

    @app.route("/files/<path:filename>")
    def serve_file(filename):
        return safe_send(directory, filename)

    client = app.test_client()

    response = client.get("/files/reports/result.html")

    assert response.status_code == 200
    assert response.data == b"nested report"


# ---------------------------------------------------------------------------
# Home route
# ---------------------------------------------------------------------------


def test_home(client):
    """The home route renders the dashboard."""
    response = client.get("/")

    assert response.status_code == 200
    assert b"Dashboard" in response.data
    assert b"True" in response.data


# ---------------------------------------------------------------------------
# Action modal
# ---------------------------------------------------------------------------


def test_action_modal(client):
    """The action modal route renders its template."""
    response = client.get("/action-modal")

    assert response.status_code == 200
    assert b"Action Modal" in response.data


# ---------------------------------------------------------------------------
# JSON files
# ---------------------------------------------------------------------------


def test_json_file(client, app):
    """The JSON route serves an existing JSON file."""
    json_dir = Path(app.config["JSON_DIR"])

    json_file = json_dir / "results.json"
    json_file.write_text(
        '{"accuracy": 0.95}',
        encoding="utf-8",
    )

    response = client.get("/json/results.json")

    assert response.status_code == 200
    assert response.get_json() == {"accuracy": 0.95}


def test_json_file_missing(client):
    """The JSON route returns 404 for a missing file."""
    response = client.get("/json/missing.json")

    assert response.status_code == 404


def test_json_nested_file(client, app):
    """The JSON route supports nested paths."""
    json_dir = Path(app.config["JSON_DIR"])
    nested_dir = json_dir / "run1"
    nested_dir.mkdir()

    json_file = nested_dir / "results.json"
    json_file.write_text(
        '{"status": "complete"}',
        encoding="utf-8",
    )

    response = client.get("/json/run1/results.json")

    assert response.status_code == 200
    assert response.get_json() == {"status": "complete"}


def test_json_path_traversal_is_blocked(client, app, tmp_path):
    """The JSON route must not serve files outside JSON_DIR."""
    secret = tmp_path / "secret.json"
    secret.write_text(
        '{"secret": true}',
        encoding="utf-8",
    )

    response = client.get("/json/../secret.json")

    assert response.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Result files
# ---------------------------------------------------------------------------


def test_result_file(client, app):
    """The result route serves an existing result file."""
    results_dir = Path(app.config["RESULTS_DIR"])
    folder = results_dir / "run1"
    folder.mkdir()

    report = folder / "report.html"
    report.write_text(
        "<html>Report</html>",
        encoding="utf-8",
    )

    response = client.get("/run1/report.html")

    assert response.status_code == 200
    assert b"Report" in response.data


def test_result_file_missing_folder(client):
    """The result route returns 404 for a missing result folder."""
    response = client.get("/does-not-exist/report.html")

    assert response.status_code == 404


def test_result_file_missing_file(client, app):
    """The result route returns 404 for a missing file."""
    results_dir = Path(app.config["RESULTS_DIR"])
    folder = results_dir / "run1"
    folder.mkdir()

    response = client.get("/run1/missing.html")

    assert response.status_code == 404


def test_result_file_nested_path(client, app):
    """The result route supports files nested below a result folder."""
    results_dir = Path(app.config["RESULTS_DIR"])

    nested = results_dir / "run1" / "reports"
    nested.mkdir(parents=True)

    report = nested / "result.html"
    report.write_text(
        "nested result",
        encoding="utf-8",
    )

    response = client.get("/run1/reports/result.html")

    assert response.status_code == 200
    assert b"nested result" in response.data


def test_result_file_path_traversal(client, app, tmp_path):
    """The result route blocks path traversal."""
    results_dir = Path(app.config["RESULTS_DIR"])
    folder = results_dir / "run1"
    folder.mkdir()

    secret = tmp_path / "secret.html"
    secret.write_text(
        "TOP SECRET",
        encoding="utf-8",
    )

    response = client.get("/run1/../secret.html")

    assert response.status_code in (403, 404)


# ---------------------------------------------------------------------------
# send_sbatch_job
# ---------------------------------------------------------------------------


def test_send_sbatch_job_success(client, app, monkeypatch):
    """A successful job submission returns a success response."""
    submitted = {}

    def submit_job(data, date_str):
        submitted["data"] = data
        submitted["date_str"] = date_str
        return "job submitted"

    app.job_backend.submit_job = submit_job

    response = client.post(
        "/send_sbatch_job",
        json={"script": "train.sh"},
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["output"] == "job submitted"

    assert submitted["data"] == {"script": "train.sh"}
    assert len(submitted["date_str"]) == 17


def test_send_sbatch_job_backend_error(client, app):
    """A failed job submission returns HTTP 500."""

    def submit_job(data, date_str):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd="sbatch",
            stderr="submission failed",
        )

    app.job_backend.submit_job = submit_job

    response = client.post(
        "/send_sbatch_job",
        json={"script": "train.sh"},
    )

    assert response.status_code == 500

    data = response.get_json()

    assert data["status"] == "error"
    assert data["output"] == "submission failed"


def test_send_sbatch_job_passes_json_payload(client, app):
    """The submitted JSON payload is passed unchanged to the backend."""
    captured = {}

    def submit_job(data, date_str):
        captured["data"] = data
        return "ok"

    app.job_backend.submit_job = submit_job

    payload = {
        "job_name": "test",
        "nodes": 2,
        "partition": "cpu",
    }

    response = client.post(
        "/send_sbatch_job",
        json=payload,
    )

    assert response.status_code == 200
    assert captured["data"] == payload


# ---------------------------------------------------------------------------
# cancel_sbatch_job
# ---------------------------------------------------------------------------


def test_cancel_sbatch_job_success(client, app):
    """A successful cancellation returns a success response."""
    captured = {}

    def cancel_job(data):
        captured["data"] = data
        return "job cancelled"

    app.job_backend.cancel_job = cancel_job

    response = client.post(
        "/cancel_sbatch_job",
        json={"job_id": "12345"},
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["output"] == "job cancelled"
    assert captured["data"] == {"job_id": "12345"}


def test_cancel_sbatch_job_backend_error(client, app):
    """A failed cancellation returns HTTP 500."""

    def cancel_job(data):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd="scancel",
            stderr="job not found\n",
        )

    app.job_backend.cancel_job = cancel_job

    response = client.post(
        "/cancel_sbatch_job",
        json={"job_id": "12345"},
    )

    assert response.status_code == 500

    data = response.get_json()

    assert data["status"] == "error"
    assert data["output"] == "job not found"


# ---------------------------------------------------------------------------
# HTTP methods
# ---------------------------------------------------------------------------


def test_send_sbatch_job_requires_post(client):
    """Job submission does not accept GET."""
    response = client.get("/send_sbatch_job")

    assert response.status_code == 405


def test_cancel_sbatch_job_requires_post(client):
    """Job cancellation does not accept GET."""
    response = client.get("/cancel_sbatch_job")

    assert response.status_code == 405
