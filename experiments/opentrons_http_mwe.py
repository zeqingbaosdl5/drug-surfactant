import requests
import json

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
    with open(protocol_file_path, "rb") as f:
        files = {"files": f}
        response = requests.post(f"{BASE_URL}/protocols", files=files, headers=HEADERS)
    return response.json()


def create_run(protocol_id, run_time_parameters=None):
    """Create a new run from a protocol."""
    data = {"data": {"protocolId": protocol_id}}
    if run_time_parameters:
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

    # Create run
    run_response = create_run(protocol_id, {"wavelength": 600})
    run_id = run_response["data"]["id"]
    print(f"Created run: {run_id}")

    # Start run
    start_run(run_id)
    print(f"Started run: {run_id}")

    # Wait for completion
    final_status = wait_for_run_completion(run_id)
    print(f"Run completed with status: {final_status}")

    # Fetch and download absorbance data
    data_files = get_data_files()
    for file_info in data_files.get("data", []):
        if "raw_absorbance_in" in file_info.get("name", ""):
            file_id = file_info["id"]
            save_path = f"/Users/zeqingbao/Documents/GitHub/drug_surfactant/experiments/{file_info['name']}.csv"
            download_data_file(file_id, save_path)
            print(f"Downloaded absorbance data to: {save_path}")
            break


# Example usage
if __name__ == "__main__":
    # Check health
    health = get_health()
    print("Health:", health)

    # Run the absorbance protocol
    run_absorbance_protocol()
