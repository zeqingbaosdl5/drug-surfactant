import json
import os

from opentrons_http_client import (
    download_data_file,
    get_data_file_info,
    get_data_files,
    get_health,
    get_log,
    get_protocol,
    get_protocol_analyses,
    get_protocol_analysis_document,
    get_run_details,
    start_run,
    upload_protocol,
    create_run,
)

# Opentrons HTTP API base URL (replace with your robot's IP)
BASE_URL = "http://192.168.0.5:31950"  # Updated with provided IP


def wait_for_run_completion(run_id, poll_interval=5, verbosity=2):
    """Wait for a run to complete by polling its status and monitoring logs.

    verbosity levels:
      0 - quiet (no output)
      1 - status changes only
      2 - status + filtered high-level log lines
      3 - status + full log lines
    """
    import time

    HIGHLIGHT_KEYWORDS = [
        "RUNTIME_PARAM_WAVELENGTH",
        "Using wavelength",
        "raw_absorbance",
        "Sample Wavelength",
        "protocol.comment",
        "ERROR",
        "WARNING",
    ]

    previous_log = ""
    previous_status = None
    while True:
        details = get_run_details(BASE_URL, run_id)
        status = details.get("data", {}).get("status", "unknown")

        # Print status if allowed and if it changed
        if verbosity >= 1 and status != previous_status:
            print(f"Run status: {status}")
            previous_status = status

        # Fetch log (may be large)
        current_log = get_log(BASE_URL, "api.log")
        new_lines = current_log[len(previous_log) :]

        if verbosity >= 2 and new_lines.strip():
            if verbosity >= 3:
                # Verbose: print everything
                print("New log lines:")
                print(new_lines)
            else:
                # Filter for high-level keywords to reduce noise
                matched = []
                for line in new_lines.splitlines():
                    for kw in HIGHLIGHT_KEYWORDS:
                        if kw in line:
                            matched.append(line)
                            break
                if matched:
                    print("New high-level log lines:")
                    print("\n".join(matched))
        previous_log = current_log

        if status in ["succeeded", "failed", "stopped"]:
            return status
        time.sleep(poll_interval)


def run_absorbance_protocol(verbosity=2):
    """Upload and run the absorbance protocol."""
    protocol_path = "/Users/zeqingbao/Documents/GitHub/drug_surfactant/experiments/20250912-Plate Interpretation/absorbance_protocol_mwe.py"

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
            except Exception:
                print(str(doc)[:1000])

    # Create run
    run_response = create_run(BASE_URL, protocol_id, {"wavelength": 650})
    run_id = run_response["data"]["id"]
    print(f"Created run: {run_id}")

    # Start run
    start_run(BASE_URL, run_id)
    print(f"Started run: {run_id}")

    # Wait for completion
    final_status = wait_for_run_completion(run_id, verbosity=verbosity)
    print(f"Run completed with status: {final_status}")
    # Prefer files explicitly recorded on the run (outputFileIds).
    # This is more robust than scanning all dataFiles and guessing which one belongs
    # to this run.
    run_details = get_run_details(BASE_URL, run_id)
    output_ids = run_details.get("data", {}).get("outputFileIds", []) or []

    if output_ids:
        print(f"Found {len(output_ids)} output file id(s) on run; downloading...")
        for fid in output_ids:
            info = get_data_file_info(BASE_URL, fid).get("data") or {}
            name = info.get("name") or f"datafile_{fid}"
            save_path = (
                f"/Users/zeqingbao/Documents/GitHub/drug_surfactant/experiments/{name}"
            )
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

    1 + 1
