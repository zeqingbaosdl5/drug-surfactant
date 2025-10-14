# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
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
