"""
Batch Conditioning Example with Ax

This script demonstrates the recommended approach for batch conditioning 
(also known as pending observations or fantasy modeling) in Ax v1.

Key Points:
- Use `get_next_trials()` for batch generation with automatic batch conditioning
- Ax automatically tracks trials in RUNNING state as pending observations
- No manual fantasy point updates needed!
"""

import numpy as np
from ax.service.ax_client import AxClient, ObjectiveProperties
from ax.modelbridge.generation_strategy import GenerationStrategy, GenerationStep
from ax.modelbridge.factory import Generators


def branin(x1, x2):
    """Branin test function (2D)."""
    a = 1.0
    b = 5.1 / (4.0 * np.pi ** 2)
    c = 5.0 / np.pi
    r = 6.0
    s = 10.0
    t = 1.0 / (8.0 * np.pi)
    
    result = a * (x2 - b * x1 ** 2 + c * x1 - r) ** 2 + s * (1 - t) * np.cos(x1) + s
    # Add some noise
    noise = np.random.normal(0, 0.1)
    return {"objective": (result + noise, 0.1)}


def main():
    """Main function demonstrating get_next_trials with batch conditioning."""
    
    print("=" * 80)
    print("Batch Conditioning Example with get_next_trials()")
    print("=" * 80)
    
    # 1. Define generation strategy with parallelism limits
    print("\n1. Setting up GenerationStrategy with parallelism limits...")
    gs = GenerationStrategy(
        steps=[
            GenerationStep(
                model=Generators.SOBOL,
                num_trials=5,
                max_parallelism=3,  # Can run up to 3 Sobol trials in parallel
            ),
            GenerationStep(
                model=Generators.BOTORCH_MODULAR,
                num_trials=-1,  # Unlimited trials
                max_parallelism=2,  # Can run up to 2 BO trials in parallel
            ),
        ]
    )
    
    # 2. Create AxClient with the generation strategy
    ax_client = AxClient(generation_strategy=gs, verbose_logging=False)
    
    # 3. Create a simple 2D optimization problem
    ax_client.create_experiment(
        name="batch_conditioning_example",
        parameters=[
            {"name": "x1", "type": "range", "bounds": [-5.0, 10.0]},
            {"name": "x2", "type": "range", "bounds": [0.0, 15.0]},
        ],
        objectives={"objective": ObjectiveProperties(minimize=True)},
    )
    print("   ✓ Experiment created successfully!")
    
    # 4. Demonstrate get_next_trials with automatic batch conditioning
    print("\n2. Generating first batch with get_next_trials()...")
    batch_size = 5  # Request 5 trials
    trials_dict, optimization_complete = ax_client.get_next_trials(max_trials=batch_size)
    
    print(f"   → Generated {len(trials_dict)} trials (requested {batch_size})")
    print(f"   → Respects max_parallelism=3 for Sobol phase")
    print(f"   → Optimization complete: {optimization_complete}")
    
    # Display the generated trials
    print("\n   Generated trials:")
    for trial_idx, params in trials_dict.items():
        trial = ax_client.experiment.trials[trial_idx]
        print(f"   Trial {trial_idx}: x1={params['x1']:.4f}, x2={params['x2']:.4f} [Status: {trial.status}]")
    
    # 5. Try to generate more trials without completing first batch
    print("\n3. Attempting to generate more trials without completing first batch...")
    trials_dict_2, optimization_complete = ax_client.get_next_trials(max_trials=5)
    print(f"   → Generated {len(trials_dict_2)} additional trials")
    print(f"   → Expected: 0 (parallelism limit reached)")
    
    # Check current generation limits
    num_trials_available, is_complete = ax_client.get_current_trial_generation_limit()
    print(f"   → Current generation limit: {num_trials_available} trials")
    
    # 6. Complete the first batch of trials
    print("\n4. Completing first batch of trials...")
    for trial_idx, params in trials_dict.items():
        results = branin(params['x1'], params['x2'])
        ax_client.complete_trial(trial_index=trial_idx, raw_data=results)
        print(f"   ✓ Completed trial {trial_idx} with objective = {results['objective'][0]:.4f}")
    
    # 7. Generate more trials after completing first batch
    print("\n5. Generating second batch (remaining Sobol trials)...")
    trials_dict_3, optimization_complete = ax_client.get_next_trials(max_trials=5)
    print(f"   → Generated {len(trials_dict_3)} more trials")
    print(f"   → Total trials so far: {len(ax_client.experiment.trials)}")
    
    for trial_idx, params in trials_dict_3.items():
        print(f"   Trial {trial_idx}: x1={params['x1']:.4f}, x2={params['x2']:.4f}")
    
    # 8. Complete remaining Sobol trials
    print("\n6. Completing second batch...")
    for trial_idx, params in trials_dict_3.items():
        results = branin(params['x1'], params['x2'])
        ax_client.complete_trial(trial_index=trial_idx, raw_data=results)
        print(f"   ✓ Completed trial {trial_idx}")
    
    print(f"\n   All Sobol trials completed. Total: {len(ax_client.experiment.trials)} trials")
    
    # 9. Generate BO trials with batch conditioning
    print("\n7. Generating Bayesian Optimization batch with batch conditioning...")
    trials_dict_4, optimization_complete = ax_client.get_next_trials(max_trials=3)
    print(f"   → Generated {len(trials_dict_4)} BO trials (requested 3, limited to 2 by parallelism)")
    
    # Display the BO trials
    for trial_idx, params in trials_dict_4.items():
        trial = ax_client.experiment.trials[trial_idx]
        print(f"   Trial {trial_idx}: x1={params['x1']:.4f}, x2={params['x2']:.4f}")
        print(f"      Generated by: {trial.generator_run._model_key}")
    
    # 10. Verify batch conditioning is working (diversity check)
    print("\n8. Verifying batch conditioning (checking trial diversity)...")
    trial_indices = list(trials_dict_4.keys())
    if len(trial_indices) >= 2:
        params_1 = trials_dict_4[trial_indices[0]]
        params_2 = trials_dict_4[trial_indices[1]]
        
        distance = np.sqrt(
            (params_1['x1'] - params_2['x1'])**2 + 
            (params_1['x2'] - params_2['x2'])**2
        )
        
        print(f"   → Distance between the two BO trials: {distance:.4f}")
        print(f"   → Good diversity (>0.5) indicates batch conditioning is working")
    
    # 11. Complete BO trials
    print("\n9. Completing BO trials...")
    for trial_idx, params in trials_dict_4.items():
        results = branin(params['x1'], params['x2'])
        ax_client.complete_trial(trial_index=trial_idx, raw_data=results)
        print(f"   ✓ Completed trial {trial_idx} with objective = {results['objective'][0]:.4f}")
    
    # 12. Display results
    print("\n10. Final Results:")
    print("=" * 80)
    
    # Get best observed trial
    best_params, best_values = ax_client.get_best_parameters()
    print(f"\n   Best parameters found:")
    print(f"      x1 = {best_params['x1']:.4f}")
    print(f"      x2 = {best_params['x2']:.4f}")
    print(f"\n   Best objective value: {best_values[0]['objective']:.4f}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)
    print("✓ Automatic batch conditioning: Used get_next_trials() which handles pending observations")
    print("✓ Parallelism limits: GenerationStrategy respects max_parallelism settings")
    print("✓ No manual updates needed: Never called update_trial_data() with fantasy values")
    print("✓ Clean workflow: Simply generate trials, complete them when ready, and repeat")
    print("\nKey Takeaway: Use get_next_trials() for batch generation in production workflows!")
    print("=" * 80)


if __name__ == "__main__":
    main()
