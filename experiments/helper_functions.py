import pandas as pd
import numpy as np
import os
import re


# Path constants moved to top-level runner (drug_surfactant_bo.py).
# The runner must set the following attributes on this module at runtime:
# `optimizer_file_path`, `raw_data_file_path`, `design_file_path`, `snapshot_dir`.
# results_file_path = 'result/result_'

drug_stock_conc = 25  # mg/mL
surfactant_stock_conc = 100  # represents percent of the stock solution
actual_surfactant_stock_conc = 50  # mg/mL represents the actual conc
drug_total_volume = 0.18  # mL
surfactant_total_volume = 1.2  # mL
number_of_surfactants = 8  # s1 to s8

normalize_drug_properties_dict = {
    "IBP": {
        "full_name": "Ibuprofen",
        "normalized_properties": {
            "Drug_MW": 0.2063,
            "Drug_LogP": 0.3073,
            "Drug_TPSA": 0.0373,
        },  # normalized values /1000; /10; /1000
        "drug_stock_conc": 25,  # mg/mL
    },
    "DCF": {
        "full_name": "Diclofenac",
        "normalized_properties": {
            "Drug_MW": 0.2962,
            "Drug_LogP": 0.4364,
            "Drug_TPSA": 0.0493,
        },  # normalized values /1000; /10; /1000
        "drug_stock_conc": 25,  # mg/mL
    },
    "LOV": {
        "full_name": "Lovastatin",
        "normalized_properties": {
            "Drug_MW": 0.4045,
            "Drug_LogP": 0.4196,
            "Drug_TPSA": 0.0728,
        },  # normalized values /1000; /10; /1000
        "drug_stock_conc": 25,  # mg/mL
    },
    "ITZ": {
        "full_name": "Itraconazole",
        "normalized_properties": {
            "Drug_MW": 0.7056,
            "Drug_LogP": 0.5577,
            "Drug_TPSA": 0.1047,
        },  # normalized values /1000; /10; /1000
        "drug_stock_conc": 25,  # mg/mL
    },
    "RPD": {
        "full_name": "Risperidone",
        "normalized_properties": {
            "Drug_MW": 0.4105,
            "Drug_LogP": 0.3590,
            "Drug_TPSA": 0.0642,
        },  # normalized values /1000; /10; /1000
        "drug_stock_conc": 25,  # mg/mL
    },
    "GLV": {
        "full_name": "Griseofulvin",
        "normalized_properties": {
            "Drug_MW": 0.3528,
            "Drug_LogP": 0.2810,
            "Drug_TPSA": 0.0711,
        },  # normalized values /1000; /10; /1000
        "drug_stock_conc": 25,  # mg/mL
    },
    "CTZ": {
        "full_name": "Clotrimazole",
        "normalized_properties": {
            "Drug_MW": 0.3448,
            "Drug_LogP": 0.5377,
            "Drug_TPSA": 0.0178,
        },  # normalized values /1000; /10; /1000
        "drug_stock_conc": 25,  # mg/mL
    },
    "GBC": {
        "full_name": "Glibenclamide/Glyburide",
        "normalized_properties": {
            "Drug_MW": 0.4940,
            "Drug_LogP": 0.3642,
            "Drug_TPSA": 0.1136,
        },  # normalized values /1000; /10; /1000
        "drug_stock_conc": 25,  # mg/mL
    },
}


# BO initialization moved to top-level script (drug_surfactant_bo.py)


# def design_to_conc(df, drug_stock_conc=drug_stock_conc, surfactant_stock_conc=surfactant_stock_conc):

#     df_conc = pd.DataFrame()
#     df_conc['trial_index'] = df['trial_index']
#     df_conc['drug_name'] = df['drug_name']
#     df_conc['surfactant_conc'] = df['surfactant_conc']/100 * surfactant_stock_conc
#     df_conc['drug_conc'] = df['drug_conc']/100 * drug_stock_conc


#     total_ratios = [f's{i}' for i in range(1, number_of_surfactants+1)]
#     total_sum = df[total_ratios].sum(axis=1)
#     for i in range(1, number_of_surfactants+1):
#         df_conc[f's{i}'] = df[f's{i}'] / total_sum * df_conc['surfactant_conc']
#     return df_conc


def conc_to_vol_helper(conc, total_volume, stock_conc):
    vol = (conc * total_volume) / stock_conc
    return vol


