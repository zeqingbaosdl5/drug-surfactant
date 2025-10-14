#!/usr/bin/env python3
"""
MQTT OT-Flex Orchestrator - Sends experiment requests and receives absorbance results.
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
        print("OT-Flex Orchestrator connected to HiveMQ broker")
        userdata['connected'] = True
        userdata['connected_event'].set()
        data_topic = userdata.get('data_topic')
        if data_topic:
            client.subscribe(data_topic, qos=1)
            print(f"OT-Flex Orchestrator subscribed to: {data_topic}")
    else:
        print(f"OT-Flex Orchestrator failed to connect. Return code: {rc}")
        userdata['connected'] = False


def on_disconnect(client, userdata, rc, properties=None):
    """Callback for when the client disconnects from the broker."""
    if rc != 0:
        print(f"OT-Flex Orchestrator unexpected disconnection. Return code: {rc}")


def on_message(client, userdata, msg):
    """Callback for when a PUBLISH message is received from the server."""
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        print(f"\nOT-Flex Orchestrator received results on topic '{topic}'")
        
        response_dict = json.loads(payload)
        
        queue = userdata.get('queue')
        if queue:
            queue.put(response_dict)
    except Exception as e:
        print(f"OT-Flex Orchestrator error handling message: {e}")


def send_experiment_request(client, command_topic, experiment_request):
    """
    Send an experiment request to the OT-Flex device.
    
    Parameters
    ----------
    client : mqtt.Client
        MQTT client instance
    command_topic : str
        Topic to send request to
    experiment_request : dict
        Experiment request dictionary
    """
    request_json = json.dumps(experiment_request, indent=2)
    client.publish(command_topic, request_json, qos=1)
    print(f"\n{'='*60}")
    print(f"OT-Flex Orchestrator sent experiment request")
    print(f"Experiment ID: {experiment_request.get('experiment_id')}")
    print(f"{'='*60}")


def run_experiment(client, queue, command_topic, experiment_request, 
                   queue_timeout=60, function_timeout=120):
    """
    Run an experiment by sending a request and waiting for results.
    
    Parameters
    ----------
    client : mqtt.Client
        MQTT client instance
    queue : Queue
        Queue to receive responses
    command_topic : str
        Topic to send requests to
    experiment_request : dict
        Experiment request dictionary
    queue_timeout : int
        Timeout for queue operations
    function_timeout : int
        Timeout for the entire function
        
    Returns
    -------
    dict
        Response dictionary with absorbance results
    """
    send_experiment_request(client, command_topic, experiment_request)
    
    client.loop_start()
    
    t0 = time.time()
    while True:
        if time.time() - t0 > function_timeout:
            client.loop_stop()
            raise TimeoutError(
                f"Experiment timed out without results ({function_timeout} seconds)"
            )
        try:
            results = queue.get(True, timeout=queue_timeout)
        except Empty as e:
            client.loop_stop()
            raise Empty(
                f"Results retrieval timed out ({queue_timeout} seconds)"
            ) from e

        if (
            isinstance(results, dict)
            and results.get('experiment_id') == experiment_request.get('experiment_id')
        ):
            client.loop_stop()
            return results
        else:
            print(f"Received mismatched experiment_id, waiting for correct one...")


def run_otflex_orchestrator(host, username, password, device_id="otflex_001"):
    """
    Run the OT-Flex MQTT orchestrator.
    
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
    command_topic = f"sdl/otflex/{device_id}/experiment/request"
    data_topic = f"sdl/otflex/{device_id}/experiment/results"
    
    queue = Queue()
    connected_event = threading.Event()
    
    userdata = {
        'connected': False,
        'connected_event': connected_event,
        'command_topic': command_topic,
        'data_topic': data_topic,
        'queue': queue
    }
    
    client = mqtt.Client(
        client_id="otflex_orchestrator_client",
        userdata=userdata,
        protocol=mqtt.MQTTv5
    )
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    client.username_pw_set(username, password)
    client.tls_set()
    
    try:
        print(f"OT-Flex Orchestrator connecting to {host}...")
        client.connect(host, 8883, 60)
        
        client.loop_start()
        
        if not connected_event.wait(timeout=10.0):
            print("OT-Flex Orchestrator connection timeout")
            return False
        
        print("\n" + "="*60)
        print("OT-Flex Orchestrator is ready")
        print(f"Request topic:  {command_topic}")
        print(f"Results topic:  {data_topic}")
        print("="*60 + "\n")
        
        time.sleep(2)
        
        # Example experiment data based on the OT-Flex template
        experiment_data = [
            {
                "trial_index": "0",
                "drug_name": "IBP",
                "s1": "120.0",
                "s2": "0.0",
                "s3": "0.0",
                "s4": "0.0",
                "s5": "0.0",
                "s6": "168.0",
                "s7": "0.0",
                "s8": "0.0",
                "water": "396.0",
                "IBP": "180.0",
                "LOV": "0.0",
                "DCF": "0.0",
                "GLV": "0.0"
            },
            {
                "trial_index": "1",
                "drug_name": "LOV",
                "s1": "0.0",
                "s2": "150.0",
                "s3": "0.0",
                "s4": "0.0",
                "s5": "0.0",
                "s6": "200.0",
                "s7": "0.0",
                "s8": "0.0",
                "water": "320.0",
                "IBP": "0.0",
                "LOV": "180.0",
                "DCF": "0.0",
                "GLV": "0.0"
            }
        ]
        
        # Create experiment request
        experiment_id = secrets.token_hex(8)
        experiment_request = {
            'experiment_id': experiment_id,
            'operation': 'run_drug_surfactant_protocol',
            'params': {
                'data': experiment_data,
                'wavelength': 600,
                'shake_speed': 1000,
                'shake_time': 5
            }
        }
        
        print(f"Running experiment with {len(experiment_data)} wells...")
        
        try:
            result = run_experiment(
                client, queue, command_topic, experiment_request,
                queue_timeout=30, function_timeout=120
            )
            
            print("\n" + "="*60)
            print("EXPERIMENT RESULTS")
            print("="*60)
            print(f"Status: {result.get('status')}")
            print(f"Device: {result.get('device_id')}")
            print(f"Timestamp: {result.get('timestamp')}")
            print("\nAbsorbance Data:")
            absorbance_data = result.get('absorbance_data', {})
            for well_id, well_data in absorbance_data.items():
                absorbance = well_data.get('absorbance_600nm')
                print(f"  {well_id}: {absorbance} AU")
            print("="*60 + "\n")
            
            # Save results
            with open('otflex_experiment_results.json', 'w') as f:
                json.dump(result, f, indent=2)
            print("Results saved to otflex_experiment_results.json")
            
        except (Empty, TimeoutError) as e:
            print(f"\nExperiment failed: {e}")
            return False
        
        client.loop_stop()
        client.disconnect()
        return True
        
    except Exception as e:
        print(f"OT-Flex Orchestrator error: {e}")
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
    
    success = run_otflex_orchestrator(host, username, password)
    sys.exit(0 if success else 1)
