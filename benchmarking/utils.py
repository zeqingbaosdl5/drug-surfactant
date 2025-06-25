import numpy as np
import pandas as pd
import torch


def set_seeds(seed: int):
    """Set random seeds for reproducibility."""
    np.random.seed(seed)
    torch.manual_seed(seed)


def branin(x1, x2):
    y = float(
        (x2 - 5.1 / (4 * np.pi**2) * x1**2 + 5.0 / np.pi * x1 - 6.0) ** 2
        + 10 * (1 - 1.0 / (8 * np.pi)) * np.cos(x1)
        + 10
    )

    return y


def ackley(x1, x2, a=20, b=0.2, c=2 * np.pi):
    """
    ACKLEY FUNCTION

    Authors: Sonja Surjanovic, Simon Fraser University
             Derek Bingham, Simon Fraser University

    Parameters:
    xx : list or numpy array
        Input vector [x1, x2, ..., xd]
    a : float, optional
        Constant (default is 20)
    b : float, optional
        Constant (default is 0.2)
    c : float, optional
        Constant (default is 2*pi)

    Returns:
    y : float
        Output of the Ackley function
    """
    xx = np.array([x1, x2])
    d = len(xx)

    sum1 = np.sum(xx**2)
    sum2 = np.sum(np.cos(c * xx))

    term1 = -a * np.exp(-b * np.sqrt(sum1 / d))
    term2 = -np.exp(sum2 / d)

    y = term1 + term2 + a + np.exp(1)

    return y
