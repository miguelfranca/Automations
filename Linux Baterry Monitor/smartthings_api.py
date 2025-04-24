import requests
import json
from datetime import datetime

# Load API token from file
def load_parameter(file_path, parameter):
    """Load a specific parameter from a file."""
    with open(file_path, "r") as file:
        for line in file:
            if line.startswith(f"{parameter}="):
                return line.strip().split("=", 1)[1].strip('"')
    raise ValueError(f"{parameter} not found in the specified file.")

SMARTTHINGS_API_TOKEN = load_parameter(".config", "SMARTTHINGS_API_TOKEN")
BASE_URL = "https://api.smartthings.com/v1"

# Headers for API requests
HEADERS = {
    "Authorization": f"Bearer {SMARTTHINGS_API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def get_devices():
    """Fetch all SmartThings devices."""
    url = f"{BASE_URL}/devices"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()["items"]
    else:
        print(f"Failed to fetch devices: {response.status_code} - {response.text}")
        return []

def get_device_status(device_id):
    """Fetch detailed status of a specific device."""
    url = f"{BASE_URL}/devices/{device_id}/status"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch status for device {device_id}: {response.status_code} - {response.text}")
        return {}

def control_device(device_id, capability, command, component="main", arguments=None):
    """Control a device with specified capability, command, and optional arguments."""
    url = f"{BASE_URL}/devices/{device_id}/commands"
    command_payload = {
        "capability": capability,
        "command": command
    }
    if arguments:
        command_payload["arguments"] = arguments

    payload = {
        "commands": [
            {
                "component": component,
                **command_payload
            }
        ]
    }

    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        print(f"Device {device_id} {command}ed successfully.")
    else:
        print(f"Failed to {command} device {device_id}: {response.status_code} - {response.text}")

def toggle_switch(device_id, state):
    """Turn a switch on or off."""
    if state.lower() not in {"on", "off"}:
        raise ValueError("Invalid state: must be 'on' or 'off'")
    control_device(device_id, "switch", state)

def display_devices():
    print("\n=== SmartThings Devices ===")
    devices = get_devices()
    for device in devices:
        print(f"\nDevice Name: {device['label']}")
        print(f"Device ID: {device['deviceId']}")

        device_manufacturer = device.get("deviceManufacturerCode", "Unknown")
        if(device_manufacturer != "Unknown"):
            print(f"Manufacturer: {device_manufacturer}")

        # Fetch device status to check for "switch" capability
        capabilities = device.get('components', [{}])[0].get('capabilities', [])
        capability_ids = [capability.get('id', 'Unknown') for capability in capabilities]
        if "switch" in capability_ids:
            status = get_device_status(device["deviceId"])
            switch_status = (
                status.get("components", {})
                .get("main", {})
                .get("switch", {})
                .get("switch", {})
                .get("value")
            )
            if switch_status is not None:
                print(f"Switch Status: {switch_status.capitalize()}")

        print("Capabilities:")
        for capability in capabilities:
            print(f"  - {capability.get('id', 'Unknown')}")

def get_scenes():
    """Fetch all SmartThings scenes."""
    url = f"{BASE_URL}/scenes"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()["items"]
    else:
        print(f"Failed to fetch scenes: {response.status_code} - {response.text}")
        return []

def display_scenes():
    print("\n=== SmartThings Scenes ===")
    scenes = get_scenes()
    for scene in scenes:
        name = scene.get("sceneName", "Unknown")
        scene_id = scene.get("sceneId", "Unknown")

        last_modified_ms = scene.get("lastUpdatedDate", "Unknown")
        if last_modified_ms != "Unknown":
            last_modified_s = last_modified_ms / 1000
            date_time = datetime.fromtimestamp(last_modified_s)
            formatted_date = date_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            formatted_date = "Unknown"

        print(f"\nScene Name: {name}")
        print(f"Scene ID: {scene_id}")
        print(f"Last Modified: {formatted_date}")

def My_SmartThings():
    print("Fetching SmartThings devices and scenes...")

    # Fetch devices and scenes
    devices = get_devices()
    scenes = get_scenes()

    # Display fetched data
    if devices:
        display_devices(devices)
    else:
        print("No devices found.")

    if scenes:
        display_scenes(scenes)
    else:
        print("No scenes found.")

# Exported functions for reuse
__all__ = ["get_devices", "get_device_status", "control_device", "toggle_switch", "My_SmartThings", "display_devices", "get_scenes", "display_scenes", "load_parameter"]
