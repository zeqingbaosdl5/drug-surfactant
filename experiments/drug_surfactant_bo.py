import json
import os
import sys

import glob
import itertools
import numpy as np
import math
from datetime import datetime


REPO_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(REPO_DIR, "experiments"))

SMOKE_TEST = str(os.getenv("SMOKE_TEST", "")).strip().lower() in {"1", "true"}

if not SMOKE_TEST:
    print("Running with real robot execution (non smoke test).")
    from opentrons_http_otflex_iA_mwe import run_otflex_iA
else:
    print("Running with dummy robot execution (smoke test).")

    def run_otflex_iA(otflex_params):
        """
        Dummy function to mimic the real robot execution for SMOKE_TEST.
        Writes a mock plate-format CSV file (A-H rows, 1-12 columns) with plausible absorbance values.
        """
        import os
        import random

        # Try to get the global n (iteration number)
        iteration = globals().get("n", 0)
        raw_data_file = f"{RAW_DATA_FILE_PATH}i{iteration}.csv"
        os.makedirs(os.path.dirname(raw_data_file), exist_ok=True)
        # Write a plate-format CSV: first row is header (empty, 1,2,...,12), then A-H rows
        rows = [chr(ord("A") + i) for i in range(8)]
        cols = [str(i) for i in range(1, 13)]
        with open(raw_data_file, "w", newline="") as f:
            f.write("," + ",".join(cols) + "\n")
            for row in rows:
                # 80% chance below 0.06, 20% above
                values = []
                for _ in cols:
                    if random.random() < 0.9:
                        val = random.uniform(0.04, 0.059)
                    else:
                        val = random.uniform(0.06, 0.12)
                    values.append(f"{val:.3f}")
                f.write(f"{row}," + ",".join(values) + "\n")
        # print(f"[SMOKE TEST] Tips Used: 1000uL @ {otflex_params['tip1000_well']}, 50uL @ {otflex_params['tip50_well']}")


import helper_functions as hf
import pandas as pd
from ax.core.observation import ObservationFeatures

# --- BO initialization (unwrapped) ---
from ax.service.ax_client import AxClient
from ax.service.utils.instantiation import ObjectiveProperties

# from ax.adapter.registry import Generators
# from ax.generation_strategy.generation_node import GenerationStep
# from ax.generation_strategy.generation_strategy import GenerationStrategy

from ax.modelbridge import Models
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy


# Path / file constants (defined at top-level so helpers don't own file paths)
_SUFFIX = "_smoketest" if SMOKE_TEST else ""
OPTIMIZER_FILE_PATH = f"optimizer/optimizer{_SUFFIX}_"
RAW_DATA_FILE_PATH = f"raw_data/raw_absorbance{_SUFFIX}_"
DESIGN_FILE_PATH = f"optimizer/design{_SUFFIX}_"
SNAPSHOT_DIR = f"optimizer/snapshots{_SUFFIX}/"

# build generation strategy
gs = GenerationStrategy(
    steps=[
        # GenerationStep(
        #     model=Generators.SOBOL, num_trials=1000, model_kwargs={"seed": 0}
        # ),
        # GenerationStep(
        #     model=Models.BOTORCH_MODULAR, num_trials=-1, model_kwargs={}
        # ),  # faster, but less performant
        GenerationStep(
            model=Models.SAASBO, num_trials=-1, model_kwargs={}
        ),  # Use for production runs
    ]
)

# If a snapshot exists in SNAPSHOT_DIR, restore the latest one. Otherwise create new experiment.
# Dynamically determine n based on available raw absorbance CSV files

os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def determine_current_iteration():
    """Determine current iteration number n based on existing raw data files."""
    raw_data_pattern = RAW_DATA_FILE_PATH + "i*.csv"
    raw_data_files = glob.glob(raw_data_pattern)
    return len(raw_data_files)


n = determine_current_iteration()


# Restore AxClient from latest completed snapshot if available, else create new experiment
try:
    completed_snapshot_files = [
        os.path.join(SNAPSHOT_DIR, f)
        for f in os.listdir(SNAPSHOT_DIR)
        if f.endswith("_completed.json")
    ]
except FileNotFoundError:
    completed_snapshot_files = []

if completed_snapshot_files:
    latest = max(completed_snapshot_files, key=os.path.getmtime)
    print(f"Restoring AxClient from latest completed snapshot: {latest}")
    ax_client = AxClient.load_from_json_file(latest)
