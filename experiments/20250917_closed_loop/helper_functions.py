import pandas as pd
import numpy as np
from ax.service.ax_client import AxClient, ObjectiveProperties
import matplotlib.pyplot as plt
from ax.modelbridge.registry import Generators

from ax.core.observation import ObservationFeatures
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
import json
import subprocess
import os
import re
from ax.core.parameter_constraint import SumConstraint


optimizer_file_path = "optimizer/optimizer_"
raw_data_file_path = "raw_data/raw_absorbance_"
design_file_path = "optimizer/design_"
otflex_template_file_path = "../drug_surfactant_otflex_template.py"
otflex_output_file_path = "protocol/otflex_"
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
    drug_stock_conc=drug_stock_conc,
    drug_total_volume=drug_total_volume,
    surfactant_stock_conc=surfactant_stock_conc,
    surfactant_total_volume=surfactant_total_volume,
):  # in mg/mL or mL

    df_design = pd.read_csv(design_file_path + "i" + str(iteration) + ".csv")

    # df_conc = design_to_conc(df_design)

    df_vol = conc_to_vol(
        df_design,
        drug_stock_conc,
        drug_total_volume,
        surfactant_stock_conc,
        surfactant_total_volume,
    )

    df_vol_drug = add_drug_columns(df_vol)

    return df_design, df_vol_drug


def process_absorbance(iteration, replicates=3, threshold=0.06):
    # 1) read your raw block exactly as before
    core_df = pd.read_excel(
        raw_data_file_path + f"i{iteration}.xlsx",
        sheet_name=0,
        usecols="B:N",
        skiprows=23,
        nrows=9,
    )

    # 2) grab just the numeric part and flatten row-major
    arr = core_df.iloc[:, 1:].to_numpy().flatten(order="C")

    # 3) drop all the NaNs
    arr = arr[~np.isnan(arr)]

    # 4) binarize
    binary = (arr < threshold).astype(int)

    # 5) chop into consecutive chunks of size=replicates
    n_chunks = len(binary) // replicates
    summary = []
    for i in range(n_chunks):
        block = binary[i * replicates : (i + 1) * replicates]
        success = int(block.all())
        summary.append({"trial_index": i, "success": success})

    return pd.DataFrame(summary)


def build_results(iteration, df_absorbance):
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
        results["success"] == 1, results["surf_conc"], surfactant_stock_conc
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


def results_so_far(current_iteration):

    ax_client = AxClient.load_from_json_file(
        "../iteration_"
        + str(current_iteration - 1)
        + "/"
        + optimizer_file_path
        + str(current_iteration - 1)
        + "_loaded.json"
    )
    results = ax_client.get_trials_data_frame()

    return results


def lowest_so_far(df, list_of_drugs):

    result = {}
    for drug in list_of_drugs:
        filtered_df = df[df["drug_name"] == drug]
        if not filtered_df.empty:
            result[drug] = filtered_df["obj_surf_conc"].min()
        else:
            result[drug] = None  # or np.nan or skip, depending on your preference
    return result


# def fetch_previous_design(current_iteration, drug_list):


#     previous_ax_client = AxClient.load_from_json_file("../iteration_" + str(current_iteration-1) + "/" + optimizer_file_path + str(current_iteration-1) + '_loaded.json')
#     data_so_far = previous_ax_client.get_trials_data_frame()
#     data_so_far = add_drug_columns(data_so_far)
#     constrainst = lowest_so_far(data_so_far, drug_list)

#     return data_so_far, constrainst


def add_drug_names(df):
    abbr_map = {
        props["normalized_properties"]["Drug_MW"]: abbr
        for abbr, props in normalize_drug_properties_dict.items()
    }
    full_map = {
        props["normalized_properties"]["Drug_MW"]: props["full_name"]
        for props in normalize_drug_properties_dict.values()
    }

    # add the two new columns
    df["drug_name"] = df["Drug_MW"].map(abbr_map)
    df["drug_full"] = df["Drug_MW"].map(full_map)

    return df


