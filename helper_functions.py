import pandas as pd
import numpy as np
from ax.api.client import Client
from ax.api.configs import RangeParameterConfig
import matplotlib.pyplot as plt
import subprocess


def virtual_exp(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12):

    complexity = sum(1 for x in [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12] if x != 0)
    cost = s1+s2+s3+s4+s5+s6+s7+s8+s9+s10+s11+s12
    performance = 0.3*s1*(1+s2) - 0.5*s3*s4 + s5**2 + 0.8*s9 - s10*s11 + 0.2*s12
    return {'complexity': complexity, 'cost': cost, 'performance': performance}

def optimizer_init(support_intermediate_data=False):
    """
    Initialize the Ax Client for drug-surfactant optimization.
    
    Args:
        support_intermediate_data: If True, enables support for reporting intermediate
            trial data (e.g., time-series measurements). This is required for early
            stopping based on intermediate measurements.
    
    Returns:
        Configured Client instance
    """
    # Initialize the Client
    client = Client()

    # Configure the experiment parameters
    parameters = [
        RangeParameterConfig(
            name=f"s{i}",
            bounds=(0, 20),
            parameter_type="int"
        ) for i in range(1, 13)
    ] + [
        RangeParameterConfig(
            name="surfactant_conc",
            bounds=(1, 50),
            parameter_type="int"
        ),
        RangeParameterConfig(
            name="drug_conc",
            bounds=(1, 50),
            parameter_type="int"
        )
    ]
    
    client.configure_experiment(
        name="drug_surfactant",
        parameters=parameters,
        parameter_constraints=[
            "s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 + s9 + s10 + s11 + s12 >= 1",
        ],
        support_intermediate_data=support_intermediate_data,
    )
    
    # Configure optimization with multi-objective
    # Using minimize for complexity and cost, maximize for performance
    # Thresholds are specified as outcome constraints
    client.configure_optimization(
        objectives={
            "complexity": "minimize",
            "cost": "minimize", 
            "performance": "maximize"
        },
        objective_thresholds={
            "complexity": 5,
            "cost": 0.5,
        },
    )

    return client


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
    
    # Check for invalid volumes (negative values indicate infeasible experiments)
    if (df_vol['dmso'] < 0).any() or (df_vol['water'] < 0).any():
        raise ValueError("Invalid experimental parameters: negative volumes calculated. "
                        "This indicates concentrations are too high for the available stock solutions.")
    
    df_vol.loc[:, df_vol.columns != 'trial_index'] *= 1000 # convert to uL

    return df_vol

def design_to_conc_to_vol(df, drug_stock_conc=50, drug_total_volume=0.12, surfactant_stock_conc=50, surfactant_total_volume=1): # in mg/mL or mL
    
    df_conc = design_to_conc(df)
    df_vol = conc_to_vol(df_conc, drug_stock_conc, drug_total_volume, surfactant_stock_conc, surfactant_total_volume)

    return df_conc, df_vol


def update_trial_with_intermediate_data(client, trial_index, raw_data, time_step=None):
    """
    Update a running trial with intermediate measurement data.
    
    This allows reporting measurements at intermediate time points (e.g., absorbance
    at 1hr, 6hrs, etc.) without completing the trial. Useful for time-dependent
    experiments where you want to track progress.
    
    Args:
        client: The Ax client instance
        trial_index: Index of the trial to update
        raw_data: Measurement data as a dict mapping metric names to (mean, SEM) tuples,
                 or just mean values if SEM is 0. For time-series data, can be a list
                 of (time_step, data_dict) tuples.
        time_step: Optional time step for the measurement (e.g., hours elapsed)
    
    Example:
        # Single metric at a time point
        update_trial_with_intermediate_data(
            client, 0, 
            raw_data={"absorbance": 0.45},
            time_step=1.0  # 1 hour
        )
        
        # Multiple time points
        update_trial_with_intermediate_data(
            client, 0,
            raw_data=[(1.0, {"absorbance": 0.45}), (6.0, {"absorbance": 0.82})]
        )
    """
    if time_step is not None and not isinstance(raw_data, list):
        # Convert single measurement to time-series format
        raw_data = [(time_step, raw_data)]
    
    client.update_running_trial_with_intermediate_data(
        trial_index=trial_index,
        raw_data=raw_data
    )


