import pandas as pd
import numpy as np
from ax.service.ax_client import AxClient, ObjectiveProperties
import matplotlib.pyplot as plt
from ax.modelbridge.registry import Generators as Models

from ax.core.observation import ObservationFeatures
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
import json
import subprocess
import os
import re


optimizer_file_path = 'optimizer/optimizer_'
raw_data_file_path = 'raw_data/raw_absorbance_'
design_file_path = 'optimizer/design_'
otflex_template_file_path = '../drug_surfactant_otflex_template-hs.py'
otflex_output_file_path = 'protocol/otflex_'
#results_file_path = 'result/result_'

drug_stock_conc = 25  # mg/mL
surfactant_stock_conc = 50  # mg/mL
drug_total_volume = 0.18  # mL
surfactant_total_volume = 1  # mL
number_of_surfactants = 8  # s1 to s12

normalize_drug_properties_dict = {

    'IBP': {
        'full_name': 'Ibuprofen',
        'normalized_properties': {"Drug_MW": 0.2063, "Drug_LogP": 0.3073,  "Drug_TPSA": 0.0373},  # normalized values /1000; /10; /1000
        'drug_stock_conc': 25, # mg/mL
    },

    'DCF': {
        'full_name': 'Diclofenac',
        'normalized_properties': {"Drug_MW": 0.2962, "Drug_LogP": 0.4364,  "Drug_TPSA": 0.0493},  # normalized values /1000; /10; /1000
        'drug_stock_conc': 25, # mg/mL
    },

    'LOV': {
        'full_name': 'Lovastatin',
        'normalized_properties': {"Drug_MW": 0.4045, "Drug_LogP": 0.4196,  "Drug_TPSA": 0.0728},  # normalized values /1000; /10; /1000
        'drug_stock_conc': 25, # mg/mL
    },

    'ITZ': {
        'full_name': 'Itraconazole',
        'normalized_properties': {"Drug_MW": 0.7056, "Drug_LogP": 0.5577,  "Drug_TPSA": 0.1047},  # normalized values /1000; /10; /1000
        'drug_stock_conc': 25, # mg/mL
    },

    'RPD': {
        'full_name': 'Risperidone',
        'normalized_properties': {"Drug_MW": 0.4105, "Drug_LogP": 0.3590,  "Drug_TPSA": 0.0642},  # normalized values /1000; /10; /1000
        'drug_stock_conc': 25, # mg/mL
    },
}


