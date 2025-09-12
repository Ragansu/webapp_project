#!/usr/bin/python3

import os
from flask import Flask, send_from_directory, abort, request, jsonify

import argparse
import subprocess
parser = argparse.ArgumentParser()

parser.add_argument(
    "--cca",
    action="store_true",
    default=False,
    help="Enable Retraining",
)
app = Flask(__name__)

args, _ = parser.parse_known_args()

repo = os.path.dirname(__file__)

cca = args.cca

if cca:

    # Serve main HTML page
    @app.route("/")
    def home():
        return send_from_directory("templates", "index_cca.html")

else :

    # Serve main HTML page
    @app.route("/")
    def home():
        return send_from_directory("templates", "index.html")

# Serve static files (CSS, JS, etc.)
@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

@app.route("/style.css")
def serve_css():
    return send_from_directory("static", "style.css")

# Serve CSV files directly from static (for your results_data.csv)
@app.route("/<filename>")
def serve_root_files(filename):
    if filename.endswith('.csv'):
        return send_from_directory("static", filename)

    abort(404)

# Serve result files from results/result_* folders
@app.route("/<folder>/<path:filename>")
def serve_result_direct(folder, filename):
    if not folder.startswith("result_"):
        abort(404)
    
    folder_path = os.path.join("results", folder)
    
    if not os.path.exists(os.path.join(folder_path, filename)):
        abort(404)
    
    return send_from_directory(folder_path, filename)

@app.route("/<folder>/")
def serve_result_index(folder):
    if not folder.startswith("result_"):
        abort(404)
    
    folder_path = os.path.join("results", folder)
    filename = "index.html"
    
    if not os.path.exists(os.path.join(folder_path, filename)):
        abort(404)
    
    return send_from_directory(folder_path, filename)
# Endpoint triggered by your button
@app.route("/send_sbatch_job", methods=["POST"])
def send_sbatch_job():
    data = request.get_json()
    model_type = data.get("modelType")

    try:
        result = subprocess.run(
            ["bash", f"{repo}/extra_scripts/send_sbatch_job.sh", "--model-type", model_type],
            capture_output=True,
            text=True,
            check=True,
        )
        return jsonify({"status": "success", "output": result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "output": e.stderr}), 500


@app.route("/cancel_job", methods=["POST"])
def cancel_job():
    data = request.get_json()
    job_id = data.get("jobId")
    model_type = data.get("modelType")
    date = data.get("date")

    if not job_id:
        return jsonify({"status": "error", "output": "Missing job_id"}), 400

    print("Date:", date)
    print("Job ID:", job_id)
    print("Model Type:", model_type)

    try:
        helper_result = subprocess.run(
            [
                "bash",
                f"{repo}/extra_scripts/cancel_sbatch_job.sh",
                "--model-type",
                str(model_type),
                "--job-id",
                str(job_id),
                "--unique-date",
                str(date),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Second: cancel job with SLURM scancel
        scancel_result = subprocess.run(
            ["scancel", str(job_id)],  
            capture_output=True,
            text=True,
            check=True,
        )

        return jsonify({
            "status": "success",
            "helper_output": helper_result.stdout.strip(),
            "scancel_output": scancel_result.stdout.strip(),
        })

    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "output": e.stderr.strip()}), 500





if __name__ == "__main__":
    app.run(debug=True)
