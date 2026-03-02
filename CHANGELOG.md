## [0.2.4] - 2026-03-02
- `plot_drug` / `plot_shap`: SHAP dot colors now use absolute surfactant concentration [0–800 µL] with `Normalize(vmin=0, vmax=800, clip=True)` — 0=blue, 400=white, ≥800=red. SHAP colorbar restyled to match surface colorbar (ScalarMappable, ticks 0/400/≥800, label "Surfactant conc. (µL)"). Added "a)" / "b)" panel labels to `plot_drug`. Tightened gap between panels. Removed `ColorbarBase` import.

## [0.2.3] - 2026-03-02
- Refactored cell 9: extracted `_draw_shap_panel` and `_draw_surface_panel` as private renderers; added `_compute_surface_grid` and `_top_shap_features` helpers; moved rc params to module-level `_RC`; added `plot_drug(drug)` which computes SHAP + GP once and renders both panels side-by-side in a single 15×5.8 in figure.

## [0.2.2] - 2026-03-02
- `plot_response_surface`: switched from `contourf` to `pcolormesh(shading='gouraud')` for smooth bilinear gradient rendering; replaced `RdYlGn_r` with `_SHAP_CMAP` (blue→crimson) to match SHAP plot; removed `extend='both'` for standard square colorbar ends.

## [0.2.1] - 2026-03-02
- `plot_shap`: redesigned to publication quality — custom two-panel layout (beeswarm + standalone colorbar), `RdBu_r` colormap, clean spines, dotted horizontal grid, semi-bold title, 300 DPI export. `SURF_PARAMS`/`SURF_DISPLAY` now derived from `surfactant_dict` instead of being hardcoded.

## [0.2.0] - 2026-03-02
- Replaced GBR surrogate with the actual Ax BoTorch GP in `plot_shap` and `plot_response_surface`. GP is refitted via `Models.BOTORCH_MODULAR` on each drug's experiment data. SHAP uses `KernelExplainer` (model-agnostic) with k-means background summarisation. Both functions take a single drug abbreviation as input.

## [0.1.9] - 2026-03-02
- Added surrogate-model analysis section to `data_analysis.ipynb`: 6 analysis functions using a GBR surrogate fit per drug — (1) optimization convergence curve, (2) 5-fold CV R² bar chart, (3) success vs failed surfactant concentration profiles, (4) cross-drug mean |SHAP| bar comparison, (5) per-drug SHAP beeswarm summary plots, (6) 2D response surface slices for the top-2 SHAP features. Figures saved to `data_analysis/figures/`.

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
