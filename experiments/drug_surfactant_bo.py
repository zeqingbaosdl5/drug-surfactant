import os
import sys


REPO_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(REPO_DIR, "experiments"))
sys.path.append(os.path.join(REPO_DIR, "experiments", "20250917_closed_loop"))

from opentrons_http_otflex_iA_mwe import run_otflex_iA

import helper_functions as hf


# Configuration
DRUG_LIST = (["IBP"] + ["LOV"] + ["DCF"] + ["GLV"]) * 2
BOPT_STEP = 1
N_TRIALS_PER_DRUG = 1

NEXT_PLATE_WELL = "F4"
NEXT_DEEPPLATE_WELL = "F4"
REPLICATES = 1


n = hf.get_iteration_number()

for _ in range(3):
    print(f"Very Important: Please Confirm the Iteration Number is Iteration {n}")

for _ in range(3):
    print("Very Important: Please Confirm the Drugs are:", DRUG_LIST)

# 1) Generate recommendations

df_design, ax_client, data_so_far, best_concs = hf.run_optimizer(
    current_iteration=n, drug_list=DRUG_LIST, bopt=BOPT_STEP, n_trials=N_TRIALS_PER_DRUG
)

# 2) Convert design to volumes and add constraint annotation

df_design, df_vol = hf.design_to_vol(n)
df_design["constraint"] = df_design["drug_name"].map(best_concs).fillna(0.0)

# 3) Run robot iteration (single call like `branin(...)`)

otflex_params = df_vol.drop(columns=["trial_index", "drug_name"]).to_dict(orient="records")[0]
otflex_params["next_plate_well"] = NEXT_PLATE_WELL
otflex_params["next_deepplate_well"] = NEXT_DEEPPLATE_WELL
otflex_params["replicates"] = REPLICATES

run_otflex_iA(otflex_params)

# 4) Process results and load them back into the optimizer

df_absorbance = hf.process_absorbance(iteration=n, replicates=REPLICATES, threshold=0.06)
results = hf.build_results(n, df_absorbance)
ax_client = hf.load_data_to_optimizer(iteration=n, results=results)
