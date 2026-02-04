import pandas as pd
import numpy as np
import os
import re

drug_stock_conc = 25  
surfactant_stock_conc = 100 
actual_surfactant_stock_conc = 50 
drug_total_volume = 0.18  
surfactant_total_volume = 1.2  
number_of_surfactants = 8 

# AI will ignore the drug parameters (it is only included in the results csv)
normalize_drug_properties_dict = {
    "IBP": {"full_name": "Ibuprofen", "normalized_properties": {}, "drug_stock_conc": 25}, #{"Drug_MW": 0.2063, "Drug_LogP": 0.3073, "Drug_TPSA": 0.0373}, "drug_stock_conc": 25},
    "DCF": {"full_name": "Diclofenac", "normalized_properties": {}, "drug_stock_conc": 25}, #{"Drug_MW": 0.2962, "Drug_LogP": 0.4364, "Drug_TPSA": 0.0493}, "drug_stock_conc": 25},
    "LOV": {"full_name": "Lovastatin", "normalized_properties": {}, "drug_stock_conc": 25}, #{"Drug_MW": 0.4045, "Drug_LogP": 0.4196, "Drug_TPSA": 0.0728}, "drug_stock_conc": 25},
    "GLV": {"full_name": "Griseofulvin", "normalized_properties": {}, "drug_stock_conc": 25}, #{"Drug_MW": 0.3528, "Drug_LogP": 0.2810, "Drug_TPSA": 0.0711}, "drug_stock_conc": 25},
}

def design_to_vol(iteration, design_file_path, drug_stock_conc=drug_stock_conc, drug_total_volume=drug_total_volume, surfactant_stock_conc=surfactant_stock_conc, surfactant_total_volume=surfactant_total_volume):  
    full_path = f"{design_file_path}i{iteration}.csv"
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"CSV not found at {full_path}")
    
    # Read CSV (handle variable columns if needed)
    try:
        df_design = pd.read_csv(full_path)
    except:
        return None, None

    s_cols = [f"s{i}" for i in range(1, number_of_surfactants + 1)]
    drug_cols = ["IBP", "LOV", "DCF", "GLV"]

    df_vol = pd.DataFrame({"trial_index": df_design["trial_index"], "drug_name": df_design["drug_name"]})
    
    for s in s_cols:
        df_vol[s] = pd.to_numeric(df_design[s], errors='coerce').fillna(0.0)
    
    for d in drug_cols:
        df_vol[d] = 0.0
        
    for idx, row in df_design.iterrows():
        chosen_drug = row['drug_name']
        if chosen_drug in drug_cols:
            df_vol.at[idx, chosen_drug] = 180.0

    df_vol["dmso"] = round((drug_total_volume*1000) - df_vol[drug_cols].sum(axis=1), 2)
    df_vol["water"] = round((surfactant_total_volume*1000) - df_vol[s_cols].sum(axis=1), 2)
    
    return df_design, df_vol

# --- FIXED LOGIC: Handles Duplicates and Location ---
def process_absorbance(raw_data_file_path, trials_data, replicates=3, threshold=0.06):
    """
    Reads the absorbance CSV and extracts values for the specific wells used in this batch.
    trials_data: List of dicts containing 'well_slot' (the start well for each trial).
    """
    # Load 8x12 CSV (Rows A-H, Cols 1-12)
    try:
        df = pd.read_csv(raw_data_file_path, index_col=0)
        
        # --- FIX 1: Remove Duplicate Rows ---
        # Keeps the first 'A', drops the second empty 'A'
        df = df[~df.index.duplicated(keep='first')]
        
        # --- FIX 2: Ensure Columns are Strings ---
        # Ensures that column "1" is treated as string "1", not integer 1
        df.columns = df.columns.astype(str)

    except Exception as e:
        print(f"[ERR] Could not read raw data: {e}")
        return pd.DataFrame()

    summary = []
    
    for trial in trials_data:
        start_well = trial['well_slot']
        
        # Identify the 3 replicate wells
        # Example: start_well="A10" -> wells=["A10", "A11", "A12"]
        target_wells = []
        curr = start_well
        for _ in range(replicates):
            target_wells.append(curr)
            curr = get_next_well(curr)
            
        # Extract values from dataframe
        vals = []
        for w in target_wells:
            row = w[0]        # "A"
            col = str(w[1:])  # "10"
            try:
                # Opentrons CSV usually has columns "1", "2"... as strings
                val = df.at[row, col]
                
                # Extra Safety: If it STILL returns a series (unlikely now), take the first one
                if isinstance(val, pd.Series):
                    val = val.iloc[0]
                    
                vals.append(float(val))
            except KeyError:
                print(f"[WARN] Well {w} not found in raw data file.")
                vals.append(0.0) # Default to 0 if missing

        # Determine Success
        # Success = 1 if ALL replicates are clear (< threshold)
        # Success = 0 if ANY replicate is cloudy (> threshold)
        is_clear = all(v < threshold for v in vals)
        success = 1 if is_clear else 0
        avg_abs = float(np.mean(vals))
        
        summary.append({
            "well_slot": start_well,
            "success": success,
            "absorbance": avg_abs
        })
        
    return pd.DataFrame(summary)

def build_results(iteration, df_absorbance, design_file_path):
    df_design = pd.read_csv(f"{design_file_path}i{iteration}.csv")
    
    # Merge design with results on 'well_slot' to ensure alignment
    results = pd.merge(df_design, df_absorbance, on="well_slot", how="left")
    
    # 1. Actual Volume
    results["vol_actual"] = results["total_vol"]
    
    # 2. Penalized Volume (The "Objective" the AI sees)
    # If Success: Use actual volume.
    # If Fail (success=0): Use 1200 (Max Penalty).
    results["vol_with_penalty"] = np.where(results["success"] == 1, results["total_vol"], surfactant_total_volume * 1000)
    
    # Clean up old columns if they exist
    if "obj_total_vol" in results.columns:
        results.drop(columns=["obj_total_vol"], inplace=True)
        
    return results

def add_drug_names(df):
    if "drug" in df.columns:
        df["drug_name"] = df["drug"]
        df["drug_full"] = df["drug"].map({abbr: props["full_name"] for abbr, props in normalize_drug_properties_dict.items()})
    return df

def get_next_well(starting_well, offset=1):
    if not isinstance(starting_well, str) or len(starting_well) < 2:
        raise ValueError(f"Invalid starting_well: {starting_well}")
    row_letter = starting_well[0].upper()
    col_str = starting_well[1:]
    col_num = int(col_str)
    start_index = (ord(row_letter) - ord("A")) * 12 + (col_num - 1)
    next_index = start_index + offset
    if next_index >= 96:
        raise ValueError("Wellplate exhausted.")
    next_row = chr(ord("A") + (next_index // 12))
    next_col = (next_index % 12) + 1
    return f"{next_row}{next_col}"

def ax_trial_status_dataframe(ax_client):
    rows = []
    for idx, trial in ax_client.experiment.trials.items():
        rows.append({
            "trial_index": idx, 
            "status": trial.status.name, 
            "plate_num": trial._properties.get("plate_num")
        })
    return pd.DataFrame(rows)