else:
    ax_client = AxClient(generation_strategy=gs)
    ax_client.create_experiment(
        name="drug_surfactant",
        parameters=[
            {
                "name": "s1",
                "type": "range",
                "bounds": [0.0, hf.surfactant_total_volume * 1000],
                "value_type": "float",
            },
            {
                "name": "s2",
                "type": "range",
                "bounds": [0.0, hf.surfactant_total_volume * 1000],
                "value_type": "float",
            },
            {
                "name": "s3",
                "type": "range",
                "bounds": [0.0, hf.surfactant_total_volume * 1000],
                "value_type": "float",
            },
            {
                "name": "s4",
                "type": "range",
                "bounds": [0.0, hf.surfactant_total_volume * 1000],
                "value_type": "float",
            },
            {
                "name": "s5",
                "type": "range",
                "bounds": [0.0, hf.surfactant_total_volume * 1000],
                "value_type": "float",
            },
            {
                "name": "s6",
                "type": "range",
                "bounds": [0.0, hf.surfactant_total_volume * 1000],
                "value_type": "float",
            },
            {
                "name": "s7",
                "type": "range",
                "bounds": [0.0, hf.surfactant_total_volume * 1000],
                "value_type": "float",
            },
            {
                "name": "s8",
                "type": "range",
                "bounds": [0.0, hf.surfactant_total_volume * 1000],
                "value_type": "float",
            },
            {
                "name": "drug",
                "type": "choice",
                "values": ["IBP", "LOV", "DCF", "GLV"],
                "value_type": "str",
            },
            # Derived / featurized drug properties (normalized) so acquisition can condition on them.
            {
                "name": "Drug_MW",
                "type": "range",
                "bounds": [0.0, 1.0],
                "value_type": "float",
            },
            {
                "name": "Drug_LogP",
                "type": "range",
                "bounds": [0.0, 1.0],
                "value_type": "float",
            },
            {
                "name": "Drug_TPSA",
                "type": "range",
                "bounds": [0.0, 1.0],
                "value_type": "float",
            },
        ],
        objectives={
            "obj_surf_conc": ObjectiveProperties(minimize=True),
        },
        parameter_constraints=[
            f"s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 <= {hf.surfactant_total_volume * 1000}",
        ],
        outcome_constraints=["absorbance <= 0.06"],
    )
    # persist initial optimizer state and a timestamped snapshot (only if newly created)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pending_snapshot_path = os.path.join(SNAPSHOT_DIR, f"{0}_{timestamp}_pending.json")
    ax_client.save_to_json_file(pending_snapshot_path)
# --- end BO initialization ---


WELL_POSITIONS_FILE = f"well_positions{'_smoketest' if SMOKE_TEST else ''}.json"

try:

    with open(WELL_POSITIONS_FILE, "r") as f:
        well_positions = json.load(f)
    prev_plate = well_positions.get("plate", hf.get_next_well("A1", offset=n))
    prev_deep = well_positions.get("deepplate", hf.get_next_well("A1", offset=n))
    #next_plate_default = hf.get_next_well(prev_plate, offset=1)
    #next_deep_default = hf.get_next_well(prev_deep, offset=1)
    #next_plate_default = hf.get_next_well(prev_plate)
    #next_deep_default = hf.get_next_well(prev_deep)
    next_plate_default = prev_plate
    next_deep_default = prev_deep
    print(
        f"Last saved plate well: {prev_plate}\nLast saved deepplate well: {prev_deep}"
    )
except (FileNotFoundError, json.JSONDecodeError):
    prev_plate = hf.get_next_well("A1", offset=n)
    prev_deep = hf.get_next_well("A1", offset=n)
    next_plate_default = prev_plate
    next_deep_default = prev_deep
    print("No previous well positions found.")

plate_input = input(
    f"Enter starting plate well (press Enter for {next_plate_default}): "
).strip()
deep_input = input(
    f"Enter starting deep plate well (press Enter for {next_deep_default}): "
).strip()
NEXT_PLATE_WELL = plate_input if plate_input else next_plate_default
NEXT_DEEPPLATE_WELL = deep_input if deep_input else next_deep_default


# Only update well positions file if user manually set a position
if plate_input or deep_input:
    with open(WELL_POSITIONS_FILE, "w") as f:
        json.dump({"plate": NEXT_PLATE_WELL, "deepplate": NEXT_DEEPPLATE_WELL}, f)
