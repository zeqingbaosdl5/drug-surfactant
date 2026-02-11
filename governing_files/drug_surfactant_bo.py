import json
import os
import sys
import glob
import itertools
import numpy as np
import math
import time
import threading
from datetime import datetime

# --- SETUP PATHS ---
REPO_DIR = os.path.dirname(__file__)
sys.path.append(REPO_DIR)
PROJECT_ROOT = os.path.dirname(REPO_DIR)

# --- CONFIG ---
SMOKE_TEST = str(os.getenv("SMOKE_TEST", "")).strip().lower() in {"1", "true"}
BASE_URL = os.getenv("OPENTRONS_BASE_URL", "http://192.168.0.5:31950")
absorbance_threshold = float(os.getenv("ABSORBANCE_THRESHOLD"))

# --- EXPERIMENT FOLDER SELECTION ---
if not SMOKE_TEST:
    print(f"📂 Project Root: {PROJECT_ROOT}")
    
    # Try to get from environment first (e.g. from UI), fallback to manual input
    folder_input = os.getenv("EXP_FOLDER_NAME", "").strip()
    if not folder_input:
        folder_input = input("Enter experiment folder name (e.g., 20261129_test): ").strip()

    if not folder_input:
        raise ValueError("❌ Error: Experiment folder name is required.")
    
    EXP_PATH = os.path.join(PROJECT_ROOT, folder_input)
    if not os.path.isdir(EXP_PATH):
        raise FileNotFoundError(f"❌ Error: Folder not found: {EXP_PATH}\nPlease create it first with required subfolders (optimizer, protocols, raw_data, results).")
    
    print(f"✅ Using Experiment Folder: {EXP_PATH}")
else:
    # In smoke test, verify or create a dummy folder to avoid cluttering root
    EXP_PATH = os.path.join(PROJECT_ROOT, "smoketest_output")
    os.makedirs(EXP_PATH, exist_ok=True)
    print(f"⚠️  SMOKE TEST: Using folder {EXP_PATH}")

# --- IMPORTS ---
import helper_functions as hf
import pandas as pd
from ax.core.observation import ObservationFeatures
from ax.service.ax_client import AxClient
from ax.service.utils.instantiation import ObjectiveProperties
from ax.modelbridge import Models
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy

# ==========================================
#    CRITICAL SMOKE TEST LOGIC
# ==========================================
if SMOKE_TEST:
    print("⚠️  RUNNING IN SMOKE TEST MODE (No Robot Connection) ⚠️")
    
    def run_otflex_iA(protocol_file_path):
        print(f"[SMOKE] Pretending to upload & run: {os.path.basename(protocol_file_path)}")
        return "dummy_run_id_123"

    def get_run_details(base_url, run_id):
        return {
            "data": {
                "id": run_id,
                "status": "succeeded",
                "outputFileIds": ["dummy_file_id_999"]
            }
        }

    def download_data_file(base_url, file_id, save_path):
        print(f"[SMOKE] Generating absorbance linked to s1-s8 -> {save_path}")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        rows = [chr(ord("A") + i) for i in range(8)]
        cols = [str(i) for i in range(1, 13)]
        plate = np.full((8, 12), float(absorbance_threshold) * 1.2, dtype=float)

        iteration = None
        base = os.path.basename(save_path)
        if "_i" in base and base.endswith(".csv"):
            try:
                iteration = int(base.split("_i")[-1].split(".csv")[0])
            except ValueError:
                iteration = None

        design_path = None
        if iteration is not None:
            design_path = DESIGN_FILE_PATH + f"i{iteration}.csv"

        if design_path and os.path.exists(design_path):
            df_design = pd.read_csv(design_path)
            s_cols = [f"s{i}" for i in range(1, 9)]

            for _, row in df_design.iterrows():
                s_vals = {c: float(row[c]) for c in s_cols}
                total_vol = float(sum(s_vals.values()))
                s1 = s_vals["s1"]; s2 = s_vals["s2"]; s3 = s_vals["s3"]; s4 = s_vals["s4"]
                s5 = s_vals["s5"]; s6 = s_vals["s6"]; s7 = s_vals["s7"]; s8 = s_vals["s8"]
                if s6 != 0:
                    base_abs = 0.3 * s1 + 0.2 * s2 - 0.4 * s3 + (s4 * s5 - 100 * s6) + s8
                else:
                    base_abs = 0.3 * s1 + 0.2 * s2 - 0.4 * s3 + s8

                seed = int((total_vol + base_abs) * 1000) % (2**32)
                rng = np.random.default_rng(seed)

                curr = row["well_slot"]
                for _ in range(REPLICATES):
                    row_letter = curr[0]
                    col_num = int(curr[1:])
                    r_idx = ord(row_letter) - ord("A")
                    c_idx = col_num - 1
                    val = float(base_abs + rng.normal(0, 0.002))
                    val = max(0.0, min(0.2, val))
                    plate[r_idx, c_idx] = val
                    curr = hf.get_next_well(curr)

        with open(save_path, "w", newline="") as f:
            f.write("," + ",".join(cols) + "\n")
            for i, row in enumerate(rows):
                values = [f"{plate[i, j]:.3f}" for j in range(12)]
                f.write(f"{row}," + ",".join(values) + "\n")

