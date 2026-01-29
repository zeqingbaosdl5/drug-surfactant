import os
import time
from opentrons_http_client import (
    upload_protocol,
    create_run,
    start_run,
    wait_for_run_completion,
    get_run_details,
    get_protocol_analyses,
    wait_for_analysis_completion
)

BASE_URL = os.getenv("OPENTRONS_BASE_URL", "http://192.168.0.5:31950")

LABWARE_DEFINITIONS = [
    os.path.join(os.path.dirname(__file__), "allenlab_8_wellplate_20000ul.json"),
    os.path.join(os.path.dirname(__file__), "corning_96_wellplate_360ul_flat_new.json")
]

def run_otflex_iA(protocol_file_path: str):
    """
    Uploads the generated protocol file, runs it, and returns the Run ID.
    """
    print(f"Uploading {os.path.basename(protocol_file_path)}...")
    
    # 1. Upload
    upload_response = upload_protocol(BASE_URL, protocol_file_path, labware_paths=LABWARE_DEFINITIONS)
    protocol_id = upload_response['data']['id']
    print(f"Protocol Uploaded: {protocol_id}")

    # 2. Analyze
    print("Waiting for protocol analysis...")
    # Polling for analysis
    analyses = get_protocol_analyses(BASE_URL, protocol_id)
    if analyses.get("data"):
        analysis_id = analyses["data"][0]["id"]
        wait_for_analysis_completion(BASE_URL, protocol_id, analysis_id)
    
    # 3. Create Run
    # run_time_parameters is empty because data is hardcoded in the file
    run_response = create_run(BASE_URL, protocol_id, run_time_parameters={})
    run_id = run_response['data']['id']
    print(f"Run Created: {run_id}. Starting...")
    
    # 4. Start
    start_run(BASE_URL, run_id)
    
    # 5. Wait for Finish
    final_status = wait_for_run_completion(BASE_URL, run_id)
    print(f"Run finished with status: {final_status}")
    
    return run_id