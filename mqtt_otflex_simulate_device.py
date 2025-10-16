#!/usr/bin/env python3
"""
MQTT OT-Flex Device with Protocol Simulation
Based on AC dev lab OT2mqtt.py pattern but using opentrons.simulate instead of opentrons.execute.
This directly uses opentrons functions rather than creating protocol strings.
"""
import json
import sys
from queue import Empty, Queue
from time import sleep
import os

import opentrons.simulate

import paho.mqtt.client as mqtt

# Get protocol API for simulation (similar to opentrons.execute.get_protocol_api())
protocol = opentrons.simulate.get_protocol_api("2.21")

# Device configuration
DEVICE_ID = "otflex_sim_001"

# MQTT Broker Configuration (using environment variables)
host = os.environ.get('HIVEMQ_HOST')
username = os.environ.get('HIVEMQ_USERNAME')
password = os.environ.get('HIVEMQ_PASSWORD')

if not all([host, username, password]):
    missing = []
    if not host:
        missing.append('HIVEMQ_HOST')
    if not username:
        missing.append('HIVEMQ_USERNAME')
    if not password:
        missing.append('HIVEMQ_PASSWORD')
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# MQTT Topics
COMMAND_TOPIC = f"command/otflex/{DEVICE_ID}/protocol"
STATUS_TOPIC = f"status/otflex/{DEVICE_ID}/complete"

# Initialize MQTT client and command queue
client = mqtt.Client(protocol=mqtt.MQTTv5)
client.tls_set()
client.username_pw_set(username, password)

command_queue = Queue()

print("Initializing simulated OT-Flex device...")
print("NOTE: Using mock absorbance reader due to opentrons.simulate limitations")
print("The absorbance reader module has restrictions in simulation mode.")

# Robot setup - following drug_surfactant_otflex_template.py pattern
# Load tip racks
tip1000_1 = protocol.load_labware(load_name="opentrons_flex_96_filtertiprack_1000ul", location="B1")
tip1000_2 = protocol.load_labware(load_name="opentrons_flex_96_filtertiprack_1000ul", location="A1")
tip50 = protocol.load_labware(load_name="opentrons_flex_96_filtertiprack_50ul", location="B2")
print("Tip racks loaded")

# Load heater shaker module (D3 slot)
# For simulation: Mock heater shaker due to limitations
# For real hardware: hs_mod = protocol.load_module("heaterShakerModuleV1", "D3")
class MockHeaterShaker:
    def close_labware_latch(self):
        print("  [MOCK] Closing heater-shaker latch")
    def open_labware_latch(self):
        print("  [MOCK] Opening heater-shaker latch")
    def set_and_wait_for_shake_speed(self, speed):
        print(f"  [MOCK] Setting shake speed to {speed} rpm")
    def deactivate_shaker(self):
        print("  [MOCK] Deactivating shaker")
    def load_adapter(self, name):
        # Return the adapter which can load labware
        return protocol.load_labware("opentrons_universal_flat_adapter", "D3")

hs_mod = MockHeaterShaker()
# For real hardware: Uncomment line below and comment out mock above
# hs_mod = protocol.load_module("heaterShakerModuleV1", "D3")
print("Heater-shaker module loaded (mocked for simulation)")

# Load pipettes
pipette_low = protocol.load_instrument(instrument_name="flex_1channel_50", mount="right", tip_racks=[tip50])
pipette_high = protocol.load_instrument(instrument_name="flex_1channel_1000", mount="left", tip_racks=[tip1000_1, tip1000_2])
print("Pipettes loaded: 50µL (right), 1000µL (left)")

# Load source labware
surfactant_stock_1 = protocol.load_labware(load_name="opentrons_24_tuberack_nest_2ml_snapcap", location="C1")
surfactant_drug_stock = protocol.load_labware(load_name="opentrons_24_tuberack_nest_2ml_snapcap", location="C2")
print("Source labware loaded")

