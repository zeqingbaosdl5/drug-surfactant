#!/usr/bin/env python3
"""
Test async absorbance reading - demonstrates independent plate reading.
This shows how to read absorbance spectra at any time, independent of experiments.
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
    """Callback for connection."""
    if rc == 0:
        print("Test client connected to HiveMQ broker")
        userdata['connected'] = True
        userdata['connected_event'].set()
        data_topic = userdata.get('data_topic')
        if data_topic:
            client.subscribe(data_topic, qos=1)
            print(f"Subscribed to: {data_topic}")
    else:
        print(f"Connection failed. Return code: {rc}")


def on_disconnect(client, userdata, rc, properties=None):
    """Callback for disconnection."""
    if rc != 0:
        print(f"Unexpected disconnection. Return code: {rc}")


def on_message(client, userdata, msg):
    """Callback for received messages."""
    try:
        payload = msg.payload.decode()
        response_dict = json.loads(payload)
        queue = userdata.get('queue')
        if queue:
            queue.put(response_dict)
    except Exception as e:
        print(f"Error handling message: {e}")


def send_absorbance_request(client, command_topic, request):
    """Send an absorbance reading request."""
    request_json = json.dumps(request, indent=2)
    client.publish(command_topic, request_json, qos=1)
    print(f"\n{'='*60}")
    print(f"Sent absorbance request")
    print(f"Request ID: {request.get('experiment_id')}")
    print(f"Wavelengths: {request.get('params', {}).get('wavelengths')}")
    print(f"Wells: {request.get('params', {}).get('wells')}")
    print(f"{'='*60}")


def wait_for_response(queue, experiment_id, timeout=30):
    """Wait for a response matching the experiment ID."""
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Response timeout ({timeout} seconds)")
        try:
            result = queue.get(True, timeout=10)
            if result.get('experiment_id') == experiment_id:
                return result
            else:
                print(f"Received mismatched ID, waiting...")
        except Empty:
            raise Empty(f"Queue timeout ({timeout} seconds)")


def test_async_absorbance():
    """Test async absorbance reading capability."""
    host = os.environ.get('HIVEMQ_HOST')
    username = os.environ.get('HIVEMQ_USERNAME')
    password = os.environ.get('HIVEMQ_PASSWORD')
    
    if not all([host, username, password]):
        print("Error: Missing required environment variables")
        return False
    
    device_id = "otflex_001"
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
        client_id="async_absorbance_test_client",
        userdata=userdata,
        protocol=mqtt.MQTTv5
    )
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    client.username_pw_set(username, password)
    client.tls_set()
    
    try:
        print("\n" + "="*60)
        print("ASYNC ABSORBANCE READING TEST")
        print("="*60 + "\n")
        
        print("Connecting to broker...")
        client.connect(host, 8883, 60)
        client.loop_start()
        
        if not connected_event.wait(timeout=10.0):
            print("Connection timeout")
            return False
        
        print("Connected successfully\n")
        time.sleep(2)
        
        # Test 1: Read single wavelength, all wells
        print("\n" + "="*60)
        print("TEST 1: Read all wells at 600nm")
        print("="*60)
        
        request1 = {
            'experiment_id': secrets.token_hex(8),
            'operation': 'read_absorbance',
            'params': {
                'wavelengths': [600],
                'wells': 'all'
            }
        }
        
        send_absorbance_request(client, command_topic, request1)
        result1 = wait_for_response(queue, request1['experiment_id'])
        
        print(f"\n✓ Received response:")
        print(f"  Status: {result1.get('status')}")
        print(f"  Wells read: {result1.get('num_wells')}")
        print(f"  Wavelengths: {result1.get('wavelengths')}")
        
        time.sleep(2)
        
        # Test 2: Read multiple wavelengths, specific wells
        print("\n" + "="*60)
        print("TEST 2: Read specific wells at multiple wavelengths")
        print("="*60)
        
        request2 = {
            'experiment_id': secrets.token_hex(8),
            'operation': 'read_absorbance',
            'params': {
                'wavelengths': [450, 500, 550, 600, 650],
                'wells': ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
            }
        }
        
        send_absorbance_request(client, command_topic, request2)
        result2 = wait_for_response(queue, request2['experiment_id'])
        
        print(f"\n✓ Received response:")
        print(f"  Status: {result2.get('status')}")
        print(f"  Wells read: {result2.get('num_wells')}")
        print(f"  Wavelengths: {result2.get('wavelengths')}")
        
        # Show sample spectra
        print("\n  Sample spectra:")
        for well_id in ['A1', 'A2']:
            spectra = result2.get('absorbance_spectra', {}).get(well_id, {})
            spectra_str = ", ".join([f"{wl}nm: {abs}" for wl, abs in spectra.items()])
            print(f"    {well_id}: {spectra_str}")
        
        time.sleep(2)
        
        # Test 3: Read single well
        print("\n" + "="*60)
        print("TEST 3: Read single well")
        print("="*60)
        
        request3 = {
            'experiment_id': secrets.token_hex(8),
            'operation': 'read_absorbance',
            'params': {
                'wavelengths': [600],
                'wells': 'H12'
            }
        }
        
        send_absorbance_request(client, command_topic, request3)
        result3 = wait_for_response(queue, request3['experiment_id'])
        
        print(f"\n✓ Received response:")
        print(f"  Status: {result3.get('status')}")
        print(f"  Wells read: {result3.get('num_wells')}")
        
        spectra = result3.get('absorbance_spectra', {}).get('H12', {})
        print(f"  H12 absorbance: {spectra}")
        
        # Save results
        all_results = {
            'test1_all_wells': result1,
            'test2_specific_wells': result2,
            'test3_single_well': result3
        }
        
        with open('async_absorbance_results.json', 'w') as f:
            json.dump(all_results, f, indent=2)
        print("\n✓ Results saved to async_absorbance_results.json")
        
        print("\n" + "="*60)
        print("ALL ASYNC ABSORBANCE TESTS PASSED")
        print("="*60 + "\n")
        
        client.loop_stop()
        client.disconnect()
        return True
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_async_absorbance()
    sys.exit(0 if success else 1)