# def run_optimizer(current_iteration, drug_list, bopt, n_trials=1):

#     if current_iteration == 0:
#         ax_client = AxClient.load_from_json_file(optimizer_file_path + '00' + '.json')
#     else:
#         ax_client = AxClient.load_from_json_file("../iteration_" + str(current_iteration-1) + "/" + optimizer_file_path + str(current_iteration-1) + '_loaded.json')
#         data_so_far = ax_client.get_trials_data_frame()
#         data_so_far = add_drug_names(data_so_far)
#         best_concs = lowest_so_far(data_so_far, drug_list)


#     ax_client.generation_strategy._curr = ax_client.generation_strategy._steps[bopt]

#     trials_data = []

#     count = 0
#     for drug in drug_list:
#         count = count+1

#         print()
#         print()
#         print("*" * 100, count, " out of ", len(drug_list), "*" * 100)
#         print("*" * 200)

#         drug_props = normalize_drug_properties_dict[drug]["normalized_properties"].copy()
#         drug_props["drug_conc"] = 100  # fix drug conc to the maximum

#         drug_features = ObservationFeatures(parameters = drug_props)

#         best_conc = best_concs[drug]

# #        space = ax_client.experiment.search_space

#         # 找到对应的 Parameter 对象（这里用私有属性 _parameters）
#         param_objs = [
#             ax_client.experiment.search_space._parameters["surf_1_conc"],
#             ax_client.experiment.search_space._parameters["surf_2_conc"],
#         ]

#         #Clear existing constraints
#         ax_client.experiment.search_space._parameter_constraints = []


#         # 重新构造上下界约束
#         new_constraints = [
#             # 上界： surf_1_conc + surf_2_conc <= bound
#             SumConstraint(parameters=param_objs, is_upper_bound=True,  bound=best_conc - 1),
#             # 下界： surf_1_conc + surf_2_conc >= 1
#             SumConstraint(parameters=param_objs, is_upper_bound=False, bound=1),
#         ]

#         print("Updating constraints for drug:", drug, " | Best conc so far:", best_conc)

#         # 直接替换私有属性
#         ax_client.experiment.search_space._parameter_constraints = new_constraints

#         # Print the updated constraints for verification
#         print("Updated constraints:", ax_client.experiment.search_space._parameter_constraints)


#         trials, _ = ax_client.get_next_trials(n_trials, fixed_features=drug_features)

#         # **关键**：清除上一次模型的拟合结果，让下一次 gen 时重新 fit
#         ax_client.generation_strategy._curr._model = None

#         # 逐条生成 trial，使用 force=True 强制重新拟合
#         for _ in range(n_trials):
#             parameters, trial_index = ax_client.get_next_trial(
#                 fixed_features=drug_features,
#                 force=True,
#             )
#             trials_data.append({
#                 "trial_index": trial_index,
#                 "drug_name":   drug,
#                 **parameters,
#             })


#         print()
#         if bopt == 0:
#             print("Generating a random trial for")
#         elif bopt == 1:
#             print("Generating a Bayesian Optimization trial for")
#         print("Drug name: ", normalize_drug_properties_dict[drug]["full_name"],f"{(drug)}", " | Iteration: ", current_iteration)
#         print()
#         print("*" * 200)
#         print("*" * 200)
#         print()
#         print()

#     df_design = pd.DataFrame(trials_data)
#     df_design ['surf_conc'] = df_design['surf_1_conc'] + df_design['surf_2_conc']
#     df_design ['obj_surf_conc'] = None


#     ax_client.save_to_json_file(optimizer_file_path + str(current_iteration) + '.json')
#     df_design.to_csv(design_file_path + 'i' + str(current_iteration) + '.csv', index=False)

#     return df_design, ax_client, data_so_far, best_concs


