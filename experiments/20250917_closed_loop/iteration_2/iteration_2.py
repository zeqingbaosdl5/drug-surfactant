# %% [markdown]
# # import libraries

# %%
import pandas as pd
from ax.service.ax_client import AxClient, ObjectiveProperties
import matplotlib.pyplot as plt
from ax.modelbridge.registry import Models
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
import time


import sys

sys.path.append("../")
import helper_functions as hf

# %% [markdown]
# # generate recommendations

# %%
n = hf.get_iteration_number()

for i in range(3):
    print("Very Important: Please Confirm the Iteration Number is Iteration " + str(n))

print()

list_of_drugs = (["IBP"] + ["LOV"] + ["DCF"] + ["GLV"]) * 2

for i in range(3):
    print("Very Important: Please Confirm the Drugs are: ", list_of_drugs)


# %%
time_start = time.time()


df_design, ax_client, data_so_far, best_concs = hf.run_optimizer(
    current_iteration=n, drug_list=list_of_drugs, bopt=1
)

time_end = time.time()
time_duration = round((time_end - time_start) / 60, 2)

print("Time taken for optimization: " + str(time_duration) + " mins")
print("Time taken for optimization: " + str(time_duration * 60) + " seconds")

# %% [markdown]
# # process results

# %%
ax_client = hf.load_design_optimizer(n)
ax_client.get_trials_data_frame()

# %%
df_design, df_vol = hf.design_to_vol(n)
df_design["constraint"] = df_design["drug_name"].map(best_concs).fillna(0.0)
df_design


# %%
df_vol

# %%
df_vol[["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]].sum()

# %%
plate_well = input("Enter the plate well starting well (e.g., F1): ")
deepplate_well = input("Enter the deep plate well starting well (e.g., F1): ")


print("Please confirm the following information:")
print("Wellplate will start at: " + plate_well)
print("Deep plate will start at: " + deepplate_well)

print()
print("*******************************************************")
print("Continue if correct, or rerun this cell if incorrect.")
print("*******************************************************")

# %%
hf.generate_protocol(
    df_vol=df_vol, iteration=n, plate_well=plate_well, deepplate_well=deepplate_well
)

# %%
df_absorbance = hf.process_absorbance(iteration=n, threshold=0.06)
df_absorbance

# %%
results = hf.build_results(n, df_absorbance)
results

# %% [markdown]
# # load the results to the optimizer

# %%
ax_client = hf.load_data_to_optimizer(iteration=n, results=results)
ax_client

# %%