REPLICATES = 3

# # To update pipette tip location/ initiation ###################################################################################################################################################
# tip1000_well = input("Enter starting 1000uL TIP well (default A1): ").upper() or "A1"
# tip50_well = input("Enter starting 50uL TIP well (default A1): ").upper() or "A1"

#well_names_list = [f"{r}{c}" for c in range(1, 13) for r in "ABCDEFGH"]

TIP_STATE_FILE = "tip_positions.json"

try:
    with open(TIP_STATE_FILE, "r") as f:
        tip_state = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    tip_state = {"rack_id_1000": "0", "well_1000": "A1", "well_50": "A1"}

# # Manual tip location check and override
# print(f"\nRemembered 1000uL: Rack {tip_state['rack_id_1000']}, Well {tip_state['well_1000']}")
# print(f"Remembered 50uL:   Well {tip_state['well_50']}")

# user_1000_rack = input(f"Enter 1000uL Rack ID (Enter for {tip_state['rack_id_1000']}): ").strip()
# user_1000_well = input(f"Enter 1000uL Well (Enter for {tip_state['well_1000']}): ").strip().upper()
# user_50_well   = input(f"Enter 50uL Well (Enter for {tip_state['well_50']}): ").strip().upper()

# if user_1000_rack: tip_state["rack_id_1000"] = user_1000_rack
# if user_1000_well: tip_state["well_1000"] = user_1000_well
# if user_50_well:   tip_state["well_50"] = user_50_well

# --- SMART TIP SETUP (Press Enter for Default) ---
print("\n--- TIP SETUP ---")

# 1. 1000uL Rack
default_rack = tip_state.get('rack_id_1000', '0')
user_rack = input(f"Enter 1000uL Rack ID (0=Slot B1, 1=Slot A1) [Press Enter for {default_rack}]: ").strip()
tip_state["rack_id_1000"] = user_rack if user_rack else default_rack

# 2. 1000uL Well
default_1000 = tip_state.get('well_1000', 'A1')
user_1000 = input(f"Enter 1000uL Start Well [Press Enter for {default_1000}]: ").strip().upper()
tip_state["well_1000"] = user_1000 if user_1000 else default_1000

# 3. 50uL Well
default_50 = tip_state.get('well_50', 'A1')
user_50 = input(f"Enter 50uL Start Well [Press Enter for {default_50}]: ").strip().upper()
tip_state["well_50"] = user_50 if user_50 else default_50

# Save immediately
with open(TIP_STATE_FILE, "w") as f:
    json.dump(tip_state, f)

print(f"Confirmed Start: 1000uL @ Rack {tip_state['rack_id_1000']}:{tip_state['well_1000']} | 50uL @ {tip_state['well_50']}\n")

# Number of closed-loop batches to run in this iteration
NUM_BATCHES = 3 #change for amount of iterations you want to run
TRIALS_PER_ITERATION = 3  # number of samples per batch
#drug_choices = ["IBP", "LOV", "DCF", "GLV"]
drug_choices = ["IBP"] #to only test for IBP
surf_names = [f"s{i}" for i in range(1, 9)]


