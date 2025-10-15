#!/usr/bin/env python3
"""
Test orchestrator for MQTT OT-Flex simulation device.
Sends absorbance reading commands and receives results.
"""
import json
import os
import sys
import secrets
import time
from queue import Queue, Empty
import threading

import paho.mqtt.client as mqtt

# Device configuration
DEVICE_ID = "otflex_sim_001"

# MQTT Configuration
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

# Result queue
result_queue = Queue()
connected_event = threading.Event()


def on_connect(client, userdata, flags, rc, properties=None):
    print("Orchestrator connected to MQTT Broker with result code", rc)
    client.subscribe(STATUS_TOPIC, qos=2)
    connected_event.set()


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")
    print(f"\nReceived result on topic {msg.topic}")
    try:
        result = json.loads(payload)
        result_queue.put(result)
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON payload: {e}")


# Initialize MQTT client
client = mqtt.Client(protocol=mqtt.MQTTv5)
client.tls_set()
client.username_pw_set(username, password)
client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to MQTT broker...")
client.connect(host, 8883)
client.loop_start()

# Wait for connection
if not connected_event.wait(timeout=10):
    raise ConnectionError("Failed to connect to MQTT broker")

print(f"Orchestrator ready")
print(f"  Command topic: {COMMAND_TOPIC}")
print(f"  Status topic: {STATUS_TOPIC}")


def send_absorbance_command(wavelengths, wells, session_id=None, experiment_id=None):
    """
    Send absorbance reading command to device.
    
    Parameters
    ----------
    wavelengths : list
        Wavelengths to read
    wells : str or list
        Wells to read
    session_id : str, optional
        Session identifier
    experiment_id : str, optional
        Experiment identifier
        
    Returns
    -------
    dict
        Result from device
    """
    if session_id is None:
        session_id = secrets.token_hex(4)
    if experiment_id is None:
        experiment_id = secrets.token_hex(8)
    
    command_payload = {
        "session_id": session_id,
        "experiment_id": experiment_id,
        "command": {
            "wavelengths": wavelengths,
            "wells": wells
        }
    }
    
    print(f"\n{'='*60}")
    print(f"Sending absorbance command:")
    print(f"  Experiment ID: {experiment_id}")
    print(f"  Wavelengths: {wavelengths}")
    print(f"  Wells: {wells}")
    print(f"{'='*60}")
    
    # Send command
    command_json = json.dumps(command_payload)
    client.publish(COMMAND_TOPIC, command_json, qos=2)
    
    # Wait for result
    timeout = 60
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = result_queue.get(timeout=1)
            if result.get('experiment_id') == experiment_id:
                return result
            else:
                print(f"Received result for different experiment, waiting...")
                result_queue.put(result)  # Put back for other requests
        except Empty:
            continue
    
    raise TimeoutError(f"No result received within {timeout} seconds")


# Test 1: Single wavelength, all wells
print("\n" + "="*60)
print("TEST 1: Single wavelength (600nm), all wells")
print("="*60)

try:
    result1 = send_absorbance_command(
        wavelengths=[600],
        wells='all'
    )
    
    print("\n✓ Result received:")
    print(f"  Status: {result1.get('status')}")
    print(f"  Wells read: {result1.get('num_wells')}")
    print(f"  Protocol commands: {result1.get('protocol_commands')}")
    
    # Show sample data
    absorbance_data = result1.get('absorbance_data', {})
    sample_wells = list(absorbance_data.keys())[:3]
    print(f"\n  Sample absorbance data:")
    for well in sample_wells:
        data = absorbance_data[well]
        print(f"    {well}: {data}")
    
except Exception as e:
    print(f"✗ Test 1 failed: {e}")

time.sleep(2)

# Test 2: Multi-wavelength, specific wells
print("\n" + "="*60)
print("TEST 2: Multi-wavelength (450-650nm), specific wells")
print("="*60)

try:
    result2 = send_absorbance_command(
        wavelengths=[450, 500, 550, 600, 650],
        wells=['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    )
    
    print("\n✓ Result received:")
    print(f"  Status: {result2.get('status')}")
    print(f"  Wells read: {result2.get('num_wells')}")
    print(f"  Protocol commands: {result2.get('protocol_commands')}")
    
    # Show multi-wavelength data
    absorbance_data = result2.get('absorbance_data', {})
    print(f"\n  Multi-wavelength absorbance data:")
    for well in ['A1', 'A2']:
        data = absorbance_data.get(well, {})
        print(f"    {well}:")
        for wl, value in data.items():
            print(f"      {wl}nm: {value}")
    
except Exception as e:
    print(f"✗ Test 2 failed: {e}")

time.sleep(2)

# Test 3: Single well
print("\n" + "="*60)
print("TEST 3: Single wavelength, single well (H12)")
print("="*60)

try:
    result3 = send_absorbance_command(
        wavelengths=[600],
        wells=['H12']
    )
    
    print("\n✓ Result received:")
    print(f"  Status: {result3.get('status')}")
    print(f"  Wells read: {result3.get('num_wells')}")
    
    absorbance_data = result3.get('absorbance_data', {})
    print(f"\n  Absorbance data for H12:")
    print(f"    {absorbance_data.get('H12')}")
    
except Exception as e:
    print(f"✗ Test 3 failed: {e}")

print("\n" + "="*60)
print("All tests completed")
print("="*60)

# Cleanup
client.loop_stop()
client.disconnect()