def conc_to_vol(
    df,
    drug_stock_conc,
    drug_total_volume,
    surfactant_stock_conc,
    surfactant_total_volume,
):  # in mg/mL or mL

    # start output
    df_vol = pd.DataFrame(
        {"trial_index": df["trial_index"], "drug_name": df["drug_name"]}
    )

    # drug volume (mL)
    df_vol["drug"] = df["drug_conc"].apply(
        lambda c: conc_to_vol_helper(c, drug_total_volume, drug_stock_conc)
    )

    # initialize surfactant volume columns s1…sN
    s_cols = [f"s{i}" for i in range(1, number_of_surfactants + 1)]
    for s in s_cols:
        df_vol[s] = 0.0

    # find all "surf_X" slots dynamically
    surf_slots = sorted(
        [col for col in df.columns if re.match(r"^surf_\d+$", col)],
        key=lambda x: int(x.split("_")[1]),
    )

    # for each slot, compute its volume and add it into the correct s# column
    for slot in surf_slots:
        conc_col = f"{slot}_conc"
        # volume from that slot (in mL)
        slot_volumes = df[conc_col].apply(
            lambda c: conc_to_vol_helper(
                c, surfactant_total_volume, surfactant_stock_conc
            )
        )
        # which surfactant it is
        surf_names = df[slot]
        for idx, surf in surf_names.items():
            if pd.isna(surf):
                continue
            if surf not in s_cols:
                # skip unknown or out‑of‑range surfactants
                continue
            df_vol.at[idx, surf] += slot_volumes.at[idx]

    # calculate dmso and water (mL)
    df_vol["dmso"] = drug_total_volume - df_vol["drug"]
    df_vol["water"] = surfactant_total_volume - df_vol[s_cols].sum(axis=1)

    # convert everything except trial_index & drug_name to µL
    data_cols = df_vol.columns.difference(["trial_index", "drug_name"])
    df_vol.loc[:, data_cols] *= 1000

    return df_vol


def add_drug_columns(df):
    unique_drugs = df["drug_name"].unique()
    for d in unique_drugs:
        df[d] = df.apply(
            lambda row: row["drug"] if row["drug_name"] == d else 0, axis=1
        )
    return df


def design_to_vol(
    iteration,
    design_file_path,
    drug_stock_conc=drug_stock_conc,
    drug_total_volume=drug_total_volume,
    surfactant_stock_conc=surfactant_stock_conc,
    surfactant_total_volume=surfactant_total_volume,
):  # in mg/mL or mL

    df_design = pd.read_csv(design_file_path + "i" + str(iteration) + ".csv")

    s_cols = [f"s{i}" for i in range(1, number_of_surfactants + 1)]
    drug_cols = ["IBP", "LOV", "DCF", "GLV"]

    # New format: s1..sN and drug volumes are already in µL.
    if all(col in df_design.columns for col in s_cols + drug_cols):
        df_vol = pd.DataFrame(
            {
                "trial_index": df_design["trial_index"],
                "drug_name": df_design.get("drug_name", None),
            }
        )

        for s in s_cols:
            df_vol[s] = df_design[s].astype(float)

        for d in drug_cols:
            df_vol[d] = df_design[d].astype(float)

        # dmso and water (µL) as remainder
        df_vol["dmso"] = (drug_total_volume * 1000) - df_vol[drug_cols].sum(axis=1)
        df_vol["water"] = (surfactant_total_volume * 1000) - df_vol[s_cols].sum(axis=1)
    else:
        # Old format: surf_1/surf_2 choice + *_conc columns
        df_vol = conc_to_vol(
            df_design,
            drug_stock_conc,
            drug_total_volume,
            surfactant_stock_conc,
            surfactant_total_volume,
        )
        df_vol_drug = add_drug_columns(df_vol)
        return df_design, df_vol_drug

    return df_design, df_vol


def process_absorbance(raw_data_file_path, replicates=3, threshold=0.06):
    # 1) Read plate-format CSV (A-H rows, 1-12 columns)
    # The first row is header (empty, 1,2,...,12), then A-H rows
    df = pd.read_csv(raw_data_file_path, nrows=8, index_col=0)
    arr = df.to_numpy().flatten(order="C")
    arr = arr[~np.isnan(arr)]
    binary = (arr < threshold).astype(int)
    n_chunks = len(binary) // replicates
    summary = []
    # Map from flat index to well_slot (A1, A2, ..., H12)
    rows = list(df.index)
    cols = list(df.columns)
    for i in range(n_chunks):
        block = binary[i * replicates : (i + 1) * replicates]
        success = int(block.all())
        # Calculate well_slot for the first value in this chunk
        flat_idx = i * replicates
        row_idx = flat_idx // len(cols)
        col_idx = flat_idx % len(cols)
        well_slot = f"{rows[row_idx]}{cols[col_idx]}"
        summary.append({"trial_index": i, "success": success, "well_slot": well_slot})

    return pd.DataFrame(summary)