# Number of iterations to run
start_n = n 
for n in range(start_n, start_n + NUM_BATCHES):
    drug = drug_choices[n % len(drug_choices)]
    print(f"\n=== Starting Batch Iteration {n}/{NUM_BATCHES-1} for drug: {drug} ===")

    # 1) Generate recommendations
    
    # First, get the actual data from the optimizer
    data_so_far = ax_client.get_trials_data_frame()

    # If we have data, we must ensure the fixed properties exist for the helper function
    if not data_so_far.empty:
        for d_key, info in hf.normalize_drug_properties_dict.items():
            props = info['normalized_properties']
            # Map properties (MW, LogP, TPSA) to every row matching this drug
            mask = data_so_far['drug'] == d_key
            for col, val in props.items():
                data_so_far.loc[mask, col] = val
        
        # Now that columns are 'hydrated', this will work perfectly
        data_so_far = hf.add_drug_names(data_so_far)

    # Compute per-drug best surfactant concentration for dynamic constraint, only using successful experiments (absorbance <= 0.06)
    if not data_so_far.empty:
        drug_data = data_so_far[
            (data_so_far["drug"] == drug) & (data_so_far["absorbance"] <= 0.06)
        ]
        if not drug_data.empty:
            best_surf_conc = drug_data["obj_surf_conc"].min()
        else:
            best_surf_conc = hf.surfactant_total_volume * 1000
    else:
        best_surf_conc = hf.surfactant_total_volume * 1000

    print(f"Updated constraints for {drug}: s1+...+s8 <= {max(best_surf_conc - 2, 1)}")

    # Fixed drug amount for the campaign (µL).
    fixed_drug_amount_ul = hf.drug_total_volume * 1000
    candidate_resolution_ul = 5.0  # may generate a lot of combinations, can adjust
    dynamic_surf_upper_ul = float(max(best_surf_conc - 2, 1))
    dynamic_surf_upper_ul = min(
        dynamic_surf_upper_ul, hf.surfactant_total_volume * 1000
    )

    if dynamic_surf_upper_ul < 2 * candidate_resolution_ul:
        candidate_resolution_ul = max(1.0, dynamic_surf_upper_ul / 2.0)

    levels = np.arange(
        candidate_resolution_ul,
        dynamic_surf_upper_ul + candidate_resolution_ul,
        candidate_resolution_ul,
    )

    n_surf = len(surf_names)
    n_pairs = int(math.comb(n_surf, 2))
    n_levels = len(levels)
    print(
        f"Theoretical max number of candidates (without limiting based on best-so-far concentration) for {drug}: {n_pairs * n_levels * n_levels}. Proceeding with candidate generation.."
    )

    props = hf.normalize_drug_properties_dict[drug]["normalized_properties"]
    candidate_rows = []
    for i, j in itertools.combinations(range(n_surf), 2):
        v1s = levels
        for v1 in v1s:
            max_v2 = dynamic_surf_upper_ul - v1
            if max_v2 < candidate_resolution_ul:
                continue
            v2s = np.arange(
                candidate_resolution_ul,
                max_v2 + candidate_resolution_ul,
                candidate_resolution_ul,
            )
            # Vectorized creation of all (v1, v2) pairs for this surfactant pair
            n_pairs = len(v2s)
            arr = np.zeros((n_pairs, n_surf), dtype=float)
            arr[:, i] = v1
            arr[:, j] = v2s
            # Add drug and property columns
            df = pd.DataFrame(arr, columns=surf_names)
            df["drug"] = drug
            df["Drug_MW"] = float(props["Drug_MW"])
            df["Drug_LogP"] = float(props["Drug_LogP"])
            df["Drug_TPSA"] = float(props["Drug_TPSA"])
            candidate_rows.append(df)
    if candidate_rows:
        candidate_df = pd.concat(candidate_rows, ignore_index=True)
    else:
        candidate_df = pd.DataFrame(
            columns=surf_names + ["drug", "Drug_MW", "Drug_LogP", "Drug_TPSA"]
        )

    print(f"Generated {len(candidate_df)} candidate combinations for {drug}.")

    # Avoid suggesting points already evaluated (grid points match exactly).
    tried_keys = set()
    if not data_so_far.empty:
        needed_cols = surf_names + ["drug"]
        if all(col in data_so_far.columns for col in needed_cols):
            for _, r in data_so_far[needed_cols].iterrows():
                tried_keys.add(tuple([r[c] for c in needed_cols]))

    if tried_keys:
        candidate_df = candidate_df[
            ~candidate_df.apply(
                lambda r: tuple([r[c] for c in surf_names + ["drug"]]) in tried_keys,
                axis=1,
            )
        ]

    # trials_data = []
    # num_init = 4 if SMOKE_TEST else 12
    # if n + 1 <= num_init:
    #     rng = np.random.default_rng(n)
    #     sample_idx = int(rng.choice(len(candidate_df), size=1, replace=False)[0])
    #     chosen = candidate_df.iloc[[sample_idx]]

    trials_data = []
    chosen_rows = []

    num_init = 4 if SMOKE_TEST else 12

    if n + 1 <= num_init:
        rng = np.random.default_rng(n)
        sample_indices = rng.choice(
            len(candidate_df),
            size=TRIALS_PER_ITERATION,
            replace=False
        )
        chosen_rows = candidate_df.iloc[sample_indices]

    else:
        print("Fitting model..")
        ax_client.fit_model()
        model = ax_client.generation_strategy.model

        obs_feats = [
            ObservationFeatures(row.to_dict())
            for _, row in candidate_df.iterrows()
        ]
        acqf_vals = model.evaluate_acquisition_function(obs_feats)

        best_indices = np.argsort(acqf_vals)[-TRIALS_PER_ITERATION:]
        chosen_rows = candidate_df.iloc[best_indices]

    # else:
    #     print("Fitting model..")
    #     ax_client.fit_model()
    #     model = ax_client.generation_strategy.model
    #     # Evaluate acquisition function in batches to reduce memory usage
        import time

        acqf_batch_size = 1000  # Set your preferred batch size here
        acqf_list = []
        total = len(candidate_df)
        start = 0
        batch_num = 1
        batch_start_time = time.time()
        while start < total:
            end = min(start + acqf_batch_size, total)
            if batch_num in [
                1,
                2,
                4,
                8,
                16,
                32,
                64,
                128,
                256,
                512,
                1024,
                2048,
                4096,
                8192,
                16384,
            ]:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                elapsed = time.time() - batch_start_time
                print(
                    f"[{now}] Elapsed: {elapsed:7.2f}s | Processing acquisition function batch {batch_num} (rows {start}..{end-1})"
                )
            obs_feat_chunk = [
                ObservationFeatures(row.to_dict())
                for _, row in candidate_df.iloc[start:end].iterrows()
            ]
            vals = model.evaluate_acquisition_function(
                observation_features=obs_feat_chunk
            )
            acqf_list.extend(vals)
            start = end
            batch_num += 1
        acqf_values = np.array(acqf_list)
        best_index = int(np.argmax(acqf_values))
        chosen = candidate_df.iloc[[best_index]]

    # #ax_params = chosen.iloc[0].to_dict()
    # # Convert the chosen candidate to a dictionary for Ax
    # ax_params = chosen.iloc[0].to_dict()

    # # FIX: Inject drug properties to stop the KeyError: 'Drug_MW'
    # if drug in hf.normalize_drug_properties_dict:
    #     props = hf.normalize_drug_properties_dict[drug]['normalized_properties']
    #     ax_params.update(props)

    # _, trial_index = ax_client.attach_trial(ax_params)

    # obj_surf_conc = sum(ax_params[s] for s in surf_names)
    # print(f"Chosen surfactant concentrations for {drug}: {ax_params}")

    # # Add well_slot and plate_num to trial._properties
    # trial = ax_client.experiment.trials[trial_index]
    # trial._properties["well_slot"] = NEXT_PLATE_WELL
    # trial._properties["plate_num"] = 1  # Always 1 for now

    # drug_cols = {d: 0.0 for d in drug_choices}
    # drug_cols[drug] = float(fixed_drug_amount_ul)

    # trials_data.append(
    #     {
    #         "trial_index": trial_index,
    #         "drug_name": drug,
    #         **{k: ax_params[k] for k in surf_names},
    #         **drug_cols,
    #     }
    # )

    trial_indices = []

    for _, row in chosen_rows.iterrows():
        ax_params = row.to_dict()
        props = hf.normalize_drug_properties_dict[drug]["normalized_properties"]
        ax_params.update(props)

        _, trial_index = ax_client.attach_trial(ax_params)
        trial_indices.append(trial_index)

        trial = ax_client.experiment.trials[trial_index]
        # Assign unique wells to this trial inside the loop
        trial._properties["well_slot"] = NEXT_PLATE_WELL
        trial._properties["deep_well_slot"] = NEXT_DEEPPLATE_WELL
        trial._properties["plate_num"] = 1

        trials_data.append({
            "trial_index": trial_index,
            "drug_name": drug,
            "well_slot": NEXT_PLATE_WELL,
            "deep_well_slot": NEXT_DEEPPLATE_WELL,
            "rack_1000": tip_state["rack_id_1000"],
            "well_1000": tip_state["well_1000"],
            "well_50": tip_state["well_50"],
            "replicates": REPLICATES,          # Add this here!
            **{k: ax_params[k] for k in surf_names},
            "surf_conc": row.get('surf_conc', 0.0),
            "obj_surf_conc": "" 
        })
        
        print(f"Trial {trial_index} assigned to Plate: {NEXT_PLATE_WELL}, Deep: {NEXT_DEEPPLATE_WELL}")
        
        # INCREMENT: Move wells forward for the NEXT sample in this batch
        NEXT_PLATE_WELL = hf.get_next_well(NEXT_PLATE_WELL, offset=REPLICATES)
        NEXT_DEEPPLATE_WELL = hf.get_next_well(NEXT_DEEPPLATE_WELL, offset=2)

    df_design = pd.DataFrame(trials_data)
    df_design["surf_conc"] = sum(df_design[s] for s in surf_names)
    df_design["obj_surf_conc"] = None

    ax_client.save_to_json_file(OPTIMIZER_FILE_PATH + str(n) + ".json")
    df_design.to_csv(DESIGN_FILE_PATH + "i" + str(n) + ".csv", index=False)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pending_snapshot_file = os.path.join(SNAPSHOT_DIR, f"{n}_{ts}_pending.json")
    ax_client.save_to_json_file(pending_snapshot_file)

    df_design, df_vol = hf.design_to_vol(n, design_file_path=DESIGN_FILE_PATH)

