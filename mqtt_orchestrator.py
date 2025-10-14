#!/usr/bin/env python3
"""
MQTT Orchestrator - Sends commands to devices and receives data.
Based on ACC-HelloWorld hardware-software-communication pattern.
"""
import os
import sys
import time
import json
import secrets
from queue import Queue, Empty
import paho.mqtt.client as mqtt
import threading


def on_connect(client, userdata, flags, rc, properties=None):
    """Callback for when the client receives a CONNACK response from the server."""
    if rc == 0:
        print("Orchestrator connected to HiveMQ broker")
        userdata['connected'] = True
        userdata['connected_event'].set()
        # Subscribe to data topic
        data_topic = userdata.get('data_topic')
        if data_topic:
            client.subscribe(data_topic, qos=1)
            print(f"Orchestrator subscribed to: {data_topic}")
    else:
        print(f"Orchestrator failed to connect. Return code: {rc}")
        userdata['connected'] = False


def on_disconnect(client, userdata, rc, properties=None):
    """Callback for when the client disconnects from the broker."""
    if rc != 0:
        print(f"Orchestrator unexpected disconnection. Return code: {rc}")


def on_message(client, userdata, msg):
    """Callback for when a PUBLISH message is received from the server."""
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        print(f"Orchestrator received data on topic '{topic}': {payload}")
        
        # Parse the response
        response_dict = json.loads(payload)
        
        # Put response in queue
        queue = userdata.get('queue')
        if queue:
            queue.put(response_dict)
    except Exception as e:
        print(f"Orchestrator error handling message: {e}")


def send_command(client, command_topic, command_dict):
    """
    Send a command to the device.
    
    Parameters
    ----------
    client : mqtt.Client
        MQTT client instance
    command_topic : str
        Topic to send command to
    command_dict : dict
        Command dictionary to send
    """
    command_json = json.dumps(command_dict)
    client.publish(command_topic, command_json, qos=1)
    print(f"Orchestrator sent command to '{command_topic}': {command_json}")


def run_experiment(client, queue, command_topic, command_dict, queue_timeout=30, function_timeout=60):
    """
    Run an experiment by sending a command and waiting for the response.
    
    Parameters
    ----------
    client : mqtt.Client
        MQTT client instance
    queue : Queue
        Queue to receive responses
    command_topic : str
        Topic to send commands to
    command_dict : dict
        Command dictionary to send
    queue_timeout : int
        Timeout for queue operations
    function_timeout : int
        Timeout for the entire function
        
    Returns
    -------
    dict
        Response dictionary from the device
    """
    # Send the command
    send_command(client, command_topic, command_dict)
    
    client.loop_start()
    
    t0 = time.time()
    while True:
        if time.time() - t0 > function_timeout:
            client.loop_stop()
            raise TimeoutError(
                f"Function timed out without valid data ({function_timeout} seconds)"
            )
        try:
            results = queue.get(True, timeout=queue_timeout)
        except Empty as e:
            client.loop_stop()
            raise Empty(
                f"Data retrieval timed out ({queue_timeout} seconds)"
            ) from e

        # Only return the data if it matches the expected experiment id
        if (
            isinstance(results, dict)
            and results.get('experiment_id') == command_dict.get('experiment_id')
        ):
            client.loop_stop()
            return results
        else:
            print(f"Received mismatched experiment_id, waiting for correct one...")


def run_orchestrator(host, username, password, device_id="device_001"):
    """
    Run the MQTT orchestrator.
    
    Parameters
    ----------
    host : str
        MQTT broker hostname
    username : str
        MQTT username
    password : str
        MQTT password
    device_id : str
        Unique device identifier to communicate with
    """
    # Define topics
    command_topic = f"sdl/device/{device_id}/command"
    data_topic = f"sdl/device/{device_id}/data"
    
    # Create queue and event
    queue = Queue()
    connected_event = threading.Event()
    
    # Create userdata dictionary
    userdata = {
        'connected': False,
        'connected_event': connected_event,
        'command_topic': command_topic,
        'data_topic': data_topic,
        'queue': queue
    }
    
    # Create MQTT client
    client = mqtt.Client(
        client_id="orchestrator_client",
        userdata=userdata,
        protocol=mqtt.MQTTv5
    )
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    # Set username and password
    client.username_pw_set(username, password)
    
    # Enable TLS for secure connection
    client.tls_set()
    
    try:
        print(f"Orchestrator connecting to {host}...")
        client.connect(host, 8883, 60)
        
        # Start network loop
        client.loop_start()
        
        # Wait for connection
        if not connected_event.wait(timeout=10.0):
            print("Orchestrator connection timeout")
            return False
        
        print("Orchestrator is ready")
        print(f"  Command topic: {command_topic}")
        print(f"  Data topic: {data_topic}")
        
        # Wait a bit for device to be ready
        time.sleep(2)
        
        # Define test commands
        commands = [
            {'operation': 'read_temperature', 'params': {}},
            {'operation': 'blink_led', 'params': {'color': 'red'}},
            {'operation': 'blink_led', 'params': {'color': 'green'}},
        ]
        
        results_list = []
        
        # Run experiments
        for i, command in enumerate(commands):
            # Add unique experiment ID
            experiment_id = secrets.token_hex(4)
            command['experiment_id'] = experiment_id
            
            print(f"\n--- Experiment {i+1}/{len(commands)} ---")
            print(f"Sending command: {command}")
            
            try:
                result = run_experiment(client, queue, command_topic, command, 
                                       queue_timeout=10, function_timeout=30)
                print(f"Received result: {result}")
                results_list.append(result)
            except (Empty, TimeoutError) as e:
                print(f"Experiment failed: {e}")
                results_list.append({'error': str(e), 'command': command})
            
            time.sleep(1)
        
        print("\n" + "=" * 50)
        print("All experiments completed")
        print(f"Total: {len(results_list)} results")
        print("=" * 50)
        
        # Save results
        with open('orchestrator_results.json', 'w') as f:
            json.dump(results_list, f, indent=2)
        print("\nResults saved to orchestrator_results.json")
        
        # Clean disconnect
        client.loop_stop()
        client.disconnect()
        return True
        
    except Exception as e:
        print(f"Orchestrator error: {e}")
        return False


if __name__ == "__main__":
    # Get credentials from environment variables
    host = os.environ.get('HIVEMQ_HOST')
    username = os.environ.get('HIVEMQ_USERNAME')
    password = os.environ.get('HIVEMQ_PASSWORD')
    
    if not all([host, username, password]):
        print("Error: Missing required environment variables")
        print(f"  HIVEMQ_HOST: {'✓' if host else '✗'}")
        print(f"  HIVEMQ_USERNAME: {'✓' if username else '✗'}")
        print(f"  HIVEMQ_PASSWORD: {'✓' if password else '✗'}")
        sys.exit(1)
    
    success = run_orchestrator(host, username, password)
    sys.exit(0 if success else 1)