def build_results(iteration, df_absorbance, design_file_path):
    # 1. trial_index from df_design
    df_design = pd.read_csv(design_file_path + "i" + str(iteration) + ".csv")
    results = df_design.copy()
    # results['trial_index'] = df_design['trial_index']
    # results['drug_name'] = df_design['drug_name']

    # # 2. s1 to s12 from df_design
    # s_cols = [f's{i}' for i in range(1, number_of_surfactants+1)]
    # results[s_cols] = df_design[s_cols]

    # # 3. surfactant_conc and drug_conc from df_conc
    # results['surfactant_input'] = df_conc['surfactant_conc']
    # results['drug_conc'] = df_conc['drug_conc']

    # # 4. Calculate initial drug concentration to surfactant concentration ratio
    # results['initial_drug_conc_surfactant_conc_ratio'] = results['drug_conc'] / results['surfactant_conc']

    # 5. success from df_absorbance
    results["success"] = df_absorbance[
        "success"
    ]  # if 'success' in df_absorbance.columns else 0

    # # 6. micelle_drug_conc = drug_conc / 10 * success
    # results['micelle_drug_conc'] = (results['drug_conc'] / 10) * results['success']

    # # 7. complexity = number of non-zero s1-s12
    # results['complexity'] = results[s_cols].ne(0).sum(axis=1)

    #    results['surf_conc'] = results['surf_1_conc'] + results['surf_2_conc'] + results['surf_3_conc']
    results["obj_surf_conc"] = np.where(
        results["success"] == 1,
        results["surf_conc"],
        surfactant_total_volume * 1000,
    )

    return results


# def normalize_data(df, mode):
#     df = df.copy()

#     factors = {
#         'surfactant_input': surfactant_stock_conc,  # normalized value is between 0 and 1
#         'success': 1,  # success is binary, so no normalization needed
#         'drug_conc': drug_stock_conc,  # normalized value is between 0 and 1
# #        'micelle_drug_conc': drug_stock_conc / 10,  # micelle drug conc is 1/10 of drug conc
#         'complexity': number_of_surfactants
#     }
#     for col, factor in factors.items():
#         if col in df.columns:
#             if mode == 'normalize':
#                 df[col] = df[col] / factor
#             elif mode == 'denormalize':
#                 df[col] = df[col] * factor
#             else:
#                 raise ValueError("mode must be either 'normalize' or 'denormalize'")

#     return df


def lowest_so_far(df, list_of_drugs):

    result = {}
    for drug in list_of_drugs:
        filtered_df = df[df["drug_name"] == drug]
        if not filtered_df.empty:
            result[drug] = filtered_df["obj_surf_conc"].min()
        else:
            result[drug] = None  # or np.nan or skip, depending on your preference
    return result


def add_drug_names(df):
    # Newer experiments represent drug identity directly as a categorical parameter.
    if "drug" in df.columns:
        df["drug_name"] = df["drug"]
        df["drug_full"] = df["drug"].map(
            {
                abbr: props["full_name"]
                for abbr, props in normalize_drug_properties_dict.items()
            }
        )
        return df

    # Backward-compatible: infer drug from normalized drug MW.
    abbr_map = {
        props["normalized_properties"]["Drug_MW"]: abbr
        for abbr, props in normalize_drug_properties_dict.items()
    }
    full_map = {
        props["normalized_properties"]["Drug_MW"]: props["full_name"]
        for props in normalize_drug_properties_dict.values()
    }

    df["drug_name"] = df["Drug_MW"].map(abbr_map)
    df["drug_full"] = df["Drug_MW"].map(full_map)

    return df


def get_next_well(starting_well, offset=1):
    """Return the well that is `offset` positions after `starting_well` in a 96-well plate.

    - `starting_well`: string like 'A1'..'H12'
    - `offset`: positive integer steps forward

    Raises ValueError if starting_well is invalid or if the computed well is beyond H12.
    """
    # Validate input
    if not isinstance(starting_well, str) or len(starting_well) < 2:
        raise ValueError(f"Invalid starting_well: {starting_well}")

    row_letter = starting_well[0].upper()
    col_str = starting_well[1:]
    try:
        col_num = int(col_str)
    except Exception:
        raise ValueError(f"Invalid starting_well column: {starting_well}")

    if row_letter < "A" or row_letter > "H" or col_num < 1 or col_num > 12:
        raise ValueError(f"starting_well out of 96-well range: {starting_well}")

    start_index = (ord(row_letter) - ord("A")) * 12 + (col_num - 1)
    next_index = start_index + offset
    if next_index >= 96:
        raise ValueError("Wellplate exhausted: replace plate before continuing.")

    next_row = chr(ord("A") + (next_index // 12))
    next_col = (next_index % 12) + 1
    return f"{next_row}{next_col}"
