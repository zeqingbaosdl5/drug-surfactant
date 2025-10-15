# Using Opentrons Simulate for Protocol Testing

This document explains how to use `opentrons.simulate` to validate and test OT-Flex protocols before running them on hardware.

## Installation

```bash
pip install opentrons>=7.0.0
```

## What is opentrons.simulate?

`opentrons.simulate` is a tool that validates protocol syntax and simulates protocol execution without requiring physical hardware. It's useful for:

- **Validating protocol syntax** - Catch errors before deployment
- **Testing protocol logic** - Verify command sequences
- **Development** - Iterate quickly without hardware access
- **CI/CD** - Automated protocol testing

## Basic Usage

### Simulating a Protocol File

```python
import opentrons.simulate

# Read protocol from file
with open('protocol.py', 'r') as f:
    protocol_text = f.read()

# Simulate the protocol using StringIO for file-like object
from io import StringIO
protocol_file = StringIO(protocol_text)
runlog, bundle = opentrons.simulate.simulate(protocol_file)

# Access simulation results
print(f"Protocol: {bundle.metadata.get('protocolName') if bundle else 'N/A'}")
print(f"Commands: {len(runlog)}")
```

### What Gets Simulated

The simulator:
- ✅ Validates Python syntax
- ✅ Checks API compatibility
- ✅ Verifies labware and module loading
- ✅ Simulates liquid handling commands
- ✅ Validates deck configuration
- ❌ Does NOT perform physical movements
- ❌ Does NOT connect to actual hardware
- ❌ Does NOT return real sensor data

## Absorbance Reader Simulation

### Single Wavelength

```python
import opentrons.simulate
from io import StringIO

protocol_text = """
from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.21"}

def run(protocol: protocol_api.ProtocolContext):
    pr_mod = protocol.load_module("absorbanceReaderV1", "C3")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "D1")
    
    # Close lid before initialization (required)
    pr_mod.close_lid()
    
    # Initialize for single wavelength
    pr_mod.initialize(mode="single", wavelengths=[600])
    
    pr_mod.open_lid()
    pr_mod.close_lid()
    
    # Read plate (simulated - returns empty dict)
    pr_data = pr_mod.read()
    
    pr_mod.open_lid()
"""

protocol_file = StringIO(protocol_text)
runlog, bundle = opentrons.simulate.simulate(protocol_file)
```

### Multi-Wavelength

```python
# Close lid before initialization (required)
pr_mod.close_lid()

# Initialize for multiple wavelengths
pr_mod.initialize(mode="multi", wavelengths=[450, 500, 550, 600, 650])

# Read returns data structure like:
# pr_data = {
#     450: {"A1": value, "A2": value, ...},
#     500: {"A1": value, "A2": value, ...},
#     ...
# }
```

## Testing Script

Run the included test script:

```bash
python test_opentrons_simulate.py
```

This demonstrates:
- Basic protocol simulation
- Multi-wavelength absorbance reading
- Command inspection
- Error handling

## Integration with MQTT Device

The MQTT OT-Flex device (`mqtt_otflex_device.py`) simulates absorbance readings. To integrate with real Opentrons hardware:

1. **Protocol Generation**: Convert experiment requests to Opentrons protocols
2. **Validation**: Use `opentrons.simulate` to validate before execution
3. **Execution**: Deploy to actual OT-Flex robot
4. **Data Return**: Parse actual absorbance data and send via MQTT

Example workflow:

```python
import opentrons.simulate
from io import StringIO

# 1. Generate protocol from MQTT request
protocol_text = generate_protocol(experiment_request)

# 2. Validate with simulate
try:
    protocol_file = StringIO(protocol_text)
    runlog, bundle = opentrons.simulate.simulate(protocol_file)
    print("Protocol is valid")
except Exception as e:
    raise ValueError(f"Invalid protocol: {e}")

# 3. Execute on hardware (when connected to robot)
# result = execute.execute(protocol_text, robot_context)

# 4. Return results via MQTT
# send_mqtt_response(result)
```

## Limitations

### Simulation Limitations
- Hardware modules (plate reader, heater-shaker) return empty/mock data
- No actual liquid tracking
- No collision detection
- No real-time execution

### When to Use Real Hardware
- Final validation before production
- Actual absorbance measurements
- Precise liquid handling verification
- Integration testing with other equipment

## Resources

- [Opentrons Python API](https://docs.opentrons.com/v2/)
- [Simulate API Reference](https://docs.opentrons.com/v2/simulate.html)
- [Protocol API](https://docs.opentrons.com/v2/new_protocol_api.html)
- [Absorbance Reader Module](https://docs.opentrons.com/v2/modules/absorbance_plate_reader.html)

## Troubleshooting

### Import Error
```
ImportError: No module named 'opentrons'
```
**Solution**: Install with `pip install opentrons`

### API Level Mismatch
```
Error: API level 2.19 not supported
```
**Solution**: Update to API level 2.21 or higher for absorbance reader support

### Module Initialization Error
```
CannotPerformModuleAction: Cannot perform Initialize action on Absorbance Reader without calling `.close_lid()` first.
```
**Solution**: Call `pr_mod.close_lid()` before `pr_mod.initialize()`

### Module Not Found
```
ModuleNotFoundError: Module 'absorbanceReaderV1' not found
```
**Solution**: Check module name spelling and API compatibility

## See Also

- `mqtt_otflex_device.py` - MQTT device for OT-Flex operations
- `test_opentrons_simulate.py` - Example simulation scripts
- `MQTT_README.md` - MQTT communication patterns
