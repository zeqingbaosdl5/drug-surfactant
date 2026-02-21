## [0.1.8] - 2026-02-20
- `drug_visualization`: updated colors to Office 2019 accent palette (`#4472C4`/`#70AD47`/`#C00000`/`#7030A0`)
- `drug_visualization`: fixed value label placement (bottom-up collision detection prevents upward stacking drift)
- `drug_visualization`: background bands now extend ±0.5 data units beyond outer axes using `Rectangle` patches
- `drug_visualization`: sigmoid segments clipped ±0.10 from each axis for a "passes-through" visual gap effect

## [0.1.7] - 2026-02-20

- Added `drug_visualization(drug_dict)` to `data_analysis.ipynb`: parallel coordinates plot using PCHIP interpolation (gentle S-curves, no overshoot), per-axis 20% padding normalisation, alternating #ECEFF8/#F7F9FC background bands, two-layer glow fill, solid curves, white-bordered circle markers, nudged value labels, and bottom-center dashed legend.

## [0.1.6] - 2026-02-19

- Replaced single greedy dropdown with three separate iteration-count inputs (High, Medium, Low greedy iterations) in the launcher UI. The UI validates that their sum equals the total number of iterations. In `drug_surfactant_bo.py`, greedy level is now determined per-iteration: iteration 0 remains random; subsequent iterations run as "high" for the first H iters, "medium" for the next M, and "low" for the remaining L.

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
