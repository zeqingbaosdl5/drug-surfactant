## [0.1.5] - 2026-02-09

- Enhanced trial selection diversity: now selects pairs with no overlapping surfactants, ensuring each trial uses completely distinct surfactants.

## [0.1.4] - 2026-02-09

- Fixed IndexError in pair selection: used positional index for acqf_vals access instead of DataFrame index label, to handle filtered DataFrames with non-contiguous indices.

## [0.1.3] - 2026-02-09

- Fixed parameter error in trial attachment: removed 'pair' column from params before attaching to AxClient to match search space.

## [0.1.2] - 2026-02-09

- Changed trial selection logic: now selects the highest acquisition function score from each unique surfactant pair combination, then picks the top trials from those to ensure diversity across different combinations.

## [0.1.1] - 2026-02-09

- Added diversity constraint to trial selection in Bayesian Optimization: selected trials must have at least 50 uL Euclidean distance in surfactant volume space to promote exploration.
