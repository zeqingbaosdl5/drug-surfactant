#!/bin/bash
source /Users/zeqing/opt/anaconda3/bin/activate drug_surfactant
cd "$(dirname "$0")"
python governing_files/launcher_ui.py