# Define source wells (simplified compared to template - using tube rack instead of 8-well plates)
sources = {
    's1': surfactant_stock_1['A1'],
    's2': surfactant_stock_1['A2'],
    's3': surfactant_stock_1['A3'],
    's4': surfactant_stock_1['A4'],
    's5': surfactant_stock_1['A5'],
    's6': surfactant_stock_1['A6'],
    's7': surfactant_stock_1['B1'],
    's8': surfactant_stock_1['B2'],
    'water': surfactant_drug_stock['A1'],
    'IBP': surfactant_drug_stock['A2'],
    'LOV': surfactant_drug_stock['A3'],
    'DCF': surfactant_drug_stock['A4'],
    'GLV': surfactant_drug_stock['A5'],
}

# Load well plates
plate = protocol.load_labware(load_name="corning_96_wellplate_360ul_flat", location='D1')
deepplate = protocol.load_labware(load_name="corning_96_wellplate_360ul_flat", location='D2')
print("Well plates loaded")

# Load trash bin
trash = protocol.load_trash_bin(location="A3")
print("Trash bin loaded")

print("Labware loaded successfully")

# Mock the pr_mod object for simulation purposes
class MockAbsorbanceReader:
    def close_lid(self):
        print("  [MOCK] Closing absorbance reader lid")
    
    def initialize(self, mode, wavelengths):
        print(f"  [MOCK] Initializing reader in {mode} mode for wavelengths: {wavelengths}")
    
    def open_lid(self):
        print("  [MOCK] Opening absorbance reader lid")
    
    def read(self):
        print("  [MOCK] Reading absorbance data")
        # Return mock data structure matching real reader output
        import random
        result = {}
        for wl in [450, 500, 550, 600, 650]:
            result[wl] = {}
        return result

# For simulation: Use mock absorbance reader due to opentrons.simulate limitations
pr_mod = MockAbsorbanceReader()
# For real hardware: Uncomment the line below and comment out the mock reader above
# pr_mod = protocol.load_module("absorbanceReaderV1", "C3")
print("Mock absorbance reader created (simulated hardware)")
print("Labware loaded successfully")


# MQTT Callbacks
def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected to MQTT Broker with result code", rc)
    client.subscribe(COMMAND_TOPIC, qos=2)


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")
    print(f"Received message on topic {msg.topic}: {payload}")
    try:
        payload = json.loads(payload)
        if msg.topic == COMMAND_TOPIC:
            command_queue.put(payload)
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON payload: {e}")


client.on_connect = on_connect
client.on_message = on_message
client.connect(host, 8883)
client.loop_start()

print("MQTT client connected and ready")


def read_absorbance(wavelengths, wells):
    """
    Read absorbance using opentrons functions directly.
    
    Parameters
    ----------
    wavelengths : list
        List of wavelengths to read
    wells : str or list
        Wells to read ('all' or list of well names)
    
    Returns
    -------
    dict
        Absorbance data organized by well
    """
    print(f"Reading absorbance:")
    print(f"  Wavelengths: {wavelengths}")
    print(f"  Wells: {wells}")
    
    # Close lid before initialization (required)
    pr_mod.close_lid()
    print("  Lid closed")
    
    # Initialize for wavelength(s)
    if len(wavelengths) == 1:
        pr_mod.initialize(mode="single", wavelengths=wavelengths)
        print(f"  Initialized in single mode: {wavelengths}")
    else:
        pr_mod.initialize(mode="multi", wavelengths=wavelengths)
        print(f"  Initialized in multi mode: {wavelengths}")
    
    # Open lid to load plate (would use gripper on real robot)
    pr_mod.open_lid()
    print("  Lid opened for plate loading")
    
    # Close lid for reading
    pr_mod.close_lid()
    print("  Lid closed for reading")
    
    # Read the plate - this returns actual data structure from opentrons
    pr_data = pr_mod.read()
    print(f"  Plate read complete")
    
    # Open lid when done
    pr_mod.open_lid()
    print("  Lid opened after reading")
    
    # Process the data based on wells requested
    absorbance_data = {}
    
    if wells == 'all':
        # Read all 96 wells
        for row in 'ABCDEFGH':
            for col in range(1, 13):
                well_id = f"{row}{col}"
                absorbance_data[well_id] = {}
                for wl in wavelengths:
                    # In simulation, pr_data may be empty or have mock values
                    # Access: pr_data[wavelength][well_name]
                    if pr_data and wl in pr_data and well_id in pr_data[wl]:
                        absorbance_data[well_id][wl] = pr_data[wl][well_id]
                    else:
                        # Mock data for simulation
                        absorbance_data[well_id][wl] = round(0.1 + (hash(f"{well_id}{wl}") % 100) / 200, 4)
    else:
        # Read specific wells
        for well_id in wells:
            absorbance_data[well_id] = {}
            for wl in wavelengths:
                if pr_data and wl in pr_data and well_id in pr_data[wl]:
                    absorbance_data[well_id][wl] = pr_data[wl][well_id]
                else:
                    # Mock data for simulation
                    absorbance_data[well_id][wl] = round(0.1 + (hash(f"{well_id}{wl}") % 100) / 200, 4)
    
    return absorbance_data


