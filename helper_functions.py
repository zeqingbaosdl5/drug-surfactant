import pandas as pd
import numpy as np
from ax.service.ax_client import AxClient, ObjectiveProperties
import matplotlib.pyplot as plt
from ax.modelbridge.factory import Models
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy


def virtual_exp(r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12):

    complexity = sum(1 for x in [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12] if x != 0)
    cost = r1+r2+r3+r4+r5+r6+r7+r8+r9+r10+r11+r12
    performance = 0.3*r1*(1+r2) - 0.5*r3*r4 + r5**2 + 0.8*r9 - r10*r11 + 0.2*r12
    return {'complexity': complexity, 'cost': cost, 'performance': performance}

def optimizer_init():
    
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
            {"name": f"r{i}", "type": "range", "bounds": [0, 20], "value_type": "int"} for i in range(1, 13)] + 

            [{"name": "surfactant_conc", "type": "range", "bounds": [1, 500], "value_type": "int"},
             {"name": "drug_conc",       "type": "range", "bounds": [1, 500], "value_type": "int"}],

        objectives={
            'complexity': ObjectiveProperties(minimize=True, threshold=5),
            'cost': ObjectiveProperties(minimize=True, threshold=0.5),
            'performance': ObjectiveProperties(minimize=False),
        },

        parameter_constraints=[
            "r1 + r2 + r3 + r4 + r5 + r6 + r7 + r8 + r9 + r10 + r11 + r12 >= 1", 
        ],
    )

    return ax_client


