import os
import uuid

import requests


HEADERS = {"opentrons-version": "4"}


def get_health(base_url: str):
    response = requests.get(f"{base_url}/health", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def upload_protocol(base_url: str, protocol_file_path: str, labware_paths: list = None):
    file_objects = []
    files_list = []

    # Open protocol file
    f_proto = open(protocol_file_path, "rb")
    file_objects.append(f_proto)
    base = os.path.basename(protocol_file_path)
    prefix = uuid.uuid4().hex[:6]
    unique_name = f"{prefix}_{base}"
    files_list.append((unique_name, f_proto))

    # Open labware files
    if labware_paths:
        for labware_path in labware_paths:
            f_lab = open(labware_path, "rb")
            file_objects.append(f_lab)
            base = os.path.basename(labware_path)
            prefix = uuid.uuid4().hex[:6]
            unique_name = f"{prefix}_{base}"
            files_list.append((unique_name, f_lab))

    files = [("files", ft) for ft in files_list]
    try:
        response = requests.post(f"{base_url}/protocols", files=files, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    finally:
        for f in file_objects:
            f.close()


def create_run(base_url: str, protocol_id: str, run_time_parameters: dict):
    data = {"data": {"protocolId": protocol_id}}
    data["data"]["runTimeParameterValues"] = run_time_parameters
    response = requests.post(f"{base_url}/runs", json=data, headers=HEADERS)
    if not response.ok:
        raise ValueError(
            f"Failed to create run: {response.status_code} {response.text}"
        )
    return response.json()


def get_runs(base_url: str):
    response = requests.get(f"{base_url}/runs", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_run_details(base_url: str, run_id: str):
    response = requests.get(f"{base_url}/runs/{run_id}", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_data_files(base_url: str):
    response = requests.get(f"{base_url}/dataFiles", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_data_file_info(base_url: str, data_file_id: str):
    response = requests.get(f"{base_url}/dataFiles/{data_file_id}", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def download_data_file(base_url: str, data_file_id: str, save_path: str):
    response = requests.get(
        f"{base_url}/dataFiles/{data_file_id}/download", headers=HEADERS
    )
    response.raise_for_status()
    with open(save_path, "wb") as f:
        f.write(response.content)
    return save_path


def get_log(base_url: str, log_identifier: str):
    response = requests.get(f"{base_url}/logs/{log_identifier}", headers=HEADERS)
    response.raise_for_status()
    return response.text


def get_protocol(base_url: str, protocol_id: str):
    response = requests.get(f"{base_url}/protocols/{protocol_id}", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_protocol_analyses(base_url: str, protocol_id: str):
    response = requests.get(
        f"{base_url}/protocols/{protocol_id}/analyses", headers=HEADERS
    )
    response.raise_for_status()
    return response.json()


def get_protocol_analysis_document(base_url: str, protocol_id: str, analysis_id: str):
    response = requests.get(
        f"{base_url}/protocols/{protocol_id}/analyses/{analysis_id}/asDocument",
        headers=HEADERS,
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return response.text


def start_run(base_url: str, run_id: str):
    response = requests.post(
        f"{base_url}/runs/{run_id}/actions",
        json={"data": {"actionType": "play"}},
        headers=HEADERS,
    )
    response.raise_for_status()
    return response.json()


def wait_for_run_completion(base_url: str, run_id: str, poll_interval=5):
    import time

    previous_status = None
    while True:
        details = get_run_details(base_url, run_id)
        status = details.get("data", {}).get("status", "unknown")

        if status != previous_status:
            print(f"Run status: {status}")
            previous_status = status

        if status in ["succeeded", "failed", "stopped"]:
            return status
        time.sleep(poll_interval)


def wait_for_analysis_completion(
    base_url: str, protocol_id: str, analysis_id: str, poll_interval=5
):
    import time

    while True:
        analyses = get_protocol_analyses(base_url, protocol_id)
        for analysis in analyses.get("data", []):
            if analysis["id"] == analysis_id:
                status = analysis["status"]
                if status == "completed":
                    return analysis
                elif status == "failed":
                    raise ValueError(f"Analysis failed for protocol {protocol_id}")
                break
        time.sleep(poll_interval)


def run_protocol(
    base_url: str,
    protocol_path: str,
    run_time_parameters: dict,
    labware_paths: list = None,
):
    upload_response = upload_protocol(base_url, protocol_path, labware_paths)
    protocol_id = upload_response["data"]["id"]
    print(f"Uploaded protocol: {protocol_id}")

    # Check analyses
    analyses = get_protocol_analyses(base_url, protocol_id)
    print("Analyses:", analyses.get("data", []))
    if analyses.get("data"):
        analysis = analyses["data"][0]
        analysis_id = analysis["id"]
        if analysis["status"] == "pending":
            print("Waiting for analysis to complete...")
            wait_for_analysis_completion(base_url, protocol_id, analysis_id)
        doc = get_protocol_analysis_document(base_url, protocol_id, analysis_id)
        print("Analysis document (truncated):")
        if isinstance(doc, str):
            print(doc[:1000])
        else:
            try:
                import json

                print(json.dumps(doc)[:1000])
            except TypeError:
                print(str(doc)[:1000])
        # Check for errors in doc
        if isinstance(doc, dict) and "errors" in doc and doc["errors"]:
            raise ValueError(f"Protocol analysis errors: {doc['errors']}")

    run_response = create_run(base_url, protocol_id, run_time_parameters)
    run_id = run_response["data"]["id"]
    print(f"Created run: {run_id}")

    start_run(base_url, run_id)
    print(f"Started run: {run_id}")

    final_status = wait_for_run_completion(base_url, run_id)
    print(f"Run completed with status: {final_status}")

    return get_run_details(base_url, run_id)
