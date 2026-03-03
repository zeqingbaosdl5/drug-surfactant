# Drug-Surfactant Nanoformulation Optimizer

An automated self-driving laboratory (SDL) for discovering surfactants that solubilize poorly water-soluble drugs using the minimum possible surfactant volume. A Bayesian optimization (BO) loop proposes formulations, an Opentrons Flex robot physically prepares them, and an Absorbance Reader Module measures drug solubilization — all without human intervention.

## Overview

Poorly water-soluble drugs often require surfactant excipients to form stable "solutions". This system searches for the optimal two-surfactant combination and their volumes that keeps a drug dissolved while minimizing total surfactant use. 
Case study drugs: **Ibuprofen (IBP)**, **Lovastatin (LOV)**, **Diclofenac (DCF)**, and **Griseofulvin (GLV)**.

Each iteration of the loop:
1. Uses prior results to fit a Gaussian process surrogate (via [Ax](https://ax.dev/) / [BoTorch](https://botorch.org/))
2. Proposes new candidate formulations and registers them as trials
3. Auto-generates an Opentrons Flex protocol and uploads it to the robot
4. Waits for the robot to prepare, mix, dissolve, and read absorbance
5. Downloads results, evaluates success, and updates the optimizer

## Repository Structure

```
governing_files/         # Core scripts and labware definitions
    launcher_ui.py           # Tkinter GUI — configure and launch experiments
    drug_surfactant_bo.py    # Main BO orchestration loop
    helper_functions.py      # Volume calculations, absorbance processing, utilities
    protocol_template.py     # Opentrons Flex protocol template (filled per iteration)
    opentrons_http_client.py # Low-level Opentrons HTTP API client
    opentrons_http_otflex_iA_mwe.py  # Upload, run, and poll a protocol on the robot
    allenlab_8_wellplate_20000ul.json         # Custom 8-well stock plate labware
    corning_96_wellplate_360ul_flat_new.json  # Custom 96-well plate labware

Click_Me_to_Run.command  # macOS launcher (activates conda env, opens GUI)

experiments_template/    # Template folder structure for new experiment dates
smoketest_output/        # Output folder for smoke test (no-robot) runs
2026-02-19/              # Case study on IBP
2026-02-20/              # Case study on LOV
2026-02-23/              # Case study on DCF
2026-02-26/              # Case study on GLV
data_analysis/
    data_analysis.ipynb  # Notebook for post-hoc analysis and visualization
```

Each dated experiment folder contains:

```
YYYY-MM-DD/
    experiment_parameters.csv   # Logged copy of all run configuration
    tip_positions.json          # Tip state (for resuming mid-experiment)
    well_positions.json         # Plate/deep-well state (for resuming)
    optimizer/
        design_iN.csv           # Proposed formulations for iteration N
        optimizer_N.json        # Ax state before iteration N
        optimizer_N_loaded.json # Ax state after completing iteration N
    protocols/
        otflex_iN.py            # Auto-generated robot protocol for iteration N
    raw_data/
        raw_absorbance_iN.csv   # 8×12 absorbance plate reading from robot
    results/
        viewer_results_iN_*.csv # Full per-trial results with volumes and outcomes
```

## Hardware Requirements

| Hardware | Purpose |
|---|---|
| Opentrons Flex robot | Liquid handling (pipetting, gripper for plate moves) |
| Flex 1-channel 1000 µL pipette | Dispensing surfactants and water (> 40 µL) |
| Flex 1-channel 50 µL pipette | Dispensing drugs and small volumes (≤ 40 µL) |
| Flex 96-filter tip racks (1000 µL ×2, 50 µL ×1) | Disposable tips |
| Heater-Shaker Module V1 | Mixing formulations in the deep-well plate |
| Absorbance Reader Module V1 | Measuring turbidity at 600 nm |
| Allen Lab 8-well plate (20 mL) ×2 | Stock solutions: 8 surfactants + 4 drugs/DMSO/water |
| Corning 96-well flat plate (360 µL) ×2 | Experimental plate + deep-well plate on heater-shaker |
| macOS host computer | Running BO, GUI, and robot communication |

The host connects to the robot over **Ethernet** at `http://169.254.40.153:31950` (default) or WiFi at `http://192.168.0.5:31950`. Override via the `OPENTRONS_BASE_URL` environment variable.

## Software Requirements

Requires a conda environment named `drug-surfactant`. Key packages:

| Package | Purpose |
|---|---|
| `ax-platform` | Bayesian optimization service layer |
| `botorch` | Gaussian process surrogate + acquisition functions |
| `torch` | Required by BoTorch |
| `pandas` | CSV handling for designs and results |
| `numpy` | Numerical computations |
| `requests` | HTTP communication with Opentrons Flex API |
| `tkinter` | GUI launcher (standard library) |


## Usage

### GUI (recommended)

Double-click `Click_Me_to_Run.command` on macOS. This activates the `drug-surfactant` conda environment and opens the configuration GUI.

In the GUI:
- Set the experiment folder name (e.g., today's date)
- Configure starting tip and well positions (for resuming a run)
- Set all optimization parameters (see below)
- Click **LAUNCH EXPERIMENT**

Live console output is streamed directly in the GUI window.


## Key Parameters

| Parameter | Default | Description |
|---|---|---|
| `NUM_ITERATIONS` | 10 | Total BO iterations |
| `TRIALS_PER_ITERATION` | 3 | New formulations tested per iteration (iter 1+) |
| `NUM_RANDOM_TRIALS` | 9 | Random seed formulations in iteration 0 |
| `REPLICATES` | 2 | Replicate wells per formulation on the plate |
| `ABSORBANCE_THRESHOLD` | 0.06 | AU at 600 nm — below this = formulation is clear |
| `SURFACTANT_VOL_REDUCTION` | 10 | % reduction applied to best known volume each iteration |
| `DRUG_CHOICES` | IBP | Comma-separated drugs to study (IBP, LOV, DCF, GLV) |
| `PUNISHMENT_FACTOR` | 1 | Volume multiplier reported to Ax for failed (cloudy) trials |
| `DELAY_TIME` | 60 | Minutes to wait between mixing and absorbance reading |
| `GREEDY_HIGH_ITERS` | 4 | First N iterations — high-diversity candidate selection |
| `GREEDY_MEDIUM_ITERS` | 4 | Next N iterations — medium-diversity selection |
| `GREEDY_LOW_ITERS` | 2 | Final N iterations — low-diversity (fully greedy) selection |

## Smoke Test (No Robot)

Check **Smoke Test** in the GUI (or set `SMOKE_TEST=1`) to run a full dry-run without a physical robot. Robot calls are mocked and synthetic absorbance values are generated deterministically, enabling complete pipeline testing on any laptop.

Output is written to `smoketest_output/`.

## Resuming a Run

The system saves tip positions, well positions, and optimizer state after every iteration. To resume a partially completed experiment, set the experiment folder to the existing dated folder and specify the correct starting tip rack and plate positions in the GUI. The optimizer will automatically reload from the latest `optimizer_N_loaded.json` checkpoint.

## How the BO Loop Works

```
Iteration 0
  └── Random sampling: NUM_RANDOM_TRIALS candidates chosen at random
        └── Register trials → generate protocol → run robot → process absorbance → update Ax

Iteration 1+
  └── Fit GP surrogate on all completed trials
        └── Evaluate acquisition function over all feasible (s_i, s_j, volume) candidates
              └── Select TRIALS_PER_ITERATION diverse candidates (greedy diversity filter)
                    └── Tighten volume budget by SURFACTANT_VOL_REDUCTION% of best-so-far
                          └── Register trials → generate protocol → run robot → process absorbance → update Ax
```

The objective is to **minimize total surfactant volume** subject to the formulation being optically clear. Successful formulations report their actual volume; failed formulations are penalized by `PUNISHMENT_FACTOR`.

## License

See [LICENSE](LICENSE).
