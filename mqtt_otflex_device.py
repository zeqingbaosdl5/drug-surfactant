#!/usr/bin/env python3
"""
MQTT OT-Flex Device - Simulates OT-Flex robot operations.
Receives experiment requests and returns absorbance results.
"""
import os
import sys
import time
import json
import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc, properties=None):
    """Callback for when the client receives a CONNACK response from the server."""
    if rc == 0:
        print("OT-Flex Device connected to HiveMQ broker")
        userdata['connected'] = True
        command_topic = userdata.get('command_topic')
        if command_topic:
            client.subscribe(command_topic, qos=1)
            print(f"OT-Flex Device subscribed to: {command_topic}")
    else:
        print(f"OT-Flex Device failed to connect. Return code: {rc}")
        userdata['connected'] = False


def on_disconnect(client, userdata, rc, properties=None):
    """Callback for when the client disconnects from the broker."""
    if rc != 0:
        print(f"OT-Flex Device unexpected disconnection. Return code: {rc}")


def on_message(client, userdata, msg):
    """Callback for when a PUBLISH message is received from the server."""
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        print(f"\n{'='*60}")
        print(f"OT-Flex Device received experiment request")
        print(f"Topic: {topic}")
        print(f"{'='*60}")
        
        experiment_request = json.loads(payload)
        print(f"Experiment ID: {experiment_request.get('experiment_id')}")
        print(f"Parameters: {json.dumps(experiment_request.get('params', {}), indent=2)}")
        
        response = run_otflex_experiment(experiment_request)
        
        data_topic = userdata.get('data_topic')
        if data_topic:
            response_json = json.dumps(response)
            client.publish(data_topic, response_json, qos=1)
            print(f"\nOT-Flex Device published results to '{data_topic}'")
            print(f"{'='*60}\n")
    except Exception as e:
        print(f"OT-Flex Device error handling message: {e}")


def simulate_absorbance_reading(well_data):
    """
    Simulate absorbance reading for a well.
    
    Parameters
    ----------
    well_data : dict
        Dictionary with surfactant and drug volumes
        
    Returns
    -------
    dict
        Absorbance values at 600nm for different wells
    """
    # Simulate absorbance based on concentrations
    # In reality, this would come from the plate reader module
    import random
    
    # Create a simple simulation based on total volume and composition
    total_surfactant = sum(float(well_data.get(f's{i}', 0)) for i in range(1, 9))
    total_drug = sum(float(well_data.get(drug, 0)) for drug in ['IBP', 'LOV', 'DCF', 'GLV'])
    water = float(well_data.get('water', 0))
    
    # Simulate absorbance (higher concentrations = different absorbance)
    base_absorbance = 0.1 + (total_surfactant + total_drug) / 1000.0
    noise = random.uniform(-0.02, 0.02)
    absorbance = max(0.0, base_absorbance + noise)
    
    return round(absorbance, 4)


def run_otflex_experiment(experiment_request):
    """
    Simulate OT-Flex experiment execution.
    
    This would normally:
    1. Load the protocol with experiment parameters
    2. Execute liquid handling operations
    3. Shake the plate
    4. Read absorbance with plate reader
    5. Return results
    
    Parameters
    ----------
    experiment_request : dict
        Experiment request with parameters
        
    Returns
    -------
    dict
        Response with absorbance results
    """
    experiment_id = experiment_request.get('experiment_id')
    params = experiment_request.get('params', {})
    
    print("\n--- OT-Flex Protocol Execution Simulation ---")
    print("Step 1: Loading protocol...")
    time.sleep(0.5)
    
    print("Step 2: Preparing reagents...")
    time.sleep(0.5)
    
    print("Step 3: Dispensing liquids to wells...")
    # Simulate dispensing based on data parameter
    data = params.get('data', [])
    if not data:
        data = [params]  # Single experiment case
    
    time.sleep(1.0)
    
    print("Step 4: Shaking plate...")
    time.sleep(0.5)
    
    print("Step 5: Reading absorbance at 600nm...")
    time.sleep(0.5)
    
    # Simulate absorbance readings for each well
    absorbance_results = {}
    for i, well_data in enumerate(data):
        well_id = f"well_{i+1}"
        absorbance = simulate_absorbance_reading(well_data)
        absorbance_results[well_id] = {
            'absorbance_600nm': absorbance,
            'parameters': well_data
        }
        print(f"  {well_id}: {absorbance} AU")
    
    print("Protocol execution complete!")
    print("-------------------------------------------\n")
    
    response = {
        'experiment_id': experiment_id,
        'command': experiment_request,
        'absorbance_data': absorbance_results,
        'status': 'completed',
        'timestamp': time.time(),
        'device_id': 'otflex_001'
    }
    
    return response


def run_otflex_device(host, username, password, device_id="otflex_001"):
    """
    Run the OT-Flex MQTT device.
    
    Parameters
    ----------
    host : str
        MQTT broker hostname
    username : str
        MQTT username
    password : str
        MQTT password
    device_id : str
        Unique device identifier
    """
    command_topic = f"sdl/otflex/{device_id}/experiment/request"
    data_topic = f"sdl/otflex/{device_id}/experiment/results"
    
    userdata = {
        'connected': False,
        'command_topic': command_topic,
        'data_topic': data_topic
    }
    
    client = mqtt.Client(
        client_id=f"{device_id}_client",
        userdata=userdata,
        protocol=mqtt.MQTTv5
    )
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    client.username_pw_set(username, password)
    client.tls_set()
    
    try:
        print(f"OT-Flex Device connecting to {host}...")
        client.connect(host, 8883, 60)
        
        client.loop_start()
        
        timeout = 10
        start_time = time.time()
        while not userdata['connected'] and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if not userdata['connected']:
            print("OT-Flex Device connection timeout")
            return False
        
        print("\n" + "="*60)
        print("OT-Flex Device is ready and waiting for experiments")
        print(f"Request topic:  {command_topic}")
        print(f"Results topic:  {data_topic}")
        print("="*60 + "\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nOT-Flex Device shutting down...")
        
        client.loop_stop()
        client.disconnect()
        return True
        
    except Exception as e:
        print(f"OT-Flex Device error: {e}")
        return False


if __name__ == "__main__":
    host = os.environ.get('HIVEMQ_HOST')
    username = os.environ.get('HIVEMQ_USERNAME')
    password = os.environ.get('HIVEMQ_PASSWORD')
    
    if not all([host, username, password]):
        print("Error: Missing required environment variables")
        print(f"  HIVEMQ_HOST: {'✓' if host else '✗'}")
        print(f"  HIVEMQ_USERNAME: {'✓' if username else '✗'}")
        print(f"  HIVEMQ_PASSWORD: {'✓' if password else '✗'}")
        sys.exit(1)
    
    success = run_otflex_device(host, username, password)
    sys.exit(0 if success else 1)
