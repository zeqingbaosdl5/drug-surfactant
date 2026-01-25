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

normalize_drug_properties_dict = {
    "IBP": {"full_name": "Ibuprofen", "normalized_properties": {"Drug_MW": 0.2063, "Drug_LogP": 0.3073, "Drug_TPSA": 0.0373}, "drug_stock_conc": 25},
    "DCF": {"full_name": "Diclofenac", "normalized_properties": {"Drug_MW": 0.2962, "Drug_LogP": 0.4364, "Drug_TPSA": 0.0493}, "drug_stock_conc": 25},
    "LOV": {"full_name": "Lovastatin", "normalized_properties": {"Drug_MW": 0.4045, "Drug_LogP": 0.4196, "Drug_TPSA": 0.0728}, "drug_stock_conc": 25},
    "GLV": {"full_name": "Griseofulvin", "normalized_properties": {"Drug_MW": 0.3528, "Drug_LogP": 0.2810, "Drug_TPSA": 0.0711}, "drug_stock_conc": 25},
}

def conc_to_vol_helper(conc, total_volume, stock_conc):
    vol = (conc * total_volume) / stock_conc
    return vol 

# --- FIXED MATH FUNCTION ---
def design_to_vol(iteration, design_file_path, drug_stock_conc=drug_stock_conc, drug_total_volume=drug_total_volume, surfactant_stock_conc=surfactant_stock_conc, surfactant_total_volume=surfactant_total_volume):  
    full_path = f"{design_file_path}i{iteration}.csv"
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"CSV not found at {full_path}")
    
    headers = [
        "trial_index", "drug_name", "well_slot", "deep_well_slot",
        "rack_1000", "well_1000", "well_50", "replicates",
        "s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8",
        "total_vol", "obj_total_vol" 
    ]
    try:
        df_design = pd.read_csv(full_path, names=headers, skiprows=1)
    except:
        df_design = pd.read_csv(full_path)

    s_cols = [f"s{i}" for i in range(1, number_of_surfactants + 1)]
    drug_cols = ["IBP", "LOV", "DCF", "GLV"]

    # Direct Volume Pass-through
    df_vol = pd.DataFrame({"trial_index": df_design["trial_index"], "drug_name": df_design["drug_name"]})
    
    # Just copy the numbers, they are already volumes (uL)
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

def process_absorbance(raw_data_file_path, replicates=3, threshold=0.06):
    df = pd.read_csv(raw_data_file_path, nrows=8, index_col=0)
    arr = df.to_numpy().flatten(order="C")
    arr = arr[~np.isnan(arr)]
    n_chunks = len(arr) // replicates
    summary = []
    rows = list(df.index)
    cols = list(df.columns)
    for i in range(n_chunks):
        block = arr[i * replicates : (i + 1) * replicates]
        binary_block = (block < threshold).astype(int)
        success = int(binary_block.all())
        absorbance = float(np.mean(block))
        flat_idx = i * replicates
        row_idx = flat_idx // len(cols)
        col_idx = flat_idx % len(cols)
        well_slot = f"{rows[row_idx]}{cols[col_idx]}"
        summary.append({"well_slot": well_slot, "success": success, "absorbance": absorbance})
    return pd.DataFrame(summary)

def build_results(iteration, df_absorbance, design_file_path):
    headers = [
        "trial_index", "drug_name", "well_slot", "deep_well_slot",
        "rack_1000", "well_1000", "well_50", "replicates",
        "s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8",
        "total_vol", "obj_total_vol"
    ]
    df_design = pd.read_csv(design_file_path + "i" + str(iteration) + ".csv", names=headers, skiprows=1)
    results = df_design.copy()
    results["success"] = df_absorbance["success"]
    results["obj_total_vol"] = np.where(results["success"] == 1, results["total_vol"], surfactant_total_volume * 1000)
    return results

def add_drug_names(df):
    if "drug" in df.columns:
        df["drug_name"] = df["drug"]
        df["drug_full"] = df["drug"].map({abbr: props["full_name"] for abbr, props in normalize_drug_properties_dict.items()})
        return df
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
        raise ValueError("Wellplate exhausted: replace plate before continuing.")
    next_row = chr(ord("A") + (next_index // 12))
    next_col = (next_index % 12) + 1
    return f"{next_row}{next_col}"

def ax_trial_status_dataframe(ax_client):
    rows = []
    for idx, trial in ax_client.experiment.trials.items():
        rows.append({"trial_index": idx, "status": trial.status.name, "well_slot": trial._properties.get("well_slot"), "plate_num": trial._properties.get("plate_num")})
    return pd.DataFrame(rows)