else:
    print("✅ Running with REAL ROBOT execution.")
    from opentrons_http_otflex_iA_mwe import run_otflex_iA
    from opentrons_http_client import get_run_details, download_data_file


# --- FILE CONSTANTS ---
_SUFFIX = "_smoketest" if SMOKE_TEST else ""
OPTIMIZER_FILE_PATH = os.path.join(EXP_PATH, f"optimizer/optimizer{_SUFFIX}_")
RAW_DATA_FILE_PATH = os.path.join(EXP_PATH, f"raw_data/raw_absorbance{_SUFFIX}_")
DESIGN_FILE_PATH = os.path.join(EXP_PATH, f"optimizer/design{_SUFFIX}_")
SNAPSHOT_DIR = os.path.join(EXP_PATH, f"optimizer/snapshots{_SUFFIX}/")

# --- AX INITIALIZATION ---
gs = GenerationStrategy(
    steps=[
        # GenerationStep(
        #     model=Models.SAASBO,
        #     num_trials=1000,  
        #     model_kwargs={}
        # ),
        GenerationStep(
            model=Models.BOTORCH_MODULAR,
            num_trials=-1, 
            model_kwargs={}
        )
    ]
)
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

def determine_current_iteration():
    raw_data_pattern = RAW_DATA_FILE_PATH + "i*.csv"
    raw_data_files = glob.glob(raw_data_pattern)
    return len(raw_data_files)

n = determine_current_iteration()

# FIX: Look for *_loaded.json files in the optimizer folder (saved by main loop)
loaded_files_pattern = OPTIMIZER_FILE_PATH + "*_loaded.json"
completed_snapshot_files = glob.glob(loaded_files_pattern)

if completed_snapshot_files:
    latest = max(completed_snapshot_files, key=os.path.getmtime)
    print(f"✅ Detected saved optimizer state: {os.path.basename(latest)}")
    print(f"   Resuming from iteration i{n}")
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore") 
        ax_client = AxClient.load_from_json_file(latest, verbose_logging=False)
