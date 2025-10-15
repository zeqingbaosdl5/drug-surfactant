# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 2025-10-15: Created `mqtt_otflex_simulate_device.py` - MQTT device using opentrons.simulate
  - Follows AC dev lab OT2mqtt.py pattern but uses simulate instead of execute
  - Queue-based command processing with MQTT integration
  - Protocol generation and simulation for absorbance reading
  - Supports single and multi-wavelength reads with flexible well selection
- 2025-10-15: Created `test_mqtt_simulate_orchestrator.py` - Test orchestrator for simulation device
  - Demonstrates sending commands and receiving simulated results
  - Tests single wavelength, multi-wavelength, and single well scenarios
- 2025-10-15: Added `opentrons` to requirements.txt for protocol simulation and testing
- 2025-10-15: Created `test_opentrons_simulate.py` demonstrating protocol validation with opentrons.simulate
  - Checks if opentrons is installed and exits gracefully if not
  - Shows how to validate OT-Flex protocol syntax before execution
  - Demonstrates single and multi-wavelength absorbance reader simulation
  - Uses correct API level (2.21) and proper initialization sequence (close_lid before initialize)
  - Provides examples for testing protocol commands

### Changed
- 2025-10-15: Refactored error handling in all MQTT scripts to raise exceptions naturally
  - Replaced `sys.exit()` calls with proper exception raising (`ValueError`, `ConnectionError`)
  - Removed print statements for errors in favor of natural exception propagation
  - Improved error messages to be more descriptive
  - Scripts now follow Python best practices for error handling

- 2025-10-14: Refactored MQTT client scripts to be top-level scripts without function wrappers
  - Removed `if __name__ == "__main__"` pattern from all MQTT scripts
  - Converted `run_*` wrapper functions to direct top-level code execution
  - Scripts now run directly when executed: `mqtt_device.py`, `mqtt_orchestrator.py`, `mqtt_otflex_device.py`, `mqtt_otflex_orchestrator.py`

### Added
- 2025-10-14: HiveMQ integration test script (`test_hivemq_connection.py`) to verify MQTT broker connectivity
- 2025-10-14: `paho-mqtt` dependency for MQTT client functionality
- 2025-10-14: MQTT device-orchestrator pattern implementation based on ACC-HelloWorld microcourses
  - Basic device (`mqtt_device.py`) and orchestrator (`mqtt_orchestrator.py`) for generic MQTT communication
  - OT-Flex device (`mqtt_otflex_device.py`) for simulated robot operations
  - OT-Flex orchestrator (`mqtt_otflex_orchestrator.py`) for experiment requests with absorbance results
  - JSON-based message passing with experiment ID tracking
  - Complete documentation in `MQTT_README.md`
- 2025-10-14: Async absorbance reading capability
  - Independent plate reading at any time without running full experiments
  - Multi-wavelength spectra support (e.g., 450-650nm)
  - Flexible well selection (all wells, specific wells, or single well)
  - Test script (`test_async_absorbance.py`) demonstrating async reading
