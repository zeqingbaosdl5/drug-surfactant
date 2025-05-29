import pandas as pd
import numpy as np
from ax.service.ax_client import AxClient, ObjectiveProperties
import matplotlib.pyplot as plt
from ax.modelbridge.factory import Models
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
import subprocess
import os
import re


optimizer_file_path = 'optimizer/optimizer_'
raw_data_file_path = 'raw_data/raw_absorbance_'
#results_file_path = 'result/result_'


def virtual_exp(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12):

    complexity = sum(1 for x in [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12] if x != 0)
    cost = s1+s2+s3+s4+s5+s6+s7+s8+s9+s10+s11+s12
    performance = 0.3*s1*(1+s2) - 0.5*s3*s4 + s5**2 + 0.8*s9 - s10*s11 + 0.2*s12
    return {'complexity': complexity, 'cost': cost, 'performance': performance}

def optimizer_init():
    
    # generation strategy
    gs = GenerationStrategy(
        steps=[
            GenerationStep(
                model=Models.SOBOL,
                num_trials=16,  # how many sobol trials to perform (rule of thumb: 2 * number of params)
                model_kwargs={"seed": 0},
            ),
            GenerationStep(
                model=Models.SAASBO,
                num_trials=-1,
                model_kwargs={},
            ),
        ]
    )

    # initialize the AxClient
    ax_client = AxClient(generation_strategy=gs)

    # create the design space and objective space
    ax_client.create_experiment(

        name="drug_surfactant",
        parameters = [
            {"name": f"s{i}", "type": "range", "bounds": [0, 100], "value_type": "int"} for i in range(1, 13)] + 

            [{"name": "surfactant_conc", "type": "range", "bounds": [1, 100], "value_type": "int"},
             {"name": "drug_conc",       "type": "range", "bounds": [1, 100], "value_type": "int"}],

        objectives={
            'micelle_drug_conc': ObjectiveProperties(minimize=False),
            'surfactant_conc': ObjectiveProperties(minimize=True),
            'complexity': ObjectiveProperties(minimize=True, threshold=2),
        },

        # parameter_constraints=[
        #     "s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 + s9 + s10 + s11 + s12 >= 1", 
        # ],
    )

    return ax_client


def design_to_conc(df, drug_stock_conc=25, surfactant_stock_conc=50):

    df_conc = pd.DataFrame()
    df_conc['trial_index'] = df['trial_index']
    df_conc['surfactant_conc'] = df['surfactant_conc']/100 * surfactant_stock_conc
    df_conc['drug_conc'] = df['drug_conc']/100 * drug_stock_conc


    total_ratios = [f's{i}' for i in range(1, 13)]
    total_sum = df[total_ratios].sum(axis=1)
    for i in range(1, 13):
        df_conc[f's{i}'] = df[f's{i}'] / total_sum * df_conc['surfactant_conc']
    return df_conc

def conc_to_vol_helper(conc, total_volume, stock_conc):
    vol = (conc * total_volume) / stock_conc
    return vol

def conc_to_vol(df, drug_stock_conc, drug_total_volume, surfactant_stock_conc, surfactant_total_volume): # in mg/mL or mL

    df_vol = pd.DataFrame()
    df_vol['trial_index'] = df['trial_index']
    df_vol['drug'] = df['drug_conc'].apply(lambda conc: conc_to_vol_helper(conc, total_volume=drug_total_volume, stock_conc=drug_stock_conc))
    s_cols = [f"s{i}" for i in range(1, 13) if f"s{i}" in df.columns]
    for s_col in s_cols:
        df_vol[s_col] = df[s_col].apply(lambda conc: conc_to_vol_helper(conc, total_volume=surfactant_total_volume, stock_conc=surfactant_stock_conc))
    df_vol['dmso'] = drug_total_volume - df_vol['drug']

    df_vol['water'] = surfactant_total_volume - df_vol[s_cols].sum(axis=1)
    df_vol.loc[:, df_vol.columns != 'trial_index'] *= 1000 # convert to uL

    return df_vol

def design_to_conc_to_vol(df, drug_stock_conc=25, drug_total_volume=0.12, surfactant_stock_conc=50, surfactant_total_volume=1): # in mg/mL or mL
    
    df_conc = design_to_conc(df)
    df_vol = conc_to_vol(df_conc, drug_stock_conc, drug_total_volume, surfactant_stock_conc, surfactant_total_volume)

    return df_conc, df_vol