def handle_absorbance_command(payload):
    """
    Handle absorbance reading command using opentrons functions directly.
    
    Parameters
    ----------
    payload : dict
        Command payload with wavelengths and wells
    """
    session_id = payload.get("session_id", "unknown")
    experiment_id = payload.get("experiment_id", "unknown")
    command = payload.get("command", {})
    
    wavelengths = command.get("wavelengths", [600])
    wells = command.get("wells", "all")
    
    print(f"\nProcessing absorbance command:")
    print(f"  Experiment ID: {experiment_id}")
    print(f"  Session ID: {session_id}")
    
    try:
        # Use opentrons functions directly
        absorbance_data = read_absorbance(wavelengths, wells)
        
        print(f"Absorbance read completed successfully")
        print(f"  Wells read: {len(absorbance_data)}")
        
        # Send results back
        response_payload = {
            "status": "completed",
            "experiment_id": experiment_id,
            "session_id": session_id,
            "absorbance_data": absorbance_data,
            "wavelengths": wavelengths,
            "num_wells": len(absorbance_data)
        }
        
        response = json.dumps(response_payload)
        client.publish(STATUS_TOPIC, response, qos=2)
        print(f"Results published to {STATUS_TOPIC}\n")
        
    except Exception as e:
        print(f"Error processing command: {e}")
        error_payload = {
            "status": "error",
            "experiment_id": experiment_id,
            "session_id": session_id,
            "error": str(e)
        }
        error_response = json.dumps(error_payload)
        client.publish(STATUS_TOPIC, error_response, qos=2)


def pipette_selection(vol):
    """Select appropriate pipette based on volume."""
    if vol <= 40:
        return pipette_low
    else:
        return pipette_high


def run_mixing_experiment(formulation, target_well="A1"):
    """
    Run a mixing experiment using real Opentrons API operations.
    Based on drug_surfactant_otflex_template.py pattern.
    
    Parameters
    ----------
    formulation : dict
        Formulation with volumes for each component
        Example: {"s1": 120.0, "s6": 168.0, "water": 396.0, "IBP": 180.0}
    target_well : str
        Target well in deepplate for mixing, default "A1"
    
    Returns
    -------
    dict
        Summary of mixing operations
    """
    print(f"Running mixing experiment:")
    print(f"  Formulation: {formulation}")
    print(f"  Target well: {target_well}")
    
    operations = []
    
    # Set well bottom clearances for all pipettes (from template)
    for pipette in [pipette_low, pipette_high]:
        pipette.well_bottom_clearance.dispense = 25
        pipette.well_bottom_clearance.aspirate = 2
    
    # Sort components to process in logical order
    components = sorted(formulation.items(), key=lambda x: x[0])
    
    # Transfer each component to deepplate well
    for component, volume in components:
        if volume > 0:
            # Select pipette based on volume
            pipette = pipette_selection(volume)
            print(f"  Transferring {volume} µL of {component} using {pipette.name}")
            
            # Pick up tip
            pipette.pick_up_tip()
            
            # Set dispense flow rate (from template)
            pipette_high.flow_rate.dispense = 50
            
            # Determine air gap volume (from template)
            air_gap_vol = 55 if pipette == pipette_high else 10
            
            # Close heater-shaker latch before transfer (from template)
            hs_mod.close_labware_latch()
            
            # Transfer with air gap
            pipette.transfer(
                volume,
                sources[component],
                deepplate[target_well],
                new_tip='never',
                air_gap=air_gap_vol
            )
            
            # Blow out and touch tip (from template)
            pipette.blow_out(deepplate[target_well].bottom(z=25))
            pipette.touch_tip(deepplate[target_well], v_offset=15)
            
            # Drop tip
            pipette.drop_tip()
            
            operations.append({
                "component": component,
                "volume": volume,
                "pipette": pipette.name,
                "action": "transfer"
            })
    
    # Shake the deepplate to mix (from template pattern)
    print(f"  Mixing on heater shaker at 1000 rpm for 5 minutes")
    hs_mod.close_labware_latch()
    hs_mod.set_and_wait_for_shake_speed(1000)
    protocol.delay(minutes=5)
    hs_mod.deactivate_shaker()
    hs_mod.open_labware_latch()
    
    operations.append({
        "action": "shake",
        "speed_rpm": 1000,
        "time_minutes": 5
    })
    
    print(f"  Mixing complete")
    
    return {
        "operations": operations,
        "total_volume": sum(v for v in formulation.values() if v > 0),
        "num_components": sum(1 for v in formulation.values() if v > 0),
        "target_well": target_well
    }


