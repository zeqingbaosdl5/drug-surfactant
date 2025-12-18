import os

from opentrons_http_client import (
    download_data_file,
    get_data_file_info,
    get_data_files,
    get_health,
    run_protocol,
)


BASE_URL = "http://192.168.0.5:31950"


def run_otflex_iA(otflex_params: dict):
    protocol_path = os.path.join(
        os.path.dirname(__file__),
        "20250912-Plate Interpretation",
        "otflex_iA.py",
    )

    labware_paths = [
        os.path.join(os.path.dirname(__file__), "allenlab_8_wellplate_20000ul.json"),
        os.path.join(
            os.path.dirname(__file__), "corning_96_wellplate_360ul_flat_new.json"
        ),
    ]

    run_details = run_protocol(
        BASE_URL, protocol_path, otflex_params, labware_paths=labware_paths
    )
    output_ids = run_details.get("data", {}).get("outputFileIds", []) or []

    if output_ids:
        print(f"Found {len(output_ids)} output file id(s) on run; downloading...")
        for fid in output_ids:
            info = get_data_file_info(BASE_URL, fid).get("data") or {}
            name = info.get("name") or f"datafile_{fid}"
            # Make filename unique by appending part of run_id
            run_id = run_details["data"]["id"]
            if name.endswith(".csv"):
                name = name.replace(".csv", f"_{run_id[:8]}.csv")
            else:
                name = f"{name}_{run_id[:8]}"
            save_path = os.path.join(os.path.dirname(__file__), "data", name)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            download_data_file(BASE_URL, fid, save_path)
            print(f"Downloaded data file {fid} -> {save_path}")
    else:
        raise RuntimeError(
            "Run did not report any outputFileIds; cannot reliably determine "
            "which data files belong to this run."
            f" Run details: {run_details}"
            f" All data files: {get_data_files(BASE_URL)}"
        )


# Example usage
health = get_health(BASE_URL)
print("Health:", health)

example_params = {
    "drug": 180.0,
    "s1": 300.0,
    "s2": 0.0,
    "s3": 0.0,
    "s4": 300.0,
    "s5": 0.0,
    "s6": 0.0,
    "s7": 0.0,
    "s8": 0.0,
    "dmso": 0.0,
    "water": 550.0,
    "IBP": 180.0,
    "LOV": 0.0,
    "DCF": 0.0,
    "GLV": 0.0,
    "next_plate_well": "F1",
    "next_deepplate_well": "F1",
}

run_otflex_iA(example_params)