else:
    print("ℹ️  No saved optimizer state found. Starting fresh from i0.")
    ax_client = AxClient(generation_strategy=gs, verbose_logging=False)
    ax_client.create_experiment(
        name="drug_surfactant",
        parameters=[
            { "name": "s1", "type": "range", "bounds": [0.0, hf.surfactant_total_volume * 1000], "value_type": "float" },
            { "name": "s2", "type": "range", "bounds": [0.0, hf.surfactant_total_volume * 1000], "value_type": "float" },
            { "name": "s3", "type": "range", "bounds": [0.0, hf.surfactant_total_volume * 1000], "value_type": "float" },
            { "name": "s4", "type": "range", "bounds": [0.0, hf.surfactant_total_volume * 1000], "value_type": "float" },
            { "name": "s5", "type": "range", "bounds": [0.0, hf.surfactant_total_volume * 1000], "value_type": "float" },
            { "name": "s6", "type": "range", "bounds": [0.0, hf.surfactant_total_volume * 1000], "value_type": "float" },
            { "name": "s7", "type": "range", "bounds": [0.0, hf.surfactant_total_volume * 1000], "value_type": "float" },
            { "name": "s8", "type": "range", "bounds": [0.0, hf.surfactant_total_volume * 1000], "value_type": "float" },
            { "name": "drug", "type": "choice", "values": ["IBP", "LOV", "DCF", "GLV"], "value_type": "str" , "is_ordered": False, "sort_values": False},
            #{ "name": "Drug_MW", "type": "range", "bounds": [0.0, 1.0], "value_type": "float" },
            #{ "name": "Drug_LogP", "type": "range", "bounds": [0.0, 1.0], "value_type": "float" },
            #{ "name": "Drug_TPSA", "type": "range", "bounds": [0.0, 1.0], "value_type": "float" },
        ],
        objectives={
            "obj_total_vol": ObjectiveProperties(minimize=True),
        },
        parameter_constraints=[
            f"s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 <= {hf.surfactant_total_volume * 1000}",
        ],
        outcome_constraints=[f"absorbance <= {absorbance_threshold}"],
    )
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ax_client.save_to_json_file(os.path.join(SNAPSHOT_DIR, f"{0}_{ts}_pending.json"))

# --- WELL STATE ---
WELL_POSITIONS_FILE = os.path.join(EXP_PATH, f"well_positions{_SUFFIX}.json")
try:
    with open(WELL_POSITIONS_FILE, "r") as f:
        well_positions = json.load(f)
    prev_plate = well_positions.get("plate", hf.get_next_well("A1", offset=n))
    prev_deep = well_positions.get("deepplate", hf.get_next_well("A1", offset=n))
except (FileNotFoundError, json.JSONDecodeError):
    prev_plate = hf.get_next_well("A1", offset=n)
    prev_deep = hf.get_next_well("A1", offset=n)

if not SMOKE_TEST:
    print(f"Last saved: Plate {prev_plate}, Deep {prev_deep}")
    
    # Try getting from Env (UI) first, else prompt
    plate_input = os.getenv("START_PLATE_WELL")
    if plate_input is None:
        plate_input = input(f"Enter starting plate well (Enter for {prev_plate}): ").strip()
    else:
        plate_input = plate_input.strip()

    deep_input = os.getenv("START_DEEP_WELL")
    if deep_input is None:
        deep_input = input(f"Enter starting deep plate well (Enter for {prev_deep}): ").strip()
    else:
        deep_input = deep_input.strip()
else:
    plate_input, deep_input = "", ""

NEXT_PLATE_WELL = plate_input if plate_input else prev_plate
NEXT_DEEPPLATE_WELL = deep_input if deep_input else prev_deep

if plate_input or deep_input:
    with open(WELL_POSITIONS_FILE, "w") as f:
        json.dump({"plate": NEXT_PLATE_WELL, "deepplate": NEXT_DEEPPLATE_WELL}, f)

# --- TIP STATE ---
TIP_STATE_FILE = os.path.join(EXP_PATH, f"tip_positions{_SUFFIX}.json")

try:
    with open(TIP_STATE_FILE, "r") as f:
        tip_state = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    tip_state = {"rack_id_1000": "0", "well_1000": "A1", "well_50": "A1"}

