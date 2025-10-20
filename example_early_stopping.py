"""
Example: Threshold-based early stopping for time-dependent experiments

This script demonstrates how to use intermediate data reporting and threshold-based
early stopping for time-dependent experiments (e.g., absorbance measurements over time).

Use case: Measuring absorbance at 1hr, 6hrs, and 12hrs. If absorbance at any point
exceeds a global threshold, the trial is stopped early to avoid waiting the full duration.
"""

import helper_functions as hf

# Initialize client with intermediate data support
client = hf.optimizer_init(support_intermediate_data=True)

# Configuration
ABSORBANCE_THRESHOLD = 1.5  # Global threshold for absorbance
MEASUREMENT_TIMES = [1, 6, 12]  # Hours at which to measure

# Run optimization loop
for iteration in range(5):
    parameterizations, _ = client.get_next_trials(max_trials=1)
    
    for trial_index, parameterization in parameterizations.items():
        print(f"\n--- Trial {trial_index} ---")
        print(f"Parameters: surfactant_conc={parameterization['surfactant_conc']}, "
              f"drug_conc={parameterization['drug_conc']}")
        
        # Simulate time-dependent experiment with measurements at different time points
        for time_hours in MEASUREMENT_TIMES:
            # Simulate measurement (in real use, this would be actual lab measurement)
            # For demo, use a simple calculation based on parameters
            simulated_absorbance = (
                parameterization['surfactant_conc'] + parameterization['drug_conc']
            ) / 50.0 + (time_hours / 12.0)
            
            print(f"  Time {time_hours}hr: absorbance = {simulated_absorbance:.3f}")
            
            # Report intermediate data
            hf.update_trial_with_intermediate_data(
                client=client,
                trial_index=trial_index,
                raw_data={"absorbance": (simulated_absorbance, 0.0)},
                time_step=time_hours
            )
            
            # Check if threshold is exceeded and stop early if needed
            stopped = hf.early_stop_trial_if_threshold_exceeded(
                client=client,
                trial_index=trial_index,
                metric_name="absorbance",
                threshold=ABSORBANCE_THRESHOLD,
                comparison="greater",
                reason=f"Absorbance {simulated_absorbance:.3f} exceeded threshold {ABSORBANCE_THRESHOLD} at {time_hours}hrs"
            )
            
            if stopped:
                print(f"  → Trial stopped early (threshold exceeded)")
                break
        else:
            # Trial completed without early stopping
            # Add final measurements for objectives
            final_results = {
                'absorbance': (simulated_absorbance, 0.0),
                'complexity': (8, 0.0),
                'cost': (25, 0.0),
                'performance': (0.5, 0.0)
            }
            client.complete_trial(trial_index=trial_index, raw_data=final_results)
            print(f"  → Trial completed successfully")
        
        # Save state
        client.save_to_json_file(f'optimizer/optimizer_early_stop_{iteration}.json')

# View results
df = client.get_trials_data_frame()
print("\n" + "="*70)
print("Results Summary:")
print("="*70)
print(df[['trial_index', 'trial_status', 'surfactant_conc', 'drug_conc']])
print("\nNote: Trials with ABANDONED status were stopped early due to threshold exceedance")