def run_optimizer(current_iteration, drug_list, bopt, n_trials=1):
    # 1. 加载或恢复上一次的 AxClient
    if current_iteration == 0:
        ax_client = AxClient.load_from_json_file(optimizer_file_path + "00.json")
    else:
        ax_client = AxClient.load_from_json_file(
            f"../iteration_{current_iteration-1}/{optimizer_file_path}{current_iteration-1}_loaded.json"
        )
        data_so_far = ax_client.get_trials_data_frame()
        data_so_far = add_drug_names(data_so_far)
        best_concs = lowest_so_far(data_so_far, drug_list)

    # 2. 切换到对应的 generation step（sobol/bo）
    ax_client.generation_strategy._curr = ax_client.generation_strategy._steps[bopt]

    trials_data = []
    count = 0

    for drug in drug_list:
        count += 1
        print(f"\n{'*'*80} {count}/{len(drug_list)} {'*'*80}\n")

        # 3. 构造固定的药物特征
        drug_props = normalize_drug_properties_dict[drug][
            "normalized_properties"
        ].copy()
        drug_props["drug_conc"] = 100  # 固定药浓度
        drug_features = ObservationFeatures(parameters=drug_props)

        # 4. 取出该 drug 的最新 best_conc
        best_conc = best_concs[drug]

        # 5. 构造并替换新的 search_space 约束
        space = ax_client.experiment.search_space
        param_objs = [
            space._parameters["surf_1_conc"],
            space._parameters["surf_2_conc"],
        ]
        new_constraints = [
            # 上界：surf_1_conc + surf_2_conc <= best_conc - 1
            SumConstraint(
                parameters=param_objs, is_upper_bound=True, bound=best_conc - 2
            ),
            # 下界：surf_1_conc + surf_2_conc >= 1
            SumConstraint(parameters=param_objs, is_upper_bound=False, bound=1),
        ]
        space._parameter_constraints = new_constraints
        print(
            f"Update constraints (drug={drug})：surf_1_conc+surf_2_conc <= {best_conc -2}，>=1"
        )

        # 6. 清除 BoTorch/SAASBO 的拟合缓存，确保使用最新约束重新 fit
        gs = ax_client.generation_strategy
        curr = gs._curr
        # BoTorchAdapter: clear each model_spec's _fitted_model
        if hasattr(curr, "model_specs"):
            for spec in curr.model_specs:
                spec._fitted_model = None
        # SAASBO: clear _model
        if hasattr(curr, "_model"):
            curr._model = None
        # Also clear generation_strategy-level _model (to be safe)
        if hasattr(gs, "_model"):
            gs._model = None

        # 7. Use single get_next_trial(force=True) loop to generate n_trials
        for _ in range(n_trials):
            parameters, trial_index = ax_client.get_next_trial(
                fixed_features=drug_features,
                force=True,
            )
            trials_data.append(
                {
                    "trial_index": trial_index,
                    "drug_name": drug,
                    **parameters,
                }
            )

    # 8. Organize returned DataFrame
    df_design = pd.DataFrame(trials_data)
    df_design["surf_conc"] = df_design["surf_1_conc"] + df_design["surf_2_conc"]
    df_design["obj_surf_conc"] = None

    # 9. Save state
    ax_client.save_to_json_file(f"{optimizer_file_path}{current_iteration}.json")
    df_design.to_csv(f"{design_file_path}i{current_iteration}.csv", index=False)

    return df_design, ax_client, data_so_far, best_concs


def generate_protocol(df_vol, iteration, plate_well, deepplate_well):
    n = iteration

    # Input file (template)
    input_path = otflex_template_file_path

    # Output file (update name as needed)
    output_path = otflex_output_file_path + str(n) + ".py"

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

        # To label data file name from plate reader
        # Protocol generation removed — handled externally.
        print(
            f"Updated trial {trial_index}: set success=0, surfactant_input=1, complexity=1"
        )

    # Save out the updated optimizer state
    updated_path = optimizer_file_path + f"{iteration}_loaded.json"
    ax_client.save_to_json_file(updated_path)

    return ax_client


def get_iteration_number():

    current_dir = os.getcwd()

    folder_name = os.path.basename(current_dir)

    match = re.search(r"iteration_(\d+)", folder_name)
    if match:
        return int(match.group(1))
    else:
        raise ValueError("Wrong file")