if not SMOKE_TEST:
    print("\n--- TIP SETUP ---")
    
    # Check Env vars (UI) first, else prompt
    u_rack = os.getenv("TIP_RACK_ID")
    if u_rack is None:
        u_rack = input(f"Enter 1000uL Rack ID (0/1) [Enter for {tip_state.get('rack_id_1000','0')}]: ").strip()
    else:
        u_rack = u_rack.strip()

    u_1000 = os.getenv("TIP_WELL_1000")
    if u_1000 is None:
        u_1000 = input(f"Enter 1000uL Well [Enter for {tip_state.get('well_1000','A1')}]: ").strip().upper()
    else:
        u_1000 = u_1000.strip().upper()
        
    u_50 = os.getenv("TIP_WELL_50")
    if u_50 is None:
        u_50 = input(f"Enter 50uL Well [Enter for {tip_state.get('well_50','A1')}]: ").strip().upper()
    else:
        u_50 = u_50.strip().upper()

    if u_rack: tip_state["rack_id_1000"] = u_rack
    if u_1000: tip_state["well_1000"] = u_1000
    if u_50: tip_state["well_50"] = u_50
    with open(TIP_STATE_FILE, "w") as f: json.dump(tip_state, f)

print(f"Iteration Start Tips: 1000uL @ R{tip_state['rack_id_1000']}:{tip_state['well_1000']} | 50uL @ {tip_state['well_50']}")

# --- MAIN LOOP ---
NUM_ITERATIONS = int(os.getenv("NUM_ITERATIONS"))
TRIALS_PER_ITERATION = int(os.getenv("TRIALS_PER_ITERATION"))
REPLICATES = int(os.getenv("REPLICATES"))
surfactant_volume_reduction_per = float(os.getenv("SURFACTANT_VOL_REDUCTION"))
drug_choices_str = os.getenv("DRUG_CHOICES")
drug_choices = [d.strip() for d in drug_choices_str.split(",")]
absorbance_threshold = float(os.getenv("ABSORBANCE_THRESHOLD"))
num_random_trials = int(os.getenv("NUM_RANDOM_TRIALS"))
PUNISHMENT_FACTOR = int(os.getenv("PUNISHMENT_FACTOR"))
DELAY_TIME = os.getenv("DELAY_TIME", "5")


surf_names = [f"s{i}" for i in range(1, 9)]

