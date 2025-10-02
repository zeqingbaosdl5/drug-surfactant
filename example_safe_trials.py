"""
Example: Using safe_complete_trial for robust experiment handling

This script demonstrates how to use the safe_complete_trial function
to handle failed experiments when parameters lead to invalid experimental conditions.
"""

import helper_functions as hf

# Initialize the Ax client
ax_client = hf.optimizer_init()

# Run optimization with automatic failure handling
for i in range(5):
    parameterizations, _ = ax_client.get_next_trials(max_trials=1)
    
    for trial_index, parameterization in parameterizations.items():
        # Use safe_complete_trial which automatically handles failures
        success = hf.safe_complete_trial(
            ax_client=ax_client,
            trial_index=trial_index,
            parameterization=parameterization
        )
        
        print(f"Trial {trial_index}: {'✓ Success' if success else '✗ Failed'}")
        
        # Save state after each trial
        ax_client.save_to_json_file(f'optimizer/optimizer_{i}.json')

# View results
df = ax_client.get_trials_data_frame()
print("\nResults:")
print(df[['trial_index', 'trial_status']])
