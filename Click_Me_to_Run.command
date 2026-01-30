#!/bin/bash
cd "$(dirname "$0")"

# Attempt to locate Conda installation in common paths (Portable)
CONDA_BASE_PATHS=(
    "$HOME/opt/anaconda3"
    "$HOME/anaconda3"
    "$HOME/opt/miniconda3"
    "$HOME/miniconda3"
    "/opt/anaconda3"
    "/opt/miniconda3"
)

FOUND_CONDA=0
for base in "${CONDA_BASE_PATHS[@]}"; do
    if [ -f "$base/etc/profile.d/conda.sh" ]; then
        source "$base/etc/profile.d/conda.sh"
        FOUND_CONDA=1
        break
    fi
done

# Fallback
if [ $FOUND_CONDA -eq 0 ]; then
    if command -v conda &> /dev/null; then
        eval "$(conda shell.bash hook)"
    else
        echo "Error: Could not find Conda."
        exit 1
    fi
fi

conda activate drug-surfactant
python governing_files/launcher_ui.py
