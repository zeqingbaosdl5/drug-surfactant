#!/usr/bin/env python3
"""
Test script to verify HiveMQ connection with provided credentials.
This script tests the connection to HiveMQ broker using MQTT protocol.
"""
import os
import sys
import time
import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc, properties=None):
    """Callback for when the client receives a CONNACK response from the server."""
    if rc == 0:
        print("✓ Successfully connected to HiveMQ broker")
        userdata['connected'] = True
    else:
        print(f"✗ Failed to connect to HiveMQ broker. Return code: {rc}")
        userdata['connected'] = False


def on_disconnect(client, userdata, rc, properties=None):
    """Callback for when the client disconnects from the broker."""
    if rc != 0:
        print(f"✗ Unexpected disconnection. Return code: {rc}")


def on_publish(client, userdata, mid, properties=None):
    """Callback for when a message is successfully published."""
    print(f"✓ Message published successfully (message ID: {mid})")
    userdata['published'] = True


def on_message(client, userdata, msg):
    """Callback for when a PUBLISH message is received from the server."""
    print(f"✓ Message received on topic '{msg.topic}': {msg.payload.decode()}")
    userdata['received'] = True


def test_hivemq_connection():
    """Test HiveMQ connection with ping functionality."""
    # Get credentials from environment variables
    host = os.environ.get('HIVEMQ_HOST')
    username = os.environ.get('HIVEMQ_USERNAME')
    password = os.environ.get('HIVEMQ_PASSWORD')
    
    if not all([host, username, password]):
        print("✗ Error: Missing required environment variables")
        print(f"  HIVEMQ_HOST: {'✓' if host else '✗'}")
        print(f"  HIVEMQ_USERNAME: {'✓' if username else '✗'}")
        print(f"  HIVEMQ_PASSWORD: {'✓' if password else '✗'}")
        return False
    
    print("Testing HiveMQ Connection")
    print("=" * 50)
    print(f"Host: {host}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print("=" * 50)
    
    # Create userdata dictionary to track connection status
    userdata = {
        'connected': False,
        'published': False,
        'received': False
    }
    
    # Create MQTT client
    client = mqtt.Client(
        client_id="copilot_test_client",
        userdata=userdata,
        protocol=mqtt.MQTTv5
    )
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    client.on_message = on_message
    
    # Set username and password
    client.username_pw_set(username, password)
    
    # Enable TLS for secure connection (HiveMQ Cloud requires TLS)
    client.tls_set()
    
    try:
        print("\n1. Attempting to connect to HiveMQ broker...")
        client.connect(host, 8883, 60)
        
        # Start network loop
        client.loop_start()
        
        # Wait for connection
        timeout = 10
        start_time = time.time()
        while not userdata['connected'] and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if not userdata['connected']:
            print("✗ Connection timeout")
            return False
        
        # Subscribe to a test topic
        test_topic = "test/copilot/ping"
        print(f"\n2. Subscribing to topic: {test_topic}")
        client.subscribe(test_topic, qos=1)
        time.sleep(1)  # Wait for subscription to complete
        
        # Publish a test message
        print(f"\n3. Publishing test message to topic: {test_topic}")
        test_message = "ping from copilot test"
        result = client.publish(test_topic, test_message, qos=1)
        
        # Wait for message to be published and received
        timeout = 5
        start_time = time.time()
        while (not userdata['published'] or not userdata['received']) and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # Check results
        print("\n" + "=" * 50)
        print("Test Results:")
        print(f"  Connection: {'✓ Success' if userdata['connected'] else '✗ Failed'}")
        print(f"  Publish: {'✓ Success' if userdata['published'] else '✗ Failed'}")
        print(f"  Receive: {'✓ Success' if userdata['received'] else '✗ Failed'}")
        print("=" * 50)
        
        success = userdata['connected'] and userdata['published'] and userdata['received']
        
        # Disconnect
        print("\n4. Disconnecting from HiveMQ broker...")
        client.loop_stop()
        client.disconnect()
        
        return success
        
    except Exception as e:
        print(f"✗ Error during connection test: {e}")
        return False


if __name__ == "__main__":
    success = test_hivemq_connection()
    sys.exit(0 if success else 1)