def optimizer_init():
    
    # generation strategy
    gs = GenerationStrategy(
        steps=[
            GenerationStep(
                model=Models.SOBOL,
                num_trials=3,  # how many sobol trials to perform (rule of thumb: 2 * number of params)
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

            # Drug_MW [0, 1000] ~ [0.0,1,0]
            {"name": "Drug_MW", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            # Drug_LogP [0, 10] ~ [0.0,1,0]
            {"name": "Drug_LogP", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            # Drug_TPSA [0, 1000] ~ [0.0,1,0]
            {"name": "Drug_TPSA", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            ] +

            [{"name": f"s{i}", "type": "range", "bounds": [0, 100], "value_type": "int"} for i in range(1, number_of_surfactants+1)] + 

            [{"name": "surfactant_conc", "type": "range", "bounds": [1, 100], "value_type": "int"},
             {"name": "drug_conc",       "type": "range", "bounds": [1, 100], "value_type": "int"}],

        objectives={
            'success': ObjectiveProperties(minimize=False, threshold=0.5),  # success rate threshold
            'surfactant_input': ObjectiveProperties(minimize=True),
            'complexity': ObjectiveProperties(minimize=True),
        },

        parameter_constraints=[
             "s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 >= 1", 
         ],

    )

    return ax_client


def design_to_conc(df, drug_stock_conc=drug_stock_conc, surfactant_stock_conc=surfactant_stock_conc):

    df_conc = pd.DataFrame()
    df_conc['trial_index'] = df['trial_index']
    df_conc['surfactant_conc'] = df['surfactant_conc']/100 * surfactant_stock_conc
    df_conc['drug_conc'] = df['drug_conc']/100 * drug_stock_conc


    total_ratios = [f's{i}' for i in range(1, number_of_surfactants+1)]
    total_sum = df[total_ratios].sum(axis=1)
    for i in range(1, number_of_surfactants+1):
        df_conc[f's{i}'] = df[f's{i}'] / total_sum * df_conc['surfactant_conc']
    return df_conc

def conc_to_vol_helper(conc, total_volume, stock_conc):
    vol = (conc * total_volume) / stock_conc
    return vol

def conc_to_vol(df, drug_stock_conc, drug_total_volume, surfactant_stock_conc, surfactant_total_volume): # in mg/mL or mL

    df_vol = pd.DataFrame()
    df_vol['trial_index'] = df['trial_index']
    df_vol['drug'] = df['drug_conc'].apply(lambda conc: conc_to_vol_helper(conc, total_volume=drug_total_volume, stock_conc=drug_stock_conc))
    s_cols = [f"s{i}" for i in range(1, number_of_surfactants+1) if f"s{i}" in df.columns]
    for s_col in s_cols:
        df_vol[s_col] = df[s_col].apply(lambda conc: conc_to_vol_helper(conc, total_volume=surfactant_total_volume, stock_conc=surfactant_stock_conc))
    df_vol['dmso'] = drug_total_volume - df_vol['drug']

    df_vol['water'] = surfactant_total_volume - df_vol[s_cols].sum(axis=1)
    df_vol.loc[:, df_vol.columns != 'trial_index'] *= 1000 # convert to uL

    return df_vol

def design_to_conc_to_vol(iteration, drug_stock_conc=drug_stock_conc, drug_total_volume=drug_total_volume, surfactant_stock_conc=surfactant_stock_conc, surfactant_total_volume=surfactant_total_volume): # in mg/mL or mL
    
    df_design = pd.read_csv(design_file_path + 'i' + str(iteration) + '.csv')

    df_conc = design_to_conc(df_design)
    df_vol = conc_to_vol(df_conc, drug_stock_conc, drug_total_volume, surfactant_stock_conc, surfactant_total_volume)

    return df_conc, df_vol


def process_absorbance(iteration, replicates=2, threshold=0.1):

    n = replicates
    
    core_df = pd.read_excel(raw_data_file_path + 'i' + str(iteration) + '.xlsx', sheet_name=0, usecols="B:N", skiprows=23, nrows=9)
    clean_df = core_df[~core_df.iloc[:, 1:].isna().all(axis=1)].dropna(axis=1, how='all')


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

def build_results(iteration, df_conc, df_absorbance):
    # 1. trial_index from df_design
    df_design = pd.read_csv(design_file_path + 'i' + str(iteration) + '.csv')
    results = pd.DataFrame()
    results['trial_index'] = df_design['trial_index']

    # 2. s1 to s12 from df_design
    s_cols = [f's{i}' for i in range(1, number_of_surfactants+1)]
    results[s_cols] = df_design[s_cols]

    # 3. surfactant_conc and drug_conc from df_conc
    results['surfactant_input'] = df_conc['surfactant_conc']
    results['drug_conc'] = df_conc['drug_conc']

    # # 4. Calculate initial drug concentration to surfactant concentration ratio
    # results['initial_drug_conc_surfactant_conc_ratio'] = results['drug_conc'] / results['surfactant_conc']

    # 5. success from df_absorbance
    results['success'] = df_absorbance['success'] #if 'success' in df_absorbance.columns else 0

    # # 6. micelle_drug_conc = drug_conc / 10 * success
    # results['micelle_drug_conc'] = (results['drug_conc'] / 10) * results['success']

    # 7. complexity = number of non-zero s1-s12
    results['complexity'] = results[s_cols].ne(0).sum(axis=1)

    return results


def normalize_data(df, mode):
    df = df.copy()  

    factors = {
        'surfactant_input': surfactant_stock_conc,  # normalized value is between 0 and 1
        'success': 1,  # success is binary, so no normalization needed
        'drug_conc': drug_stock_conc,  # normalized value is between 0 and 1
#        'micelle_drug_conc': drug_stock_conc / 10,  # micelle drug conc is 1/10 of drug conc
        'complexity': number_of_surfactants
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


def run_optimizer(current_iteration, drug, bopt, n_trials):

    if current_iteration == 0:
        ax_client = AxClient.load_from_json_file(optimizer_file_path + '00' + '.json')
    else:
        ax_client = AxClient.load_from_json_file("../iteration_" + str(current_iteration-1) + "/" + optimizer_file_path + str(current_iteration-1) + '_loaded.json')

    ax_client.generation_strategy._curr = ax_client.generation_strategy._steps[bopt]
    
    drug_props = normalize_drug_properties_dict[drug]["normalized_properties"].copy()
    drug_props["drug_conc"] = 100  # fix drug conc to the maximum

    drug_features = ObservationFeatures(parameters = drug_props)
    

    print("**************************************************************************************************************")
    print()
    if bopt == 0:
        print("Generating random trials for")
    elif bopt == 1:
        print("Generating Bayesian Optimization trials for")
    print("Drug name: ", normalize_drug_properties_dict[drug]["full_name"],f"{(drug)}", " | Iteration: ", current_iteration)
    print()
    print("**************************************************************************************************************")

    trials, _ = ax_client.get_next_trials(n_trials, fixed_features=drug_features)

    # Prepare the trial data for DataFrame
    trials_data = []
    for trial_index, parameters in trials.items():
        trials_data.append(
            {
                "trial_index": trial_index,
                **parameters,
#                "micelle_drug_conc": None,
                "success": None,
                "surfactant_input": None, 
                "Complexity": None,

            }
        )

    df_design = pd.DataFrame(trials_data)


    ax_client.save_to_json_file(optimizer_file_path + str(current_iteration) + '.json')
    df_design.to_csv(design_file_path + 'i' + str(current_iteration) + '.csv', index=False)

    return df_design, ax_client


def generate_protocol(df_vol, iteration, plate_well, deepplate_well):
    n = iteration

    # Input file (template)
    input_path = otflex_template_file_path

    # Output file (update name as needed)
    output_path = otflex_output_file_path + str(n) + '.py'


    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Replace plate wells in lines (modify in place)
    found_plate = False
    found_deep = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not found_plate and stripped.startswith("next_plate_well") and "'H3'" in stripped:
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = f"{indent}next_plate_well = '{plate_well}'\n"
            found_plate = True
        elif not found_deep and stripped.startswith("next_deepplate_well") and "'H3'" in stripped:
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = f"{indent}next_deepplate_well = '{deepplate_well}'\n"
            found_deep = True
        if found_plate and found_deep:
            break

    df_vol_list = []
    for idx, row in df_vol.iterrows():
        df_vol_row = {'': str(idx)}  
        df_vol_row.update({col: str(row[col]) for col in df_vol.columns})
        df_vol_list.append(df_vol_row)

    # Format your df_vol_list
    data_string = json.dumps(df_vol_list, indent=4)

    # Check that the input file exists
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Target file does not exist: {input_path}")

    # Locate the data block
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if "# to be rewritten according to the exp design" in line:
            for j in range(i + 1, len(lines)):
                if lines[j].strip().startswith("#") and "data = [" in lines[j + 1]:
                    start_idx = j
                    break
            break

    if start_idx is not None:
        for k in range(start_idx + 1, len(lines)):
            if lines[k].strip().startswith("#") and k > start_idx + 1:
                end_idx = k
                break

    # Extract indent prefix AFTER finding start_idx
    if start_idx is not None:
        indent_prefix = lines[start_idx][:len(lines[start_idx]) - len(lines[start_idx].lstrip())]
    else:
        indent_prefix = "    "

    # Replace block and write new file
    if start_idx is not None and end_idx is not None:
        hash_line = indent_prefix + "#" * 136 + "\n"
        data_lines = data_string.split('\n')
        first_line = indent_prefix + "    " + "data = " + data_lines[0].lstrip() + "\n"
        rest_lines = '\n'.join(indent_prefix + line for line in data_lines[1:]) + "\n"
        data_line = first_line + rest_lines
        replacement = [hash_line, data_line, hash_line]
        new_lines = lines[:start_idx] + replacement + lines[end_idx:]

        # Only create directory if needed
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Write to new output file
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        print(f"✅ Successfully wrote to: {output_path}")
    else:
        print("❌ Could not locate the block to replace.")

def load_design_optimizer(iteration):

    n = iteration

    ax_client = AxClient.load_from_json_file(optimizer_file_path + str(n) + '.json')

    return ax_client


def load_data_to_optimizer(iteration, norm_results):
    
    n=iteration
    ax_client = AxClient.load_from_json_file(optimizer_file_path + str(n) + '.json')
    labeled_data = norm_results.copy()

    for _, row in labeled_data.iterrows():
        trial_index = int(row["trial_index"])
        success = int(row["success"])
        # pull the original values
        surfactant_input = row["surfactant_input"]
        complexity       = row["complexity"]

        # decide whether to override
        if success == 0:
            surfactant_input = 1
            complexity = 1
            print(f"Trial {trial_index}: success=0 → overriding surfactant_input & complexity to 1")
        else:
            print(
                f"Trial {trial_index}: success={success} → "
                f"using surfactant_input={surfactant_input}, complexity={complexity}"
            )

        # build the payload
        raw_data = {
            "success": success,
            "surfactant_input": surfactant_input,
            "complexity": complexity,
            # "micelle_drug_conc": row["micelle_drug_conc"],
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
