import requests
import json
import os
import uuid

# Opentrons HTTP API base URL (replace with your robot's IP)
BASE_URL = "http://192.168.0.5:31950"  # Updated with provided IP

# Required headers for Opentrons API
HEADERS = {"opentrons-version": "4"}


def get_health():
    """Check robot health."""
    response = requests.get(f"{BASE_URL}/health", headers=HEADERS)
    return response.json()


def upload_protocol(protocol_file_path):
    """Upload a protocol file."""
    # Force a unique filename to avoid server-side caching/stale analyses
    base = os.path.basename(protocol_file_path)
    prefix = uuid.uuid4().hex[:6]
    unique_name = f"{prefix}_{base}"
    with open(protocol_file_path, "rb") as f:
        # attach filename in multipart upload
        files = {"files": (unique_name, f)}
        response = requests.post(f"{BASE_URL}/protocols", files=files, headers=HEADERS)
    return response.json()


def create_run(protocol_id, run_time_parameters):
    """Create a new run from a protocol."""
    data = {"data": {"protocolId": protocol_id}}
    data["data"]["runTimeParameterValues"] = run_time_parameters
    response = requests.post(f"{BASE_URL}/runs", json=data, headers=HEADERS)
    return response.json()


def get_runs():
    """Get list of runs."""
    response = requests.get(f"{BASE_URL}/runs", headers=HEADERS)
    return response.json()


def get_run_details(run_id):
    """Get details of a specific run."""
    response = requests.get(f"{BASE_URL}/runs/{run_id}", headers=HEADERS)
    return response.json()


def get_data_files():
    """Get list of data files."""
    response = requests.get(f"{BASE_URL}/dataFiles", headers=HEADERS)
    return response.json()


def get_data_file_info(data_file_id):
    """Get metadata for a single data file by id."""
    response = requests.get(f"{BASE_URL}/dataFiles/{data_file_id}", headers=HEADERS)
    try:
        return response.json()
    except Exception:
        return {"data": {}}


def download_data_file(data_file_id, save_path):
    """Download a data file."""
    response = requests.get(
        f"{BASE_URL}/dataFiles/{data_file_id}/download", headers=HEADERS
    )
    with open(save_path, "wb") as f:
        f.write(response.content)
    return save_path


def get_log(log_identifier):
    """Get a specific log file."""
    response = requests.get(f"{BASE_URL}/logs/{log_identifier}", headers=HEADERS)
    return response.text


def get_protocol(protocol_id):
    """Get protocol metadata for a protocol id."""
    response = requests.get(f"{BASE_URL}/protocols/{protocol_id}", headers=HEADERS)
    return response.json()


def get_protocol_analyses(protocol_id):
    """List analyses for a protocol."""
    response = requests.get(
        f"{BASE_URL}/protocols/{protocol_id}/analyses", headers=HEADERS
    )
    return response.json()


def get_protocol_analysis_document(protocol_id, analysis_id):
    """Get the analysis document (source/AST) for a protocol analysis."""
    response = requests.get(
        f"{BASE_URL}/protocols/{protocol_id}/analyses/{analysis_id}/asDocument",
        headers=HEADERS,
    )
    # return raw text or json depending on server
    try:
        return response.json()
    except Exception:
        return response.text


def start_run(run_id):
    """Start a run."""
    response = requests.post(
        f"{BASE_URL}/runs/{run_id}/actions",
        json={"data": {"actionType": "play"}},
        headers=HEADERS,
    )
    return response.json()


def wait_for_run_completion(run_id, poll_interval=5):
    """Wait for a run to complete by polling its status and monitoring logs."""
    import time

    previous_log = ""
    previous_status = None
    while True:
        details = get_run_details(run_id)
        status = details.get("data", {}).get("status", "unknown")

        # Only print status if it changed
        if status != previous_status:
            print(f"Run status: {status}")
            previous_status = status

        # Fetch and print new log lines
        current_log = get_log("api.log")
        new_lines = current_log[len(previous_log) :]
        if new_lines.strip():
            print("New log lines:")
            print(new_lines)
        previous_log = current_log

        if status in ["succeeded", "failed", "stopped"]:
            return status
        time.sleep(poll_interval)


def run_absorbance_protocol():
    """Upload and run the absorbance protocol."""
    protocol_path = "/Users/zeqingbao/Documents/GitHub/drug_surfactant/experiments/20250912-Plate Interpretation/absorbance_protocol_mwe.py"

    # Upload protocol
    upload_response = upload_protocol(protocol_path)
    protocol_id = upload_response["data"]["id"]
    print(f"Uploaded protocol: {protocol_id}")

    # Inspect uploaded protocol and analyses (debug)
    proto_meta = get_protocol(protocol_id)
    print("Protocol meta keys:", list(proto_meta.keys()))
    analyses = get_protocol_analyses(protocol_id)
    print("Analyses:", analyses.get("data", []))
    # if an analysis exists, fetch the first analysis document
    if analyses.get("data"):
        analysis_id = analyses["data"][0]["id"]
        doc = get_protocol_analysis_document(protocol_id, analysis_id)
        print("Analysis document (truncated):")
        if isinstance(doc, str):
            print(doc[:1000])
        else:
            try:
                print(json.dumps(doc)[:1000])
            except Exception:
                print(str(doc)[:1000])

    # Create run
    run_response = create_run(protocol_id, {"wavelength": 650})
    run_id = run_response["data"]["id"]
    print(f"Created run: {run_id}")

    # Start run
    start_run(run_id)
    print(f"Started run: {run_id}")

    # Wait for completion
    final_status = wait_for_run_completion(run_id)
    print(f"Run completed with status: {final_status}")
    # Prefer files explicitly recorded on the run (outputFileIds).
    # This is more robust than scanning all dataFiles and guessing which one belongs
    # to this run.
    run_details = get_run_details(run_id)
    output_ids = run_details.get("data", {}).get("outputFileIds", []) or []

    if output_ids:
        print(f"Found {len(output_ids)} output file id(s) on run; downloading...")
        for fid in output_ids:
            info = get_data_file_info(fid).get("data") or {}
            name = info.get("name") or f"datafile_{fid}"
            save_path = (
                f"/Users/zeqingbao/Documents/GitHub/drug_surfactant/experiments/{name}"
            )
            download_data_file(fid, save_path)
            print(f"Downloaded data file {fid} -> {save_path}")
    else:
        # Require explicit run outputs. Failing fast reduces risk of downloading
        # stale files when multiple data files share names on the robot.
        raise RuntimeError(
            "Run did not report any outputFileIds; cannot reliably determine "
            "which data files belong to this run. Ensure your protocol registers "
            "output files (or write a unique filename per run via a runtime "
            "parameter) so the client can download results deterministically."
            f" Run details: {run_details}"
            f" All data files: {get_data_files()}"
        )


# Example usage
if __name__ == "__main__":
    # Check health
    health = get_health()
    print("Health:", health)

    # Run the absorbance protocol
    run_absorbance_protocol()

    1 + 1
