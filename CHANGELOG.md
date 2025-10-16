# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 2025-10-15: MQTT device-orchestrator pattern for OT-Flex integration
  - `mqtt_otflex_simulate_device.py`: MQTT device using opentrons.simulate following AC dev lab OT2mqtt.py pattern
    - Uses `opentrons.simulate.get_protocol_api()` for direct opentrons function calls
    - Queue-based MQTT command processing
    - Mock absorbance reader (opentrons.simulate cannot load real module)
    - Easy toggle to real hardware with commented line showing actual module loading
    - Multi-wavelength absorbance reading support
    - Flexible well selection (all wells, specific wells, single well)
    - **Independent absorbance measurements** without requiring mixing experiments
    - **Independent mixing experiments** with drug-surfactant formulations
    - Both operations can be triggered independently via MQTT commands
  - `test_mqtt_simulate_orchestrator.py`: Test orchestrator demonstrating both independent operations
    - Absorbance commands (all wells, specific wells, single well, multi-wavelength)
    - Mixing experiment commands (component transfers and shaking)
    - Demonstrates independence of absorbance and mixing operations
  - `MQTT_README.md`: Documentation for MQTT communication pattern
  - `requirements.txt`: Added paho-mqtt>=2.1.0 and opentrons>=7.0.0
- 2025-10-14: HiveMQ integration test script (`test_hivemq_connection.py`) to verify MQTT broker connectivity

### Implementation Details
- Natural error handling with proper exceptions (ValueError, ConnectionError)
- Errors bubble up naturally without try/except wrappers
- Top-level scripts without `if __name__ == "__main__"` wrappers
- Secure TLS/SSL connection to HiveMQ Cloud (MQTT v5)
- JSON message serialization with experiment ID tracking
- Queue-based message handling with timeouts
