# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- 2025-12-17: Refactored Opentrons HTTP helper functions into `experiments/opentrons_http_client.py`, kept the absorbance workflow in `experiments/opentrons_http_mwe.py`, added `experiments/opentrons_http_otflex_iA_mwe.py` runner, and added runtime float parameters to `experiments/20250912-Plate Interpretation/otflex_iA.py`. Added `run_protocol` helper to reduce boilerplate in MWE scripts.
- 2025-12-17: Added runtime string parameters for starting well positions (next_plate_well and next_deepplate_well) in otflex_iA.py, allowing dynamic well selection via opentrons_http_otflex_iA_mwe.py, with choices restricted to wells F1 through H12.
- 2025-12-18: Modified output CSV file saving in `opentrons_http_otflex_iA_mwe.py` to use a `data` subdirectory to avoid cluttering the experiments folder.
- 2025-12-18: Added `drug_surfactant_bo.py` to run one closed-loop optimization iteration end-to-end (optimizer → volume conversion → `run_otflex_iA` → absorbance processing → update optimizer).

### Added
- 2025-10-14: HiveMQ integration test script (`test_hivemq_connection.py`) to verify MQTT broker connectivity
- 2025-10-14: `paho-mqtt` dependency for MQTT client functionality

### Fixed
- 2025-12-18: Improved error handling and code quality in Opentrons HTTP client: added HTTP error checking with `response.raise_for_status()` to all request functions, replaced bare except clauses with specific exception types (ValueError, TypeError), made hardcoded paths and IP addresses configurable via environment variables, removed unused variable assignment and debug code
- 2025-12-17: Added stackingOffsetWithLabware to corning_96_wellplate_360ul_flat_new.json to enable stacking on opentrons_universal_flat_adapter, resolving LabwareCannotBeStackedError in protocol analysis. Updated opentrons_http_client.py to only raise on non-empty error lists.
- 2025-11-06: Corrected runtime parameter implementation in `absorbance_protocol_mwe.py` to use proper `add_parameters()` function and `protocol.params` accessor according to Opentrons API documentation
