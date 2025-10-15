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

# Check if opentrons is installed
try:
    import opentrons.simulate
except ImportError:
    print("Opentrons package is not installed.")
    print("To install: pip install opentrons>=7.0.0")
    sys.exit(1)

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

# Load labware only (modules have limitations in simulation)
# In real hardware, absorbance reader would be in C3 (valid slots: D3, C3, B3, A3)
plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "D2")
print("Plate loaded in slot D2")

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

pr_mod = MockAbsorbanceReader()
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
