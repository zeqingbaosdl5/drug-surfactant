import json

from opentrons_http_client import (
    download_data_file,
    get_data_file_info,
    get_data_files,
    get_health,
    get_protocol,
    get_protocol_analyses,
    get_protocol_analysis_document,
    run_protocol,
    upload_protocol,
)

import os

# Opentrons HTTP API base URL (replace with your robot's IP)
BASE_URL = os.getenv("OPENTRONS_BASE_URL", "http://192.168.0.5:31950")


def run_absorbance_protocol(verbosity=2):
    """Upload and run the absorbance protocol."""
    protocol_path = os.getenv(
        "PROTOCOL_PATH",
        "/Users/zeqingbao/Documents/GitHub/drug_surfactant/experiments/20250912-Plate Interpretation/absorbance_protocol_mwe.py",
    )

    # Upload protocol
    upload_response = upload_protocol(BASE_URL, protocol_path)
    protocol_id = upload_response["data"]["id"]
    print(f"Uploaded protocol: {protocol_id}")

    # Inspect uploaded protocol and analyses (debug)
    proto_meta = get_protocol(BASE_URL, protocol_id)
    print("Protocol meta keys:", list(proto_meta.keys()))
    analyses = get_protocol_analyses(BASE_URL, protocol_id)
    print("Analyses:", analyses.get("data", []))
    # if an analysis exists, fetch the first analysis document
    if analyses.get("data"):
        analysis_id = analyses["data"][0]["id"]
        doc = get_protocol_analysis_document(BASE_URL, protocol_id, analysis_id)
        print("Analysis document (truncated):")
        if isinstance(doc, str):
            print(doc[:1000])
        else:
            try:
                print(json.dumps(doc)[:1000])
            except TypeError:
                print(str(doc)[:1000])

    # Upload, create, start, wait and fetch run details using helper
    run_details = run_protocol(BASE_URL, protocol_path, {"wavelength": 650})
    final_status = run_details.get("data", {}).get("status", "unknown")
    print(f"Run completed with status: {final_status}")
    output_ids = run_details.get("data", {}).get("outputFileIds", []) or []

    if output_ids:
        print(f"Found {len(output_ids)} output file id(s) on run; downloading...")
        for fid in output_ids:
            info = get_data_file_info(BASE_URL, fid).get("data") or {}
            name = info.get("name") or f"datafile_{fid}"
            save_dir = os.getenv(
                "DATA_SAVE_DIR",
                "/Users/zeqingbao/Documents/GitHub/drug_surfactant/experiments",
            )
            save_path = f"{save_dir}/{name}"
            download_data_file(BASE_URL, fid, save_path)
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
            f" All data files: {get_data_files(BASE_URL)}"
        )


# Example usage
if __name__ == "__main__":
    # Check health
    health = get_health(BASE_URL)
    print("Health:", health)

    # Run the absorbance protocol
    run_absorbance_protocol()
