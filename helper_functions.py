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