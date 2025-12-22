import json
import os
import sys

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
                values = [f"{random.uniform(0.04, 0.12):.3f}" for _ in cols]
                f.write(f"{row}," + ",".join(values) + "\n")


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
        #     model=Generators.BOTORCH_MODULAR, num_trials=1000, model_kwargs={}
        # ),
        GenerationStep(model=Models.SAASBO, num_trials=-1, model_kwargs={}),
    ]
)

# If a snapshot exists in SNAPSHOT_DIR, restore the latest one. Otherwise create new experiment.
os.makedirs(SNAPSHOT_DIR, exist_ok=True)
snapshot_files = []

os.makedirs(SNAPSHOT_DIR, exist_ok=True)

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
    n = int(os.path.basename(latest).split("_")[0]) + 1
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
    )
    # persist initial optimizer state and a timestamped snapshot (only if newly created)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    n = 0
    pending_snapshot_path = os.path.join(SNAPSHOT_DIR, f"{n}_{timestamp}_pending.json")
    ax_client.save_to_json_file(pending_snapshot_path)
# --- end BO initialization ---


WELL_POSITIONS_FILE = f"well_positions{'_smoketest' if SMOKE_TEST else ''}.json"
try:
    with open(WELL_POSITIONS_FILE, "r") as f:
        well_positions = json.load(f)
    last_plate = well_positions.get("plate", hf.get_next_well("A1", offset=n))
    last_deep = well_positions.get("deepplate", hf.get_next_well("A1", offset=n))
    print(
        f"Last saved plate well: {last_plate}\nLast saved deepplate well: {last_deep}"
    )
except (FileNotFoundError, json.JSONDecodeError):
    last_plate = hf.get_next_well("A1", offset=n)
    last_deep = hf.get_next_well("A1", offset=n)
    print("No previous well positions found.")

plate_input = input(
    f"Enter starting plate well (press Enter for {last_plate}): "
).strip()
deep_input = input(
    f"Enter starting deep plate well (press Enter for {last_deep}): "
).strip()
NEXT_PLATE_WELL = plate_input if plate_input else last_plate
NEXT_DEEPPLATE_WELL = deep_input if deep_input else last_deep

# Save chosen positions for next run
with open(WELL_POSITIONS_FILE, "w") as f:
    json.dump({"plate": NEXT_PLATE_WELL, "deepplate": NEXT_DEEPPLATE_WELL}, f)
REPLICATES = 1


# Number of closed-loop batches to run in this iteration
NUM_BATCHES = 3
drug_choices = ["IBP", "LOV", "DCF", "GLV"]
surf_names = [f"s{i}" for i in range(1, 9)]


# Interleaved round-robin drug selection for each trial
total_trials = NUM_BATCHES * len(drug_choices)
for trial in range(total_trials):
    drug = drug_choices[trial % len(drug_choices)]
    print(f"\n=== Starting experiment {trial + 1}/{total_trials} for drug: {drug} ===")

    # 1) Generate recommendations (inlined from helper_functions.run_optimizer)
    data_so_far = pd.DataFrame()
    if n > 0:
        data_so_far = ax_client.get_trials_data_frame()
        data_so_far = hf.add_drug_names(data_so_far)

    # Compute per-drug best surfactant concentration for dynamic constraint
    if not data_so_far.empty and "drug" in data_so_far.columns:
        drug_data = data_so_far[data_so_far["drug"] == drug]
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

    trials_data = []
    num_init = 8
    if n <= num_init and (
        data_so_far.empty or data_so_far["obj_surf_conc"].notna().sum() < 2
    ):
        rng = np.random.default_rng(n)
        sample_idx = int(rng.choice(len(candidate_df), size=1, replace=False)[0])
        chosen = candidate_df.iloc[[sample_idx]]
    else:
        ax_client.fit_model()
        model = ax_client.generation_strategy.model
        obs_feat = [
            ObservationFeatures(row.to_dict()) for _, row in candidate_df.iterrows()
        ]
        acqf_values = np.array(
            model.evaluate_acquisition_function(observation_features=obs_feat)
        )
        best_index = int(np.argmax(acqf_values))
        chosen = candidate_df.iloc[[best_index]]

    ax_params = chosen.iloc[0].to_dict()
    _, trial_index = ax_client.attach_trial(ax_params)

    # Add well_slot and plate_num to trial._properties
    trial = ax_client.experiment.trials[trial_index]
    trial._properties["well_slot"] = NEXT_PLATE_WELL
    trial._properties["plate_num"] = 1  # Always 1 for now

    drug_cols = {d: 0.0 for d in drug_choices}
    drug_cols[drug] = float(fixed_drug_amount_ul)

    trials_data.append(
        {
            "trial_index": trial_index,
            "drug_name": drug,
            **{k: ax_params[k] for k in surf_names},
            **drug_cols,
        }
    )

    df_design = pd.DataFrame(trials_data)
    df_design["surf_conc"] = sum(df_design[s] for s in surf_names)
    df_design["obj_surf_conc"] = None

    ax_client.save_to_json_file(OPTIMIZER_FILE_PATH + str(n) + ".json")
    df_design.to_csv(DESIGN_FILE_PATH + "i" + str(n) + ".csv", index=False)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pending_snapshot_file = os.path.join(SNAPSHOT_DIR, f"{n}_{ts}_pending.json")
    ax_client.save_to_json_file(pending_snapshot_file)

    df_design, df_vol = hf.design_to_vol(n, design_file_path=DESIGN_FILE_PATH)

    otflex_params = df_vol.drop(columns=["trial_index", "drug_name"]).to_dict(
        orient="records"
    )[0]
    otflex_params["next_plate_well"] = NEXT_PLATE_WELL
    otflex_params["next_deepplate_well"] = NEXT_DEEPPLATE_WELL
    otflex_params["replicates"] = REPLICATES

    run_otflex_iA(otflex_params)

    raw_data_file = RAW_DATA_FILE_PATH + "i" + str(n) + ".csv"
    df_absorbance = hf.process_absorbance(
        replicates=REPLICATES,
        threshold=0.06,
        raw_data_file_path=raw_data_file,
    )
    results = hf.build_results(n, df_absorbance, design_file_path=DESIGN_FILE_PATH)
    labeled_data = results.copy()

    # Mark failed trials as abandoned based on well_slot and absorbance results
    # See: https://github.com/facebook/Ax/issues/2931#issuecomment-2432821274
    # For every trial in ax_client, if its well_slot matches a failed well in df_absorbance, mark as abandoned
    failed_wells = set(df_absorbance.loc[df_absorbance["success"] == 0, "well_slot"])
    for idx, trial in ax_client.experiment.trials.items():
        well = trial._properties.get("well_slot")
        if well in failed_wells:
            trial.mark_abandoned(unsafe=True)

    ax_client.save_to_json_file(OPTIMIZER_FILE_PATH + str(n) + "_loaded.json")

    # Save a completed snapshot after trial completion
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    completed_snapshot_file = os.path.join(
        SNAPSHOT_DIR, f"{n}_loaded_{timestamp}_completed.json"
    )
    ax_client.save_to_json_file(completed_snapshot_file)

    NEXT_PLATE_WELL = hf.get_next_well(NEXT_PLATE_WELL, offset=1)
    NEXT_DEEPPLATE_WELL = hf.get_next_well(NEXT_DEEPPLATE_WELL, offset=1)

print(
    f"\nClosed-loop optimization for iteration {n} completed with {NUM_BATCHES} batches."
)
