#!/usr/bin/env python3
"""
MQTT Device - Simulates a laboratory device that receives commands and sends data.
Based on ACC-HelloWorld hardware-software-communication pattern.
"""
import os
import sys
import time
import json
import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc, properties=None):
    """Callback for when the client receives a CONNACK response from the server."""
    if rc == 0:
        print("Device connected to HiveMQ broker")
        userdata['connected'] = True
        # Subscribe to command topic
        command_topic = userdata.get('command_topic')
        if command_topic:
            client.subscribe(command_topic, qos=1)
            print(f"Device subscribed to: {command_topic}")
    else:
        print(f"Device failed to connect. Return code: {rc}")
        userdata['connected'] = False


def on_disconnect(client, userdata, rc, properties=None):
    """Callback for when the client disconnects from the broker."""
    if rc != 0:
        print(f"Device unexpected disconnection. Return code: {rc}")


def on_message(client, userdata, msg):
    """Callback for when a PUBLISH message is received from the server."""
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        print(f"Device received command on topic '{topic}': {payload}")
        
        # Parse the command
        command_dict = json.loads(payload)
        
        # Simulate device operation
        response = simulate_device_operation(command_dict)
        
        # Publish response to data topic
        data_topic = userdata.get('data_topic')
        if data_topic:
            response_json = json.dumps(response)
            client.publish(data_topic, response_json, qos=1)
            print(f"Device published response to '{data_topic}': {response_json}")
    except Exception as e:
        print(f"Device error handling message: {e}")


def simulate_device_operation(command_dict):
    """
    Simulate a device operation based on the command.
    
    Parameters
    ----------
    command_dict : dict
        Command dictionary with operation parameters
        
    Returns
    -------
    dict
        Response dictionary with operation results
    """
    # Extract command parameters
    operation = command_dict.get('operation', 'unknown')
    params = command_dict.get('params', {})
    experiment_id = command_dict.get('experiment_id', 'unknown')
    
    print(f"Device executing operation: {operation}")
    
    # Simulate some work
    time.sleep(1)
    
    # Create dummy response
    if operation == 'read_temperature':
        sensor_data = {'temperature': 25.5}
    elif operation == 'blink_led':
        sensor_data = {'status': 'LED blinked', 'color': params.get('color', 'red')}
    else:
        sensor_data = {'status': 'operation completed'}
    
    response = {
        'command': command_dict,
        'sensor_data': sensor_data,
        'experiment_id': experiment_id,
        'timestamp': time.time()
    }
    
    return response


def run_device(host, username, password, device_id="device_001"):
    """
    Run the MQTT device.
    
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
    # Define topics
    command_topic = f"sdl/device/{device_id}/command"
    data_topic = f"sdl/device/{device_id}/data"
    
    # Create userdata dictionary
    userdata = {
        'connected': False,
        'command_topic': command_topic,
        'data_topic': data_topic
    }
    
    # Create MQTT client
    client = mqtt.Client(
        client_id=f"{device_id}_client",
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
        print(f"Device connecting to {host}...")
        client.connect(host, 8883, 60)
        
        # Start network loop
        client.loop_start()
        
        # Wait for connection
        timeout = 10
        start_time = time.time()
        while not userdata['connected'] and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if not userdata['connected']:
            print("Device connection timeout")
            return False
        
        print("Device is ready and listening for commands...")
        print(f"  Command topic: {command_topic}")
        print(f"  Data topic: {data_topic}")
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nDevice shutting down...")
        
        # Clean disconnect
        client.loop_stop()
        client.disconnect()
        return True
        
    except Exception as e:
        print(f"Device error: {e}")
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
    
    success = run_device(host, username, password)
    sys.exit(0 if success else 1)
