import pandas as pd
import numpy as np
from ax.service.ax_client import AxClient, ObjectiveProperties
import matplotlib.pyplot as plt
import subprocess


def virtual_exp(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12):
    """Virtual experiment function - same as original"""
    complexity = sum(1 for x in [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12] if x != 0)
    cost = s1+s2+s3+s4+s5+s6+s7+s8+s9+s10+s11+s12
    performance = 0.3*s1*(1+s2) - 0.5*s3*s4 + s5**2 + 0.8*s9 - s10*s11 + 0.2*s12
    return {'complexity': complexity, 'cost': cost, 'performance': performance}


def optimizer_init():
    """Initialize the AxClient with current API"""
    # Create ax client using the current API
    ax_client = AxClient()

    # Create the design space and objective space
    ax_client.create_experiment(
        name="drug_surfactant",
        parameters=[
            {"name": f"s{i}", "type": "range", "bounds": [0, 20], "value_type": "int"} for i in range(1, 13)
        ] + [
            {"name": "surfactant_conc", "type": "range", "bounds": [1, 50], "value_type": "int"},
            {"name": "drug_conc", "type": "range", "bounds": [1, 50], "value_type": "int"}
        ],
        objectives={
            'complexity': ObjectiveProperties(minimize=True, threshold=5),
            'cost': ObjectiveProperties(minimize=True, threshold=0.5),
            'performance': ObjectiveProperties(minimize=False),
        },
        parameter_constraints=[
            "s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 + s9 + s10 + s11 + s12 >= 1", 
        ],
    )

    return ax_client


def design_to_conc(df):
    """Convert design parameters to concentrations - same as original"""
    df_conc = df.copy()
    df_conc['surfactant_conc'] = df['surfactant_conc']
    df_conc['drug_conc'] = df['drug_conc']
    return df_conc


def conc_to_vol_helper(conc, total_volume, stock_conc):
    """Helper function for concentration to volume conversion - same as original"""
    if stock_conc == 0:
        return 0
    return (conc * total_volume) / stock_conc


def conc_to_vol(df, drug_stock_conc, drug_total_volume, surfactant_stock_conc, surfactant_total_volume):
    """Convert concentrations to volumes - same as original"""
    df_vol = df.copy()
    
    # Convert drug concentration to volume
    df_vol['drug'] = df['drug_conc'].apply(
        lambda x: conc_to_vol_helper(x, drug_total_volume, drug_stock_conc)
    )
    
    # Convert surfactant concentrations to volumes
    for i in range(1, 13):
        col_name = f's{i}'
        df_vol[col_name] = df[col_name].apply(
            lambda x: conc_to_vol_helper(x, surfactant_total_volume, surfactant_stock_conc)
        )
    
    return df_vol


def design_to_conc_to_vol(df, drug_stock_conc=50, drug_total_volume=0.12, 
                         surfactant_stock_conc=50, surfactant_total_volume=1):
    """Combined function to convert design to concentrations to volumes - same as original"""
    df_conc = design_to_conc(df)
    df_vol = conc_to_vol(df_conc, drug_stock_conc, drug_total_volume, 
                        surfactant_stock_conc, surfactant_total_volume)
    return df_vol


def upload_file_to_robot(local_file_path, remote_file_name):
    """Upload file to robot - same as original"""
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