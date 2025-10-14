# MQTT Device-Orchestrator Pattern Implementation

This directory contains a Minimum Working Example (MWE) of the MQTT device-orchestrator pattern for self-driving laboratories, based on the [ACC-HelloWorld microcourses](https://github.com/AccelerationConsortium/ac-microcourses).

## Overview

The implementation follows a publish-subscribe pattern where:
- **Device**: Receives commands via MQTT, executes operations, and publishes results
- **Orchestrator**: Sends commands to devices and receives/processes results

## Files

### Basic Device-Orchestrator Pattern
- `mqtt_device.py` - Generic MQTT device that responds to commands with sensor data
- `mqtt_orchestrator.py` - Generic orchestrator that sends commands and collects results

### OT-Flex Integration
- `mqtt_otflex_device.py` - OT-Flex robot simulation that handles experiment requests
- `mqtt_otflex_orchestrator.py` - Orchestrator that sends experiment requests and receives absorbance data

### Testing
- `test_mqtt_all_stages.py` - Comprehensive test script that runs all three stages of the implementation
- `test_async_absorbance.py` - Test script demonstrating async absorbance reading capability

## Setup

### Prerequisites
```bash
pip install paho-mqtt>=2.1.0
```

### Environment Variables
Set the following environment variables for HiveMQ connection:
```bash
export HIVEMQ_HOST="your-broker-host"
export HIVEMQ_USERNAME="your-username"
export HIVEMQ_PASSWORD="your-password"
```

## Usage

### Testing Basic Communication

1. Start the device in one terminal:
```bash
python mqtt_device.py
```

2. Run the orchestrator in another terminal:
```bash
python mqtt_orchestrator.py
```

The orchestrator will send test commands and the device will respond with simulated sensor data.

### Testing OT-Flex Integration

1. Start the OT-Flex device:
```bash
python mqtt_otflex_device.py
```

2. Run the OT-Flex orchestrator:
```bash
python mqtt_otflex_orchestrator.py
```

The orchestrator sends an experiment request with drug-surfactant formulation parameters, and the device simulates:
- Loading the protocol
- Preparing reagents
- Dispensing liquids
- Shaking the plate
- Reading absorbance at 600nm

Results are saved to `otflex_experiment_results.json`.

### Running All Tests

To run all three stages sequentially:
```bash
python test_mqtt_all_stages.py
```

This script will:
1. Test basic device-orchestrator communication
2. Verify JSON message passing (integrated in stage 1)
3. Test OT-Flex integration with experiment requests and absorbance results

### Testing Async Absorbance Reading

To test standalone absorbance reading capability:

1. Start the OT-Flex device:
```bash
python mqtt_otflex_device.py
```

2. In another terminal, run the async test:
```bash
python test_async_absorbance.py
```

This demonstrates three async reading scenarios:
- Reading all 96 wells at a single wavelength
- Reading specific wells at multiple wavelengths (450-650nm)
- Reading a single well

Results are saved to `async_absorbance_results.json`.

## MQTT Topics

### Basic Pattern
- Command topic: `sdl/device/{device_id}/command`
- Data topic: `sdl/device/{device_id}/data`

### OT-Flex Pattern
- Request topic: `sdl/otflex/{device_id}/experiment/request`
- Results topic: `sdl/otflex/{device_id}/experiment/results`

## Message Format

### Basic Device Commands
```json
{
  "operation": "read_temperature",
  "params": {},
  "experiment_id": "d8600f87"
}
```

### Basic Device Response
```json
{
  "command": {...},
  "sensor_data": {"temperature": 25.5},
  "experiment_id": "d8600f87",
  "timestamp": 1760484171.996
}
```

### OT-Flex Experiment Request
```json
{
  "experiment_id": "45b523efb898589a",
  "operation": "run_drug_surfactant_protocol",
  "params": {
    "data": [
      {
        "trial_index": "0",
        "drug_name": "IBP",
        "s1": "120.0",
        "s6": "168.0",
        "water": "396.0",
        "IBP": "180.0",
        ...
      }
    ],
    "wavelength": 600,
    "shake_speed": 1000,
    "shake_time": 5
  }
}
```

### OT-Flex Results
```json
{
  "experiment_id": "45b523efb898589a",
  "status": "completed",
  "absorbance_data": {
    "well_1": {
      "absorbance_600nm": 0.5601,
      "parameters": {...}
    },
    "well_2": {
      "absorbance_600nm": 0.6204,
      "parameters": {...}
    }
  },
  "device_id": "otflex_001",
  "timestamp": 1760484323.603
}
```

### Async Absorbance Request
```json
{
  "experiment_id": "0433597597317b4f",
  "operation": "read_absorbance",
  "params": {
    "wavelengths": [450, 500, 550, 600, 650],
    "wells": ["A1", "A2", "B1", "B2"]
  }
}
```

### Async Absorbance Response
```json
{
  "experiment_id": "0433597597317b4f",
  "operation": "read_absorbance",
  "absorbance_spectra": {
    "A1": {
      "450": 0.3797,
      "500": 0.3227,
      "550": 0.3141,
      "600": 0.4454,
      "650": 0.3705
    },
    "A2": {...}
  },
  "wavelengths": [450, 500, 550, 600, 650],
  "num_wells": 4,
  "status": "completed",
  "timestamp": 1760484800.123,
  "device_id": "otflex_001"
}
```

## Key Features

- ✅ Secure TLS/SSL connection to HiveMQ Cloud
- ✅ MQTT v5 protocol support
- ✅ JSON message serialization
- ✅ Experiment ID tracking for request-response matching
- ✅ Queue-based message handling
- ✅ Timeout and error handling
- ✅ Simulated OT-Flex operations (liquid handling, shaking, absorbance reading)
- ✅ **Async absorbance reading** - Read plate independently at any time
- ✅ **Multi-wavelength spectra** - Support for reading at multiple wavelengths simultaneously
- ✅ **Flexible well selection** - Read all wells, specific wells, or single wells

## References

- [ACC-HelloWorld Hardware-Software Communication](https://github.com/ACC-HelloWorld/4-hardware-software-communication)
- [AC Microcourses - Hello World](https://github.com/AccelerationConsortium/ac-microcourses)
- [HiveMQ MQTT Broker](https://www.hivemq.com/)
