# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 2025-10-14: HiveMQ integration test script (`test_hivemq_connection.py`) to verify MQTT broker connectivity
- 2025-10-14: `paho-mqtt` dependency for MQTT client functionality

### Fixed
- 2025-11-06: Corrected runtime parameter implementation in `absorbance_protocol_mwe.py` to use proper `add_parameters()` function and `protocol.params` accessor according to Opentrons API documentation