def handle_mixing_command(payload):
    """
    Handle mixing experiment command using real Opentrons API operations.
    
    Parameters
    ----------
    payload : dict
        Command payload with formulation details
    """
    session_id = payload.get("session_id", "unknown")
    experiment_id = payload.get("experiment_id", "unknown")
    command = payload.get("command", {})
    
    formulation = command.get("formulation", {})
    target_well = command.get("target_well", "A1")
    
    print(f"\nProcessing mixing command:")
    print(f"  Experiment ID: {experiment_id}")
    print(f"  Session ID: {session_id}")
    
    try:
        # Run the mixing experiment with real Opentrons operations
        result = run_mixing_experiment(formulation, target_well)
        
        print(f"Mixing experiment completed successfully")
        print(f"  Total volume: {result['total_volume']} µL")
        print(f"  Components mixed: {result['num_components']}")
        print(f"  Target well: {result['target_well']}")
        
        # Send results back
        response_payload = {
            "status": "completed",
            "experiment_id": experiment_id,
            "session_id": session_id,
            "mixing_result": result,
            "formulation": formulation
        }
        
        response = json.dumps(response_payload)
        client.publish(STATUS_TOPIC, response, qos=2)
        print(f"Results published to {STATUS_TOPIC}\n")
        
    except Exception as e:
        print(f"Error processing mixing command: {e}")
        error_payload = {
            "status": "error",
            "experiment_id": experiment_id,
            "session_id": session_id,
            "error": str(e)
        }
        error_response = json.dumps(error_payload)
        client.publish(STATUS_TOPIC, error_response, qos=2)


def handle_command(payload):
    """
    Route command to appropriate handler.
    
    Parameters
    ----------
    payload : dict
        Command payload
    """
    command = payload.get("command", {})
    
    if "wavelengths" in command:
        print(f"Handling absorbance read command")
        handle_absorbance_command(payload)
    elif "formulation" in command:
        print(f"Handling mixing experiment command")
        handle_mixing_command(payload)
    else:
        print(f"Unknown command type: {command}")



print(f"OT-Flex simulation device ready")
print(f"  Device ID: {DEVICE_ID}")
print(f"  Command topic: {COMMAND_TOPIC}")
print(f"  Status topic: {STATUS_TOPIC}")
print("Waiting for commands...")

# Keep device active
while True:
    try:
        command = command_queue.get(timeout=1)
        print(f"\nProcessing command from queue: {command}")
        
        if "command" in command and "experiment_id" in command:
            try:
                handle_command(command)
            except Exception as e:
                print(f"Error processing command: {e}")
                
    except Empty:
        pass
    except KeyboardInterrupt:
        print("\nShutting down...")
        client.loop_stop()
        client.disconnect()
        break
    except Exception as e:
        print(f"Unexpected error in main loop: {e}")
        
    sleep(0.1)
