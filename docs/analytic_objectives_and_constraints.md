# Analytic Objectives and Stability Constraints

This document explains the key concepts for `obj_surf_conc` as an analytic deterministic objective and stability as a threshold-based constraint.

## Analytic vs Black-Box Deterministic Objectives

### obj_surf_conc: An Analytic Deterministic Objective

The `obj_surf_conc` objective is **analytic deterministic**, meaning:

- **Known mathematical relationship**: `obj_surf_conc = surfactant_conc` (exact equality)
- **No experimental measurement needed**: Computed directly from parameters
- **No model uncertainty**: The relationship is exact, not learned

This is different from a **black-box deterministic objective** where:
- The function is evaluated (e.g., via experiment/simulation)
- Results are always the same for identical inputs (deterministic)
- But the mathematical relationship is unknown to Ax
- Ax must model the relationship using Gaussian Processes or other surrogates

### Why This Matters

For black-box objectives, setting `noise_sd=0` tells Ax the observations are noiseless, but Ax still treats it as needing to be modeled through experimental evaluation.

For analytic objectives like `obj_surf_conc`, the optimizer could theoretically:
1. Not model it at all (just compute directly)
2. Use the exact relationship in optimization

In practice with Ax 0.2.x, we still pass it as an objective for simplicity, and Ax will learn the trivial relationship quickly. The key benefit is that no experimental work is needed to determine this value.

## Stability: Threshold-Based Constraint

### Threshold Behavior (Not "Lower is Better")

As clarified by @ZeqingBao:
- Stability is measured by absorbance (turbidity)
- It's a **threshold-based criterion**, not "lower is better"
- Formulations with `absorbance <= threshold` are stable
- Values below the threshold don't provide additional benefit
- The threshold should be **easily adjustable** for different module conditions

### Adjustable Threshold

```python
# Default threshold (absorbance)
ax_client = hf.optimizer_init(stability_threshold=0.06)

# Adjust for specific conditions
ax_client = hf.optimizer_init(stability_threshold=0.10)  # More permissive
ax_client = hf.optimizer_init(stability_threshold=0.04)  # More restrictive
```

### Implementation as Outcome Constraint

When stability measurements are available, add as an outcome constraint:

```python
ax_client.create_experiment(
    name="drug_surfactant",
    parameters=[...],
    objectives={...},
    outcome_constraints=[
        f"stability <= {stability_threshold}"  # Only formulations meeting threshold are feasible
    ],
)
```

This ensures:
- Ax only proposes candidates predicted to be stable
- Infeasible (unstable) trials don't contribute to optimization
- The optimization finds Pareto-optimal formulations within the stable region

## Usage Example

```python
import helper_functions as hf

# Initialize optimizer with custom stability threshold
ax_client = hf.optimizer_init(stability_threshold=0.06)

# Get trial parameters
parameters, trial_index = ax_client.get_next_trial()

# Extract parameters
surfactant_conc = parameters["surfactant_conc"]
s1 = parameters["s1"]
# ... extract other parameters ...

# Run experiment
# Note: surfactant_conc MUST be passed to get correct obj_surf_conc
results = hf.virtual_exp(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12,
                         surfactant_conc=surfactant_conc)

# results['obj_surf_conc'] equals surfactant_conc exactly (analytic)
# When stability measurements are available, add results['stability'] = measured_absorbance

ax_client.complete_trial(trial_index=trial_index, raw_data=results)
```

## Key Takeaways

1. **obj_surf_conc is analytic**: It equals `surfactant_conc` exactly - no experiment needed
2. **Stability is threshold-based**: Not "lower is better", just needs to be below threshold
3. **Threshold is adjustable**: Easy to change based on module conditions via `stability_threshold` parameter
4. **Future work**: Add stability as an outcome constraint when measurements are available

## References

- Ax documentation on outcome constraints: https://ax.dev/docs/intro-to-bo/
- BoTorch models: https://botorch.org/docs/models/
- Discussion on analytic vs black-box objectives in GitHub issues
