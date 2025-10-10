import pandas as pd
import numpy as np
from ax.service.ax_client import AxClient, ObjectiveProperties
import matplotlib.pyplot as plt
from ax.modelbridge.factory import Models
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
import subprocess


def virtual_exp(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, surfactant_conc=None):
    """
    Virtual experiment function for evaluating drug-surfactant formulations.
    
    Args:
        s1-s12: Surfactant ratios (parameters)
        surfactant_conc: Total surfactant concentration (parameter)
    
    Returns:
        dict with objectives:
        - complexity: Number of surfactants used (minimize)
        - cost: Sum of surfactant ratios (minimize) 
        - performance: Formulation performance metric (maximize)
        - obj_surf_conc: ANALYTIC deterministic objective (minimize)
                        Equals surfactant_conc parameter directly
    """
    complexity = sum(1 for x in [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12] if x != 0)
    cost = s1+s2+s3+s4+s5+s6+s7+s8+s9+s10+s11+s12
    performance = 0.3*s1*(1+s2) - 0.5*s3*s4 + s5**2 + 0.8*s9 - s10*s11 + 0.2*s12
    
    # obj_surf_conc is an ANALYTIC deterministic objective (not black-box)
    # It equals the surfactant_conc parameter - no modeling needed, exact relationship
    obj_surf_conc = surfactant_conc if surfactant_conc is not None else 0
    
    return {'complexity': complexity, 'cost': cost, 'performance': performance, 'obj_surf_conc': obj_surf_conc}

def optimizer_init(stability_threshold=0.06):
    """
    Initialize the Ax optimizer for drug-surfactant formulation optimization.
    
    Args:
        stability_threshold: Absorbance threshold for stability constraint (default: 0.06).
                           Formulations with absorbance <= threshold are considered stable.
                           Adjust this value based on module conditions.
    
    Returns:
        AxClient configured for multi-objective optimization
    
    Note:
        obj_surf_conc is an ANALYTIC deterministic objective (not black-box):
        - It equals the surfactant_conc parameter directly
        - No experimental measurement needed
        - Known mathematical relationship: obj_surf_conc = surfactant_conc
        - Ax will still model it but the relationship is exact
    """
    
    # generation strategy
    gs = GenerationStrategy(
        steps=[
            GenerationStep(
                model=Models.SOBOL,
                num_trials=8,  # how many sobol trials to perform (rule of thumb: 2 * number of params)
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
            {"name": f"s{i}", "type": "range", "bounds": [0, 20], "value_type": "int"} for i in range(1, 13)] + 

            [{"name": "surfactant_conc", "type": "range", "bounds": [1, 50], "value_type": "int"},
             {"name": "drug_conc",       "type": "range", "bounds": [1, 50], "value_type": "int"}],

        objectives={
            'complexity': ObjectiveProperties(minimize=True, threshold=5),
            'cost': ObjectiveProperties(minimize=True, threshold=0.5),
            'performance': ObjectiveProperties(minimize=False),
            'obj_surf_conc': ObjectiveProperties(minimize=True),  # Analytic: equals surfactant_conc
        },

        parameter_constraints=[
            "s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 + s9 + s10 + s11 + s12 >= 1", 
        ],
        
        # Outcome constraints can be added when stability measurements are available:
        # outcome_constraints=[f"stability <= {stability_threshold}"]
    )

    return ax_client


def design_to_conc(df):

    df_conc = pd.DataFrame()
    df_conc['trial_index'] = df['trial_index']
    df_conc['surfactant_conc'] = df['surfactant_conc']
    df_conc['drug_conc'] = df['drug_conc']
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

def design_to_conc_to_vol(df, drug_stock_conc=50, drug_total_volume=0.12, surfactant_stock_conc=50, surfactant_total_volume=1): # in mg/mL or mL
    
    df_conc = design_to_conc(df)
    df_vol = conc_to_vol(df_conc, drug_stock_conc, drug_total_volume, surfactant_stock_conc, surfactant_total_volume)

    return df_conc, df_vol


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