# If surfactant volumes are zero, replace them with CSV-generated ones
    surf_names = [f"s{i}" for i in range(1, 9)]
    if df_vol[surf_names].sum(axis=1).iloc[0] == 0:
        print("Surf values zero — using CSV-generated volumes")
        # Correct: unpack the tuple again
        df_design, df_vol = hf.design_to_vol(n, design_file_path=DESIGN_FILE_PATH)

    # otflex_params = df_vol.drop(columns=["trial_index", "drug_name"]).to_dict(
    #     orient="records"
    # )[0]
    
    # otflex_params["next_plate_well"] = NEXT_PLATE_WELL
    # otflex_params["next_deepplate_well"] = NEXT_DEEPPLATE_WELL
    # otflex_params["replicates"] = REPLICATES
    
    # Take all samples in the batch, not just the first one [0]
    otflex_params = df_vol.drop(columns=["trial_index", "drug_name"]).to_dict(orient="records")
    
    for i, sample in enumerate(otflex_params):
        # Match the specific wells we saved for each trial in the list
        sample["next_plate_well"] = trials_data[i]["well_slot"]
        sample["next_deepplate_well"] = trials_data[i]["deep_well_slot"]
        sample["replicates"] = REPLICATES
        sample["rack_id_1000"] = tip_state["rack_id_1000"]
        sample["well_1000"] = tip_state["well_1000"]
        sample["well_50"] = tip_state["well_50"]
    # Update well position json right before running the robot
    with open(WELL_POSITIONS_FILE, "w") as f:
        json.dump(
            {
                "plate": NEXT_PLATE_WELL,
                "deepplate": NEXT_DEEPPLATE_WELL,
            },
            f,
        )
    # otflex_params["tip1000_well"] = tip1000_well
    # otflex_params["tip50_well"] = tip50_well

    # otflex_params["rack_id_1000"] = tip_state["rack_id_1000"]
    # otflex_params["well_1000"] = tip_state["well_1000"]
    # otflex_params["well_50"] = tip_state["well_50"]

    # # Use tip_state directly since it is the dictionary holding these strings
    # print("\n--- TIP USAGE PREVIEW ---")
    # print(f"1000uL Pipette starting at: Rack {tip_state['rack_id_1000']}, Well {tip_state['well_1000']}")
    # print(f"50uL Pipette starting at: Well {tip_state['well_50']}")
    # print("--------------------------\n")


    import time

    # 1. Convert the list of dictionaries (the batch) into a JSON string
    batch_json_str = json.dumps(otflex_params)

    # 2. Create ONE payload for the entire iteration
    # We use the tip state from the start; the robot will increment internally.
    run_payload = {
        "batch_json": batch_json_str,
        "iteration": n,
        "rack_id_1000": tip_state["rack_id_1000"],
        "well_1000": tip_state["well_1000"],
        "well_50": tip_state["well_50"],
        "replicates": REPLICATES,
        
        # These are just placeholders so the robot display doesn't show "null"
        "next_plate_well": otflex_params[0].get("next_plate_well", "Batch"),
        "next_deepplate_well": otflex_params[0].get("next_deepplate_well", "Batch")
    }

    # 3. Upload and Run ONCE
    print(f"--- Launching Batch {n} ({len(otflex_params)} trials) ---")
    run_otflex_iA(run_payload)
    
    # 4. Wait for the robot to finish the whole batch
    print("Batch running... Waiting 15 seconds for server cycle...")
    time.sleep(15)



    # raw_data_file = RAW_DATA_FILE_PATH + "i" + str(n) + ".csv"

    # df_absorbance = hf.process_absorbance(
    #     replicates=REPLICATES,
    #     threshold=0.06,
    #     raw_data_file_path=raw_data_file,
    # )

    # --- NEW SEARCH & RENAME LOGIC ---
    import glob
    import shutil
    

    # 1. Search for the file the robot just downloaded (wildcard handles the random ID)
    # This looks for any file starting with 'raw_absorbance' in the 'data/' folder
    possible_files = glob.glob("data/raw_absorbance*.csv")
    
    if not possible_files:
        raise FileNotFoundError(f"Robot finished, but no CSV found in the 'data/' folder for iteration {n}.")

    # 2. Identify the newest one
    latest_messy_file = max(possible_files, key=os.path.getctime)
    
    # 3. Define the clean name your helpers expect
    # This creates: raw_data/raw_absorbance_i0.csv
    clean_raw_data_path = f"raw_data/raw_absorbance_i{n}.csv"
    os.makedirs("raw_data", exist_ok=True)

    # 4. Move and Rename it
    shutil.move(latest_messy_file, clean_raw_data_path)
    print(f"DEBUG: Cleaned {latest_messy_file} -> {clean_raw_data_path}")

    # 5. Process the absorbance using the NEW CLEAN NAME
    df_absorbance = hf.process_absorbance(
        raw_data_file_path=clean_raw_data_path, 
        replicates=REPLICATES,
        threshold=0.06,
    )

    

    # #updating tips for next run
    # u1000 = 0
    # u50 = 0
    # for s in surf_names:
    #     vol = otflex_params.get(s, 0)
    #     if vol > 0:
    #         if vol <= 40: u50 += 1
    #         else: u1000 += 1
    # u1000 += 1 # Surfactant transfer (pipette_high)
    # u50 += 1   # Drug transfer (pipette_low)

    # tip1000_idx = (well_names_list.index(tip1000_well) + u1000)
    # tip50_idx = (well_names_list.index(tip50_well) + u50)
    # tip1000_well = well_names_list[tip1000_idx % 96]
    # tip50_well = well_names_list[tip50_idx % 96]
    

    # 1. Reset batch counters for this iteration
    high_used = 0
    low_used = 0

    # 2. Define components that require a tip in the deepwell preparation stage
    # Drug (180uL) and Water (550uL) are both > 40uL, so they will use high tips.
    Deepwell_component_list = [f"s{i}" for i in range(1, 9)] + ["water"] + [drug]
    
    # Store starting data for the viewer results file
    start_tips = f"1000uL:R{tip_state['rack_id_1000']}-{tip_state['well_1000']}, 50uL:{tip_state['well_50']}"
    start_well = trials_data[0]['well_slot']

    for sample in otflex_params:
        # Step A: 'make_drug_or_surfactant' stage
        # Count tips for surfactants, 550uL water, and 180uL drug
        high_used += sum(1 for s in Deepwell_component_list if float(sample.get(s, 0)) > 40)
        low_used += sum(1 for s in Deepwell_component_list if 0 < float(sample.get(s, 0)) <= 40)
        
        # Step B: 'make_exp' stage
        # Protocol uses 1 High tip and 1 Low tip to transfer mixtures to the final well plate
        high_used += 1
        low_used += 1

    # 3. Batch Overhead: +1 to each to ensure the counter starts on a fresh tip next time
    high_used += 1
    low_used += 1

    all_wells = [f"{r}{c}" for c in range(1, 13) for r in "ABCDEFGH"]

    # Update 1000uL Counter (Handles 2 racks B1 and A1)
    idx_1000 = all_wells.index(tip_state["well_1000"]) + high_used 
    if idx_1000 >= 96:
        tip_state["rack_id_1000"] = "1" # Move to tip1000_2
        tip_state["well_1000"] = all_wells[idx_1000 - 96]
    else:
        tip_state["well_1000"] = all_wells[idx_1000]

    # Update 50uL Counter (1 rack at B2)
    idx_50 = all_wells.index(tip_state["well_50"]) + low_used 
    tip_state["well_50"] = all_wells[idx_50 % 96] # Loops back to A1 if full

    # Save to JSON file so the next iteration starts correctly
    with open(TIP_STATE_FILE, "w") as f:
        json.dump(tip_state, f)
    
    # absorbance = df_absorbance.loc[ df_absorbance["well_slot"] == NEXT_PLATE_WELL, "absorbance"].values[0]

    # # ax_client.complete_trial(
    # #     trial_index, {"obj_surf_conc": obj_surf_conc, "absorbance": absorbance}
    # # )
    # for trial_index in trial_indices:
    #     ax_client.complete_trial(
    #         trial_index,
    #         {
    #             "obj_surf_conc": obj_surf_conc,
    #             "absorbance": absorbance
    #         }
    #     )

    for trial_index in trial_indices:
        # Look up the specific well we assigned to THIS trial
        this_well = ax_client.experiment.trials[trial_index]._properties["well_slot"]
        
        # Pull only the absorbance for that specific well from the result CSV
        absorbance = df_absorbance.loc[df_absorbance["well_slot"] == this_well, "absorbance"].values[0]
        
        # Calculate surf_conc for this trial
        trial_params = ax_client.experiment.trials[trial_index].arm.parameters
        trial_surf_conc = sum(trial_params[s] for s in surf_names)

        ax_client.complete_trial(
            trial_index,
            {"obj_surf_conc": trial_surf_conc, "absorbance": absorbance}
        )
        
    results = hf.build_results(n, df_absorbance, design_file_path=DESIGN_FILE_PATH)
    labeled_data = results.copy()
    
    # Mark failed trials as abandoned based on well_slot and absorbance results
    failed_wells = set(df_absorbance.loc[df_absorbance["success"] == 0, "well_slot"])
    absorbance_map = dict(zip(df_absorbance["well_slot"], df_absorbance["absorbance"]))
    for idx, trial in ax_client.experiment.trials.items():
        well = trial._properties.get("well_slot")
        absorbance_val = absorbance_map.get(well)
        if well in failed_wells:
            print(f"Marking trial {idx} as abandoned due to failed well: {well}")
            trial.mark_abandoned(unsafe=True)

    ax_client.save_to_json_file(OPTIMIZER_FILE_PATH + str(n) + "_loaded.json")

   # ============================================================
    # Viewer-only results table (NOT used by machine or optimizer)
    # ============================================================

    # Build Ax trial status table (viewer only)
    df_status = hf.ax_trial_status_dataframe(ax_client)

    # Merge status into experimental results (viewer only)
    viewer_results_with_status = results.merge(
        df_status,
        on="trial_index",
        how="left"
    )

    # Sort for readability
    viewer_results_with_status = viewer_results_with_status.sort_values("trial_index")

    # Add start/end metadata to the viewer results
    viewer_results_with_status["start_tips"] = start_tips
    viewer_results_with_status["end_tips"] = f"1000uL:R{tip_state['rack_id_1000']}-{tip_state['well_1000']}, 50uL:{tip_state['well_50']}"
    viewer_results_with_status["batch_start_well"] = start_well
    viewer_results_with_status["batch_end_well"] = NEXT_PLATE_WELL

    # Save using n_iter for clear file history
    os.makedirs("results", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    VIEWER_RESULTS_FILE = f"results/viewer_results_i{n}_{ts}.csv"
    viewer_results_with_status.to_csv(VIEWER_RESULTS_FILE, index=False)

    # Print for live inspection
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    print("\n=== Viewer-only results with Ax trial status ===")
    print(viewer_results_with_status.tail(10))
    print(f"\n[Viewer] Results saved to: {VIEWER_RESULTS_FILE}")

    # Explicitly prevent accidental downstream use
    del viewer_results_with_status


    # NEXT_PLATE_WELL = hf.get_next_well(NEXT_PLATE_WELL, offset= TRIALS_PER_ITERATION * REPLICATES) #* TOTAL_DRUGS) take out total drugs because we won't do different drugs in one iteration 
    # NEXT_DEEPPLATE_WELL = hf.get_next_well(NEXT_DEEPPLATE_WELL, offset= 2 * TRIALS_PER_ITERATION) # * TOTAL_DRUGS)


print(f"\nClosed-loop optimization completed. Ran from batch {start_n} to {n}.")

#to run terminal
    #conda activate drug-surfactant
    #cd experiments
    #python drug_surfactant_bo.py

    #if any of the raw_data files exist it considers their plate