# --- LOG PARAMETERS ---
import csv
param_log_csv = os.path.join(EXP_PATH, f"experiment_parameters{_SUFFIX}.csv")
curr_params = {
    "NUM_ITERATIONS": NUM_ITERATIONS,
    "TRIALS_PER_ITERATION": TRIALS_PER_ITERATION,
    "REPLICATES": REPLICATES,
    "SURFACTANT_VOL_REDUCTION (%)": surfactant_volume_reduction_per,
    "DRUG_CHOICES": drug_choices_str,
    "ABSORBANCE_THRESHOLD": absorbance_threshold,
    "NUM_RANDOM_TRIALS": num_random_trials,
    "PUNISHMENT_FACTOR": PUNISHMENT_FACTOR,
    "DELAY_TIME": DELAY_TIME,
}
with open(param_log_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Variable Name", "Value"])
    for k, v in curr_params.items():
        writer.writerow([k, v])



start_n = n 
import logging
logging.getLogger("ax.core.observation").setLevel(logging.CRITICAL)
logging.getLogger("ax.core.trial").setLevel(logging.CRITICAL)
logging.getLogger("ax.core.experiment").setLevel(logging.CRITICAL)
logging.getLogger("ax.service.utils.report_utils").setLevel(logging.CRITICAL) # Add this line

for n in range(start_n, start_n + NUM_ITERATIONS):
    drug = drug_choices[n % len(drug_choices)]
    print(f"\n=== Starting Iteration {n} for drug: {drug} ===")

    # 1. Update Constraints
    data_so_far = ax_client.get_trials_data_frame()
    if not data_so_far.empty:
        for d_key, info in hf.normalize_drug_properties_dict.items():
            mask = data_so_far['drug'] == d_key
            for col, val in info['normalized_properties'].items():
                data_so_far.loc[mask, col] = val
        data_so_far = hf.add_drug_names(data_so_far)

    best_total_vol = hf.surfactant_total_volume * 1000

    
    if not data_so_far.empty:
        drug_data = data_so_far[(data_so_far["drug"] == drug) & (data_so_far["absorbance"] <= absorbance_threshold)]
        drug_data = drug_data[drug_data["drug"] == drug]
        if not drug_data.empty:
            best_total_vol = drug_data["obj_total_vol"].min()


    surfactant_volume_reduction = best_total_vol * ( surfactant_volume_reduction_per / 100.0)
    print(f"Updated constraints for {drug}: s1+...+s8 <= {max(best_total_vol - surfactant_volume_reduction, 1)} uL")

    # 2. Candidate Generation
    fixed_drug_ul = hf.drug_total_volume * 1000
    resolution = 5.0  #Volume will be generated as an interval of 5 uL
    upper_lim = min(float(max(best_total_vol - surfactant_volume_reduction, 1)), hf.surfactant_total_volume * 1000)
    if upper_lim < 2 * resolution: resolution = max(1.0, upper_lim / 2.0)

    levels = np.arange(resolution, upper_lim + resolution, resolution)
    props = hf.normalize_drug_properties_dict[drug]["normalized_properties"]
    
    candidate_rows = []
    for i, j in itertools.combinations(range(len(surf_names)), 2):
        v1s = levels
        for v1 in v1s:
            max_v2 = upper_lim - v1
            if max_v2 < resolution: continue
            v2s = np.arange(resolution, max_v2 + resolution, resolution)
            arr = np.zeros((len(v2s), len(surf_names)), dtype=float)
            arr[:, i] = v1
            arr[:, j] = v2s
            df = pd.DataFrame(arr, columns=surf_names)
            df["drug"] = drug
            df["pair"] = f"{i}-{j}"
            for k,v in props.items(): df[k] = float(v)
            candidate_rows.append(df)
    
    candidate_df = pd.concat(candidate_rows, ignore_index=True) if candidate_rows else pd.DataFrame(columns=surf_names + ["drug"])#, "Drug_MW", "Drug_LogP", "Drug_TPSA"])
    print(f"Generated {len(candidate_df)} candidates.")

    if not data_so_far.empty:
        needed = surf_names + ["drug"]
        if all(c in data_so_far.columns for c in needed):
            tried = set(tuple(r) for r in data_so_far[needed].to_numpy())
            candidate_df = candidate_df[~candidate_df[needed].apply(tuple, axis=1).isin(tried)]

    candidate_df = candidate_df.reset_index(drop=True)

    # 3. Model Prediction
    if n == 0: #only iteration 0 is randomly generated
        sample_indices = np.random.default_rng(n).choice(len(candidate_df), size=num_random_trials, replace=False)
        chosen_rows = candidate_df.iloc[sample_indices]
    else:
        # Define timer function to run in background
        def timer_counter(stop_event):
            count = 0
            while not stop_event.is_set():
                sys.stdout.write(f"\r⏳ Model computing... {count} min")
                sys.stdout.flush()
                time.sleep(60)
                count += 1
            sys.stdout.write("\n")

        print("Fitting model...")
        stop_timer = threading.Event()
        t_thread = threading.Thread(target=timer_counter, args=(stop_timer,))
        t_thread.start()
        start_time = time.time()

        try:
            import logging
            # Suppress Ax warnings/info about untracked metrics from all relevant modules
            logging.getLogger("ax.core.observation").setLevel(logging.CRITICAL)
            logging.getLogger("ax.core.trial").setLevel(logging.CRITICAL)
            logging.getLogger("ax.core.experiment").setLevel(logging.CRITICAL)
            ax_client.fit_model()
            model = ax_client.generation_strategy.model
            acqf_vals = []
            for start in range(0, len(candidate_df), 1000):
                chunk = candidate_df.iloc[start:start+1000]
                obs = [ObservationFeatures(r.to_dict()) for _, r in chunk.iterrows()]
                acqf_vals.extend(model.evaluate_acquisition_function(obs))
            # Group by pair and find best idx per pair
            pair_best = {}
            for pos, (idx, row) in enumerate(candidate_df.iterrows()):
                pair = row["pair"]
                acqf = acqf_vals[pos]
                if pair not in pair_best or acqf > pair_best[pair][1]:
                    pair_best[pair] = (idx, acqf)
            # Get list of best idx per pair
            best_per_pair = [idx for idx, _ in pair_best.values()]
            # Sort by acqf descending
            best_per_pair_sorted = sorted(best_per_pair, key=lambda idx: acqf_vals[idx], reverse=True)
            # Select top TRIALS_PER_ITERATION with no overlapping surfactants
            used_indices = set()
            selected_indices = []
            for idx in best_per_pair_sorted:
                if len(selected_indices) >= TRIALS_PER_ITERATION:
                    break
                row = candidate_df.iloc[idx]
                pair = row["pair"]
                i, j = map(int, pair.split('-'))
                if i not in used_indices and j not in used_indices:
                    selected_indices.append(idx)
                    used_indices.add(i)
                    used_indices.add(j)
            chosen_rows = candidate_df.iloc[selected_indices]
        finally:
            stop_timer.set()
            t_thread.join()

        print(f"✅ Model computation done in {time.time() - start_time:.2f}s")

    # 4. Trial Registration
    trial_indices = []
    trials_data = []
    
    for _, row in chosen_rows.iterrows():
        params = {k: v for k, v in row.to_dict().items() if k != 'pair'}
        params.update(props)
        _, tid = ax_client.attach_trial(params)
        trial_indices.append(tid)
        
        trial = ax_client.experiment.trials[tid]
        trial._properties["well_slot"] = NEXT_PLATE_WELL
        trial._properties["deep_well_slot"] = NEXT_DEEPPLATE_WELL
        trial._properties["plate_num"] = 1

        trials_data.append({
            "trial_index": tid, "drug_name": drug,
            "well_slot": NEXT_PLATE_WELL, "deep_well_slot": NEXT_DEEPPLATE_WELL,
            # We record iteration Start Tips here (used for generating protocol)
            "rack_1000": tip_state["rack_id_1000"], "well_1000": tip_state["well_1000"], "well_50": tip_state["well_50"],
            "replicates": REPLICATES,
            **{k: params[k] for k in surf_names},
            "total_vol": sum(params[s] for s in surf_names),
            "obj_total_vol": "" 
        })
        NEXT_PLATE_WELL = hf.get_next_well(NEXT_PLATE_WELL, offset=REPLICATES)
        NEXT_DEEPPLATE_WELL = hf.get_next_well(NEXT_DEEPPLATE_WELL, offset=2)

    df_design = pd.DataFrame(trials_data)
    df_design["obj_total_vol"] = None
    ax_client.save_to_json_file(OPTIMIZER_FILE_PATH + str(n) + ".json")
    df_design.to_csv(DESIGN_FILE_PATH + "i" + str(n) + ".csv", index=False)
    
    # 5. Volume Calculation & TIP TRACKING
    _, df_vol = hf.design_to_vol(n, design_file_path=DESIGN_FILE_PATH)
    otflex_params = df_vol.drop(columns=["trial_index", "drug_name"]).to_dict(orient="records")
    
    for i, sample in enumerate(otflex_params):
        sample.update({
            "next_plate_well": trials_data[i]["well_slot"],
            "next_deepplate_well": trials_data[i]["deep_well_slot"],
            "replicates": REPLICATES,
        })

    with open(WELL_POSITIONS_FILE, "w") as f:
        json.dump({"plate": NEXT_PLATE_WELL, "deepplate": NEXT_DEEPPLATE_WELL}, f)

    # --- 6. GENERATE PROTOCOL ---
    import json
    template_path = os.path.join(REPO_DIR, "protocol_template.py")
    with open(template_path, "r") as f: template_str = f.read()

    protocol_content = template_str.format(
        ITERATION=n,
        RACK_ID_1000=str(tip_state["rack_id_1000"]), 
        WELL_1000=tip_state["well_1000"],
        WELL_50=tip_state["well_50"],
        START_PLATE_WELL=otflex_params[0]["next_plate_well"],
        START_DEEP_WELL=otflex_params[0]["next_deepplate_well"],
        REPLICATES=REPLICATES,
        DATA_JSON=json.dumps(otflex_params, indent=4),
        DELAY_TIME=DELAY_TIME
    )

    proto_path = os.path.join(EXP_PATH, "protocols", f"otflex{_SUFFIX}_i{n}.py")
    os.makedirs(os.path.dirname(proto_path), exist_ok=True)
    with open(proto_path, "w") as f: f.write(protocol_content)
    print(f"Generated Protocol: {proto_path}")

    # --- 7. EXECUTE & DOWNLOAD ---
    print(f"Launching Iteration {n}...")
    run_id = run_otflex_iA(proto_path)
    if not SMOKE_TEST: time.sleep(5) 

    clean_raw_path = os.path.join(EXP_PATH, "raw_data", f"raw_absorbance{_SUFFIX}_i{n}.csv")
    os.makedirs(os.path.dirname(clean_raw_path), exist_ok=True)
    
    run_details = get_run_details(BASE_URL, run_id)
    out_ids = run_details.get("data", {}).get("outputFileIds", [])
    
    if out_ids:
        print(f"Downloading result (ID: {out_ids[0]})...")
        download_data_file(BASE_URL, out_ids[0], clean_raw_path)
        print(f"Saved to: {clean_raw_path}")
    else:
        print("[WARN] No output file ID found!")

    # 8. Process Data & Update Tips
    # --- UPDATED: Passing trials_data so it knows which wells to check! ---
    df_absorbance = hf.process_absorbance(clean_raw_path, trials_data, replicates=REPLICATES, threshold=absorbance_threshold)
    
    comp_list = [f"s{i}" for i in range(1, 9)] + ["water"] + [drug]
    high, low = 0, 0
    for sample in otflex_params:
        high += sum(1 for s in comp_list if float(sample.get(s, 0)) > 40)
        low += sum(1 for s in comp_list if 0 < float(sample.get(s, 0)) <= 40)
        high += 1; low += 1
    
    all_wells = [f"{r}{c}" for c in range(1, 13) for r in "ABCDEFGH"]
    
    idx_1000 = all_wells.index(tip_state["well_1000"]) + high 
    if idx_1000 >= 96:
        tip_state["rack_id_1000"] = str(1 - int(tip_state["rack_id_1000"]))
        tip_state["well_1000"] = all_wells[idx_1000 - 96]
    else:
        tip_state["well_1000"] = all_wells[idx_1000]
        
    idx_50 = all_wells.index(tip_state["well_50"]) + low
    tip_state["well_50"] = all_wells[idx_50 % 96]
    
    with open(TIP_STATE_FILE, "w") as f: json.dump(tip_state, f)

    # 9. Complete Trials
    # failed_wells = set(df_absorbance.loc[df_absorbance["success"] == 0, "well_slot"])
    # for idx, t in ax_client.experiment.trials.items():
    #     if t._properties.get("well_slot") in failed_wells: t.mark_abandoned(unsafe=True)

    # 9. Complete Trials
    print("\n--- Completing Trials & Applying Punishment Model ---")

    for tid in trial_indices:
        well = ax_client.experiment.trials[tid]._properties["well_slot"]
        try:
            abs_val = df_absorbance.loc[df_absorbance["well_slot"] == well, "absorbance"].values[0]
            if pd.isna(abs_val): abs_val = 1.0 # default fail
        except IndexError:
            abs_val = 1.0 
        
        t_params = ax_client.experiment.trials[tid].arm.parameters
        
        # --- PUNISHMENT MODEL ---
        original_vol = sum(t_params[s] for s in surf_names)
        
        if abs_val > absorbance_threshold:
            # Failed: Apply punishment
            reported_vol = original_vol * PUNISHMENT_FACTOR
            status_msg = "FAILED"
            print(f"⚠️  Trial {tid} failed absorbance threshold ({abs_val:.4f} > {absorbance_threshold}). Applying punishment.")
        else:
            # Passed: Use actual volume
            reported_vol = original_vol
            status_msg = "SUCCESS!"
            print(f"✅ Trial {tid} succeeded absorbance threshold ({abs_val:.4f} <= {absorbance_threshold}).")

        # Log for Smoke Test / Console visibility
        print(f"Trial {tid} [{status_msg}]: Abs {abs_val:.4f} | Vol: {original_vol:.1f} -> Reported: {reported_vol:.1f}")


        import logging
        logging.getLogger("ax.core.observation").setLevel(logging.CRITICAL)
        logging.getLogger("ax.core.trial").setLevel(logging.CRITICAL)
        logging.getLogger("ax.core.experiment").setLevel(logging.CRITICAL)
        ax_client.complete_trial(tid, {"obj_total_vol": reported_vol, "absorbance": abs_val})

    ax_client.save_to_json_file(OPTIMIZER_FILE_PATH + str(n) + "_loaded.json")
    
    # 10. Viewer Result
    results = hf.build_results(n, df_absorbance, design_file_path=DESIGN_FILE_PATH)
    
    # Get status (COMPLETED/RUNNING)
    df_stat = hf.ax_trial_status_dataframe(ax_client)
    
    # Merge and Sort
    view = results.merge(
        df_stat[["trial_index", "status", "plate_num"]], 
        on="trial_index", 
        how="left"
    ).sort_values("trial_index")

    # --- CUSTOM METRICS ---

    # 1. Add "Previous Best" (The record to beat)
    view["prior_best_vol"] = best_total_vol

    # 2. Format Absorbance
    if "absorbance" in view.columns:
        view["absorbance"] = view["absorbance"].round(4)

    # 3. Calculate Original vs Reported Volume for Viewer
    # Ensure surfactant columns are float
    surf_cols = [f"s{i}" for i in range(1, 9)]
    for c in surf_cols: view[c] = view[c].astype(float)
    
    view["original_total_vol"] = view[surf_cols].sum(axis=1)
    
    # Re-apply punishment logic strictly for the CSV view
    view["reported_vol"] = view.apply(
        lambda x: x["original_total_vol"] * PUNISHMENT_FACTOR if x["absorbance"] > absorbance_threshold else x["original_total_vol"], 
        axis=1
    )

    # 4. Add 'is_new_record' flag
    # Logic: Successful (Abs <= threshold) AND Original Volume < Previous Best
    view["is_new_record"] = (
        (view["absorbance"] <= absorbance_threshold) & 
        (view["original_total_vol"] < best_total_vol)
    )

    # --- COLUMN ORDERING ---
    desired_cols = [
        "trial_index", "drug_name", 
        "well_slot", "deep_well_slot", 
        "rack_1000", "well_1000", "well_50", 
        "replicates", 
        "s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", 
        "original_total_vol", "reported_vol",  
        "success", "absorbance",
        "prior_best_vol", "is_new_record", "status"
    ]
    
    # Filter to only existing columns
    final_cols = [c for c in desired_cols if c in view.columns]
    view = view[final_cols]

    # Save to CSV
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = os.path.join(EXP_PATH, "results")
    os.makedirs(results_dir, exist_ok=True)
    view.to_csv(os.path.join(results_dir, f"viewer_results{_SUFFIX}_i{n}_{ts}.csv"), index=False)
    
    # Print Highlights
    print("\n--- Iteration Highlights ---")
    highlight_cols = ["trial_index", "s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "absorbance", "original_total_vol", "reported_vol", "is_new_record"]
    print(view[highlight_cols].tail(num_random_trials if n==0 else TRIALS_PER_ITERATION).to_string(index=False))

print(f"\nOptimization Loop {start_n} -> {n} Complete.")



# smoke test: SMOKE_TEST=1 python governing_files/drug_surfactant_bo.py
# real experiments: python governing_files/drug_surfactant_bo.py