def process_absorbance(iteration, replicates=2, threshold=0.1):

    n = replicates
    core_df = pd.read_excel(raw_data_file_path + 'i' + str(iteration) + '.xlsx', sheet_name=0, usecols="B:N", skiprows=23, nrows=9)
    clean_df = core_df.dropna()
    row_labels = clean_df.iloc[:, 0]
    numeric_data = clean_df.iloc[:, 1:]
    binary_data = (numeric_data < threshold).astype(int)

    # Combine back with row labels
    binary_df = pd.concat([row_labels.reset_index(drop=True), binary_data.reset_index(drop=True)], axis=1)

    # Flatten the binary values (excluding the 'Row' labels), row-wise
    binary_values = binary_df.iloc[:, 1:].values.flatten()
    #print(binary_values)

    # Calculate how many complete groups of size n
    num_groups = len(binary_values) // n

    # Prepare summary list
    summary = []

    for i in range(num_groups):
        group = binary_values[i * n: (i + 1) * n]
        success = int(all(group))  # If all values in the group are 1, then success = 1; else 0
        summary.append({"trial_index": i, "success": success})

    # Convert to DataFrame
    summary_df = pd.DataFrame(summary)
    
    return summary_df

def build_results(df_design, df_conc, df_absorbance):
    # 1. trial_index from df_design
    results = pd.DataFrame()
    results['trial_index'] = df_design['trial_index']

    # 2. s1 to s12 from df_design
    s_cols = [f's{i}' for i in range(1, 13)]
    results[s_cols] = df_design[s_cols]

    # 3. surfactant_conc and drug_conc from df_conc
    results['surfactant_conc'] = df_conc['surfactant_conc']
    results['drug_conc'] = df_conc['drug_conc']

    # 4. success from df_absorbance
    results['success'] = df_absorbance['success']

    # 5. micelle_drug_conc = drug_conc / 10 * success
    results['micelle_drug_conc'] = (results['drug_conc'] / 10) * results['success']

    # 6. complexity = number of non-zero s1-s12
    results['complexity'] = results[s_cols].ne(0).sum(axis=1)

    return results


def normalize_data(df, mode):
    df = df.copy()  

    factors = {
        'surfactant_conc': 50,
        'micelle_drug_conc': 2.5,
        'complexity': 12
    }
    for col, factor in factors.items():
        if col in df.columns:
            if mode == 'normalize':
                df[col] = df[col] / factor
            elif mode == 'denormalize':
                df[col] = df[col] * factor
            else:
                raise ValueError("mode must be either 'normalize' or 'denormalize'")

    return df


def run_optimizer(current_iteration, n_trials=8):

    if current_iteration == 0:
        ax_client = AxClient.load_from_json_file(optimizer_file_path + '00' + '.json')
    else:
        ax_client = AxClient.load_from_json_file("../iteration_" + str(current_iteration-1) + "/" + optimizer_file_path + str(current_iteration-1) + '_loaded.json')

    trials, _ = ax_client.get_next_trials(n_trials)

    # Prepare the trial data for DataFrame
    trials_data = []
    for trial_index, parameters in trials.items():
        trials_data.append(
            {
                "trial_index": trial_index,
                **parameters,
                "Loading": None,
                "Loading_STD": None,
                "Surfactant_conc": None,
                "Surfactant_conc_STD": None,                
                "Complexity": None,
                "Complexity_STD": None,
            }
        )

    ax_client.save_to_json_file(optimizer_file_path + str(current_iteration) + '.json')
    return pd.DataFrame(trials_data), ax_client


def load_data_to_optimizer(iteration, norm_results):
    
    n=iteration
    ax_client = AxClient.load_from_json_file(optimizer_file_path + str(n) + '.json')
    labeled_data = norm_results.copy()

    for _, row in labeled_data.iterrows():
        trial_index = int(row["trial_index"])
        raw_data = {
            "micelle_drug_conc": (row["micelle_drug_conc"]),
            "surfactant_conc": (row["surfactant_conc"]),
            "complexity": (row["complexity"]),
            }
        
        ax_client.complete_trial(trial_index=trial_index, raw_data=raw_data)
    
    ax_client.save_to_json_file(optimizer_file_path + str(n) + '_loaded.json')

    return ax_client

def get_iteration_number():

    current_dir = os.getcwd()

    folder_name = os.path.basename(current_dir)

    match = re.search(r"iteration_(\d+)", folder_name)
    if match:
        return int(match.group(1))
    else:
        raise ValueError("Wrong file")

def upload_file_to_robot(local_file_path, remote_file_name):

    remote_user = 'root'
    remote_host = '192.168.10.143'

    remote_folder = '/var/lib/jupyter/notebooks/Zeqing_Bao/drug_surfactant/'
    remote_file_path = remote_folder + remote_file_name

    mkdir_command = [
        'ssh',
        f'{remote_user}@{remote_host}',
        f'mkdir -p {remote_folder}'
    ]

    mkdir_result = subprocess.run(mkdir_command, capture_output=True, text=True)
    if mkdir_result.returncode == 0:
        print("Remote notebooks directory ready.")
    else:
        print("Failed to verify/create notebooks directory.")
        print("Error:", mkdir_result.stderr)

    scp_command = [
        'scp',
        local_file_path,
        f'{remote_user}@{remote_host}:{remote_file_path}'
    ]

    scp_result = subprocess.run(scp_command, capture_output=True, text=True)
    if scp_result.returncode == 0:
        print("File transfer successful!")
    else:
        print("File transfer failed.")
        print("Error:", scp_result.stderr)
