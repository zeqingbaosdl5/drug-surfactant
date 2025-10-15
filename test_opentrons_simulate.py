#!/usr/bin/env python3
"""
Test script demonstrating opentrons.simulate usage with OT-Flex protocols.
This script shows how to validate protocol syntax and simulate execution.

Usage:
    python test_opentrons_simulate.py
"""
import json
from opentrons import simulate


def create_simple_protocol():
    """
    Create a simple Opentrons protocol for testing absorbance reader.
    """
    protocol_text = """
from opentrons import protocol_api

metadata = {
    'protocolName': 'Absorbance Reader Test',
    'author': 'Test',
    'description': 'Simple protocol to test absorbance reader simulation'
}

requirements = {"robotType": "Flex", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    # Load absorbance reader module
    pr_mod = protocol.load_module(
        module_name="absorbanceReaderV1",
        location="C3"
    )
    
    # Load a plate
    plate = protocol.load_labware(
        load_name="corning_96_wellplate_360ul_flat",
        location='D1'
    )
    
    # Initialize the plate reader for single wavelength
    pr_mod.initialize(mode="single", wavelengths=[600])
    
    # Open lid
    pr_mod.open_lid()
    
    # Move plate to reader (simulated - would use gripper on real robot)
    protocol.comment("Moving plate to reader")
    
    # Close lid
    pr_mod.close_lid()
    
    # Read the plate
    pr_data = pr_mod.read()
    
    # Access data
    protocol.comment(f"Reading well A1 at 600nm")
    
    # Open lid
    pr_mod.open_lid()
    
    protocol.comment("Protocol complete")
"""
    return protocol_text


def test_protocol_simulation():
    """
    Test protocol simulation using opentrons.simulate.
    """
    print("="*60)
    print("Testing Opentrons Protocol Simulation")
    print("="*60)
    
    # Create a simple protocol
    protocol_text = create_simple_protocol()
    
    print("\nProtocol created. Simulating...")
    
    try:
        # Run the simulation
        # The simulate.simulate() function takes protocol text and returns
        # a tuple of (protocol_context, bundle)
        protocol, bundle = simulate.simulate(protocol_text)
        
        print("\n✓ Protocol simulation successful!")
        print(f"\n  Protocol name: {bundle.metadata.get('protocolName', 'N/A')}")
        print(f"  API Level: {bundle.metadata.get('apiLevel', 'N/A')}")
        
        # Display commands that would be executed
        print(f"\n  Commands executed: {len(bundle.commands)}")
        
        # Show first few commands as examples
        print("\n  Example commands:")
        for i, cmd in enumerate(bundle.commands[:5]):
            print(f"    {i+1}. {cmd.get('commandType', 'unknown')}")
        
        if len(bundle.commands) > 5:
            print(f"    ... and {len(bundle.commands) - 5} more commands")
        
        print("\n" + "="*60)
        print("Simulation demonstrates protocol is syntactically valid")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Protocol simulation failed:")
        print(f"  Error: {e}")
        print("\n" + "="*60)
        return False


def create_absorbance_multi_wavelength_protocol():
    """
    Create protocol demonstrating multi-wavelength absorbance reading.
    """
    protocol_text = """
from opentrons import protocol_api

metadata = {'protocolName': 'Multi-Wavelength Absorbance Test'}
requirements = {"robotType": "Flex", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    pr_mod = protocol.load_module("absorbanceReaderV1", "C3")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", 'D1')
    
    # Multi-wavelength read
    pr_mod.initialize(mode="multi", wavelengths=[450, 500, 550, 600, 650])
    pr_mod.open_lid()
    pr_mod.close_lid()
    pr_data = pr_mod.read()
    
    # Access multi-wavelength data
    protocol.comment(f"Reading well A1 at multiple wavelengths")
    for wavelength in [450, 500, 550, 600, 650]:
        protocol.comment(f"  {wavelength}nm: {pr_data.get(wavelength, {}).get('A1', 'N/A')}")
    
    pr_mod.open_lid()
"""
    return protocol_text


def test_multi_wavelength_simulation():
    """
    Test multi-wavelength absorbance protocol.
    """
    print("\n" + "="*60)
    print("Testing Multi-Wavelength Absorbance Protocol")
    print("="*60)
    
    protocol_text = create_absorbance_multi_wavelength_protocol()
    
    try:
        protocol, bundle = simulate.simulate(protocol_text)
        print("\n✓ Multi-wavelength protocol simulation successful!")
        print(f"  Commands: {len(bundle.commands)}")
        return True
    except Exception as e:
        print(f"\n✗ Multi-wavelength simulation failed: {e}")
        return False


if __name__ == "__main__":
    print("\nOpentrons Simulate - Protocol Validation Tool\n")
    
    # Test basic protocol
    result1 = test_protocol_simulation()
    
    # Test multi-wavelength protocol
    result2 = test_multi_wavelength_simulation()
    
    print("\n" + "="*60)
    if result1 and result2:
        print("✓ All protocol simulations passed")
    else:
        print("✗ Some protocol simulations failed")
    print("="*60 + "\n")
