import requests
import json
from datetime import datetime

SMARTTHINGS_API_TOKEN = "token"
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

def control_device(device_id, command):
    """Turn on or off a device that has a switch capability."""
    url = f"{BASE_URL}/devices/{device_id}/commands"
    payload = {
        "commands": [
            {
            "capability": "switch",
            "command": command
            }
        ]
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        print(f"Device {device_id} {command}ed successfully.")
    else:
        print(f"Failed to {command} device {device_id}: {response.status_code} - {response.text}")

def display_devices(devices):
    print("\n=== SmartThings Devices ===")
    for device in devices:
        print(f"\nDevice Name: {device['label']}")
        print(f"Device ID: {device['deviceId']}")

        device_type_name = device.get("dth", {}).get("deviceTypeName", "Unknown")
        print(f"Type: {device_type_name}")

        print(f"Status: {device.get('healthState', {}).get('state', 'Unknown')}")

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

def display_scenes(scenes):
    print("\n=== SmartThings Scenes ===")
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

def main():
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

    # control_device("f144305a-bbc8-4339-ba41-57a18df2da5f", "off")
    # control_device("f144305a-bbc8-4339-ba41-57a18df2da5f", "on")

if __name__ == "__main__":
    main()
