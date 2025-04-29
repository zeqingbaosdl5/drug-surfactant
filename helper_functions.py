import pandas as pd
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
        parameters=[

            {"name": "r1", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "r2", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "r3", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "r4", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "r5", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "r6", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "r7", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "r8", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "r9", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "r10", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "r11", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "r12", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"}],


        objectives={
            'complexity': ObjectiveProperties(minimize=True, threshold=5),
            'cost': ObjectiveProperties(minimize=True, threshold=0.5),
            'performance': ObjectiveProperties(minimize=False),
        },


        parameter_constraints=[
    #        "c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + c9 + c10 + c11 + c12 <= 8.0",  # example of a sum constraint, which may be redundant/unintended if composition_constraint is also selected
    #        "r1 + r2 + r3 + r4 + r5 + r6 + r7 + r8 + r9 + r10 + r11 + r12 <= 1.0",  # example of a sum constraint, which may be redundant/unintended if composition_constraint is also selected
        ],
    )

    return ax_client