def check_threshold_exceeded(client, trial_index, metric_name, threshold, comparison="greater"):
    """
    Check if the most recent measurement for a trial exceeds a threshold.
    
    This is used for simple threshold-based early stopping: if the most recent
    measurement is above (or below) a threshold, the trial should be stopped.
    
    Args:
        client: The Ax client instance
        trial_index: Index of the trial to check
        metric_name: Name of the metric to check (e.g., "absorbance")
        threshold: Threshold value to compare against
        comparison: Either "greater" (default) or "less" for threshold comparison
    
    Returns:
        True if threshold is exceeded, False otherwise
    """
    try:
        # Get trial data
        df = client.get_trials_data_frame()
        trial_data = df[df['trial_index'] == trial_index]
        
        if trial_data.empty or metric_name not in trial_data.columns:
            return False
        
        # Get the most recent measurement (last non-null value)
        metric_values = trial_data[metric_name].dropna()
        if metric_values.empty:
            return False
        
        most_recent_value = metric_values.iloc[-1]
        
        # Compare against threshold
        if comparison == "greater":
            return most_recent_value > threshold
        elif comparison == "less":
            return most_recent_value < threshold
        else:
            raise ValueError(f"Invalid comparison: {comparison}. Use 'greater' or 'less'.")
    
    except Exception as e:
        print(f"Warning: Could not check threshold for trial {trial_index}: {e}")
        return False


def early_stop_trial_if_threshold_exceeded(client, trial_index, metric_name, threshold, 
                                           comparison="greater", reason=None):
    """
    Stop a trial early if its most recent measurement exceeds a threshold.
    
    This implements simple threshold-based early stopping for time-dependent experiments.
    For example, if absorbance at 6hrs exceeds a global threshold, the trial can be
    abandoned without waiting for the full 12hr duration.
    
    Args:
        client: The Ax client instance
        trial_index: Index of the trial to check
        metric_name: Name of the metric to check (e.g., "absorbance")
        threshold: Threshold value
        comparison: Either "greater" or "less"
        reason: Optional reason for stopping (will be logged)
    
    Returns:
        True if trial was stopped, False otherwise
    """
    if check_threshold_exceeded(client, trial_index, metric_name, threshold, comparison):
        if reason is None:
            reason = f"{metric_name} exceeded threshold of {threshold}"
        
        client.abandon_trial(trial_index=trial_index, reason=reason)
        print(f"Trial {trial_index} stopped early: {reason}")
        return True
    
    return False


def safe_complete_trial(client, trial_index, parameterization, drug_stock_conc=50, drug_total_volume=0.12, 
                        surfactant_stock_conc=50, surfactant_total_volume=1):
    """
    Safely complete a trial with error handling for failed experiments.
    
    If the experiment fails due to invalid parameters (e.g., concentrations too high),
    the trial is marked as failed instead of completed.
    
    Args:
        client: The Ax client instance
        trial_index: Index of the trial to complete
        parameterization: Dictionary of parameter values for the trial
        drug_stock_conc: Stock concentration of drug (mg/mL)
        drug_total_volume: Total volume for drug solution (mL)
        surfactant_stock_conc: Stock concentration of surfactant (mg/mL)
        surfactant_total_volume: Total volume for surfactant solution (mL)
        
    Returns:
        True if trial completed successfully, False if trial failed
    """
    try:
        # Extract surfactant parameters
        s_params = {f"s{i}": parameterization[f"s{i}"] for i in range(1, 13)}
        
        # Run virtual experiment
        results = virtual_exp(**s_params)
        
        # Create a temporary dataframe to validate volumes can be calculated
        temp_df = pd.DataFrame([{
            'trial_index': trial_index,
            **s_params,
            'surfactant_conc': parameterization['surfactant_conc'],
            'drug_conc': parameterization['drug_conc']
        }])
        
        # Validate that volumes can be calculated (this will raise ValueError if invalid)
        df_conc, df_vol = design_to_conc_to_vol(
            temp_df, 
            drug_stock_conc=drug_stock_conc,
            drug_total_volume=drug_total_volume,
            surfactant_stock_conc=surfactant_stock_conc,
            surfactant_total_volume=surfactant_total_volume
        )
        
        # If we get here, the experiment is valid
        client.complete_trial(trial_index=trial_index, raw_data=results)
        return True
        
    except (ValueError, KeyError, Exception) as e:
        # Mark trial as failed if any error occurs
        client.log_trial_failure(trial_index=trial_index)
        print(f"Trial {trial_index} marked as FAILED. Reason: {str(e)}")
        return False


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
