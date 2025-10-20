# drug-surfactant

Bayesian optimization workflow for drug-surfactant formulation using Ax.

## Features

- Multi-objective optimization (complexity, cost, performance)
- Robust error handling for failed experiments
- Automatic detection of infeasible parameter combinations
- **Threshold-based early stopping for time-dependent experiments**
- Integration with Opentrons liquid handling robots

## New: Failed Experiment Handling & Early Stopping

### 1. Parameter Validation

When Ax suggests parameter combinations that are physically infeasible (e.g., concentrations too high for available stock solutions), the workflow now gracefully handles these failures:

```python
import helper_functions as hf

# Initialize optimizer
client = hf.optimizer_init()

# Run optimization with automatic failure handling
for trial_index, parameterization in parameterizations.items():
    success = hf.safe_complete_trial(
        client=client,
        trial_index=trial_index,
        parameterization=parameterization
    )
```

### 2. Threshold-Based Early Stopping

For time-dependent experiments (e.g., absorbance measurements over 12 hours), you can report intermediate measurements and stop trials early if they exceed a threshold:

```python
# Initialize with intermediate data support
client = hf.optimizer_init(support_intermediate_data=True)

# Report intermediate measurement (e.g., at 1 hour)
hf.update_trial_with_intermediate_data(
    client=client,
    trial_index=0,
    raw_data={"absorbance": 0.45},
    time_step=1.0
)

# Stop trial early if threshold exceeded
hf.early_stop_trial_if_threshold_exceeded(
    client=client,
    trial_index=0,
    metric_name="absorbance",
    threshold=1.5,
    comparison="greater"
)
```

**Benefits:**
- No crashes on invalid parameters
- Early stopping saves time on poor-performing experiments
- Optimizer learns from both failed and early-stopped trials
- Workflow continues despite failures

See [FAILED_EXPERIMENT_HANDLING.md](FAILED_EXPERIMENT_HANDLING.md) for detailed documentation and [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for updating existing workflows.

## Installation

```bash
pip install ax-platform
```

## Usage

- [example_safe_trials.py](example_safe_trials.py) - Basic parameter validation example
- [example_early_stopping.py](example_early_stopping.py) - Threshold-based early stopping example