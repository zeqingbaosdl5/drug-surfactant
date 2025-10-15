#!/usr/bin/env python3
"""
MQTT OT-Flex Device with Protocol Simulation
Based on AC dev lab OT2mqtt.py pattern but using opentrons.simulate instead of opentrons.execute.
This allows testing protocol logic without physical hardware.
"""
import json
import sys
from queue import Empty, Queue
from time import sleep
from io import StringIO

# Check if opentrons is installed
try:
    import opentrons.simulate
except ImportError:
    print("Opentrons package is not installed.")
    print("To install: pip install opentrons>=7.0.0")
    sys.exit(1)

import paho.mqtt.client as mqtt

# Device configuration
DEVICE_ID = "otflex_sim_001"

# MQTT Broker Configuration (using environment variables)
import os
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


def create_absorbance_protocol(wavelengths, wells):
    """
    Create an Opentrons protocol for absorbance reading.
    
    Parameters
    ----------
    wavelengths : list
        List of wavelengths to read (e.g., [450, 500, 600])
    wells : str or list
        Wells to read ('all' or list like ['A1', 'A2'])
    
    Returns
    -------
    str
        Protocol text ready for simulation
    """
    wells_str = repr(wells) if isinstance(wells, list) else f"'{wells}'"
    
    protocol_text = f"""
from opentrons import protocol_api

metadata = {{
    'protocolName': 'Absorbance Reading Protocol',
    'author': 'MQTT Device',
}}

requirements = {{"robotType": "Flex", "apiLevel": "2.21"}}

def run(protocol: protocol_api.ProtocolContext):
    # Load absorbance reader module
    pr_mod = protocol.load_module("absorbanceReaderV1", "C3")
    
    # Load plate
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "D1")
    
    # Close lid before initialization (required)
    pr_mod.close_lid()
    
    # Initialize for wavelength(s)
    wavelengths = {wavelengths}
    if len(wavelengths) == 1:
        pr_mod.initialize(mode="single", wavelengths=wavelengths)
    else:
        pr_mod.initialize(mode="multi", wavelengths=wavelengths)
    
    # Open lid to load plate (would use gripper on real robot)
    pr_mod.open_lid()
    protocol.comment("Place plate on reader")
    
    # Close lid for reading
    pr_mod.close_lid()
    
    # Read the plate
    pr_data = pr_mod.read()
    
    # Log some results
    wells = {wells_str}
    if wells == 'all':
        protocol.comment(f"Read all wells at wavelengths: {{wavelengths}}")
    else:
        for well in wells:
            protocol.comment(f"Read well {{well}} at wavelengths: {{wavelengths}}")
    
    # Open lid when done
    pr_mod.open_lid()
    
    protocol.comment("Protocol complete")
"""
    return protocol_text


def simulate_protocol(protocol_text):
    """
    Simulate an Opentrons protocol.
    
    Parameters
    ----------
    protocol_text : str
        The protocol code to simulate
        
    Returns
    -------
    tuple
        (runlog, bundle) from simulation
    """
    protocol_file = StringIO(protocol_text)
    runlog, bundle = opentrons.simulate.simulate(protocol_file)
    return runlog, bundle


def handle_absorbance_command(payload):
    """
    Handle absorbance reading command by simulating protocol.
    
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
    
    print(f"Processing absorbance command:")
    print(f"  Wavelengths: {wavelengths}")
    print(f"  Wells: {wells}")
    print(f"  Experiment ID: {experiment_id}")
    
    try:
        # Create protocol
        protocol_text = create_absorbance_protocol(wavelengths, wells)
        
        # Simulate protocol
        print("Simulating protocol...")
        runlog, bundle = simulate_protocol(protocol_text)
        
        print(f"Protocol simulation completed successfully")
        print(f"  Commands executed: {len(runlog)}")
        
        # In real implementation, would get actual absorbance data
        # For simulation, create mock data
        absorbance_data = {}
        if wells == 'all':
            # Mock data for all 96 wells
            for row in 'ABCDEFGH':
                for col in range(1, 13):
                    well_id = f"{row}{col}"
                    absorbance_data[well_id] = {
                        wl: round(0.1 + (hash(f"{well_id}{wl}") % 100) / 200, 4)
                        for wl in wavelengths
                    }
        else:
            # Mock data for specific wells
            for well_id in wells:
                absorbance_data[well_id] = {
                    wl: round(0.1 + (hash(f"{well_id}{wl}") % 100) / 200, 4)
                    for wl in wavelengths
                }
        
        # Send results back
        response_payload = {
            "status": "completed",
            "experiment_id": experiment_id,
            "session_id": session_id,
            "absorbance_data": absorbance_data,
            "wavelengths": wavelengths,
            "num_wells": len(absorbance_data),
            "protocol_commands": len(runlog)
        }
        
        response = json.dumps(response_payload)
        client.publish(STATUS_TOPIC, response, qos=2)
        print(f"Results published to {STATUS_TOPIC}")
        
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
        print(f"Handling absorbance read command: {payload}")
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
