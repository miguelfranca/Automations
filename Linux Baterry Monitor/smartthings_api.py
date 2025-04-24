import requests
import json
from datetime import datetime
import argparse
import os

# Load API token from file
def load_parameter(file_path, parameter):
    """Load a specific parameter from a file."""
    with open(file_path, "r") as file:
        for line in file:
            if line.startswith(f"{parameter}="):
                return line.strip().split("=", 1)[1].strip('"')
    raise ValueError(f"{parameter} not found in the specified file.")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, ".config")

LOGGING = False

SMARTTHINGS_API_TOKEN = load_parameter(CONFIG_FILE, "SMARTTHINGS_API_TOKEN")
BASE_URL = "https://api.smartthings.com/v1"
LOG_FILE = "log.txt"

# Headers for API requests
HEADERS = {
    "Authorization": f"Bearer {SMARTTHINGS_API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def log(file_path: str, content: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_content = f"[{timestamp}] {content}"
    print(content)
    
    if(not LOGGING):
        return

    try:
        with open(file_path, 'a') as file:
            file.write(full_content + '\n')
    except Exception as e:
        pass

def get_devices():
    """Fetch all SmartThings devices."""
    url = f"{BASE_URL}/devices"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()["items"]
    else:
        log(LOG_FILE, f"Failed to fetch devices: {response.status_code} - {response.text}")
        return []

def get_device_status(device_id):
    """Fetch detailed status of a specific device."""
    url = f"{BASE_URL}/devices/{device_id}/status"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        log(LOG_FILE, f"Failed to fetch status for device {device_id}: {response.status_code} - {response.text}")
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
        log(LOG_FILE, f"Device {device_id} {command}ed successfully.")
    else:
        log(LOG_FILE, f"Failed to {command} device {device_id}: {response.status_code} - {response.text}")

    return response.status_code

def toggle_switch(device_id, state):
    """Turn a switch on or off."""
    if state.lower() not in {"on", "off"}:
        raise ValueError("Invalid state: must be 'on' or 'off'")
    return control_device(device_id, "switch", state)

def display_devices():
    log(LOG_FILE, "\n=== SmartThings Devices ===")
    devices = get_devices()

    if(len(devices) == 0):
        log(LOG_FILE, "No scenes found.")

    for device in devices:
        log(LOG_FILE, f"\nDevice Name: {device['label']}")
        log(LOG_FILE, f"Device ID: {device['deviceId']}")

        device_manufacturer = device.get("deviceManufacturerCode", "Unknown")
        if(device_manufacturer != "Unknown"):
            log(LOG_FILE, f"Manufacturer: {device_manufacturer}")

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
                log(LOG_FILE, f"Switch Status: {switch_status.capitalize()}")

        log(LOG_FILE, "Capabilities:")
        for capability in capabilities:
            log(LOG_FILE, f"  - {capability.get('id', 'Unknown')}")

def get_scenes():
    """Fetch all SmartThings scenes."""
    url = f"{BASE_URL}/scenes"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()["items"]
    else:
        log(LOG_FILE, f"Failed to fetch scenes: {response.status_code} - {response.text}")
        return []

def display_scenes():
    log(LOG_FILE, "\n=== SmartThings Scenes ===")
    scenes = get_scenes()
    
    if(len(scenes) == 0):
        log(LOG_FILE, "No scenes found.")

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

        log(LOG_FILE, f"\nScene Name: {name}")
        log(LOG_FILE, f"Scene ID: {scene_id}")
        log(LOG_FILE, f"Last Modified: {formatted_date}")

def My_SmartThings():
    log(LOG_FILE, "Fetching SmartThings devices and scenes...")

    display_devices()
    display_scenes()

def parse_arguments():
    parser = argparse.ArgumentParser(description="SmartThings CLI for Argos")
    parser.add_argument("--display-devices", action="store_true", help="Display SmartThings devices")
    parser.add_argument("--toggle-switch", nargs=2, metavar=("device_id", "state"), help="Toggle a device switch state")
    return parser.parse_args()

def main():
    args = parse_arguments()
    if args.display_devices:
        display_devices()
    elif args.toggle_switch:
        device_id, state = args.toggle_switch
        toggle_switch(device_id, state)
    else:
        print("No valid action provided.")
if __name__ == "__main__":
    main()


# Exported functions for reuse
__all__ = ["get_devices", "get_device_status", "control_device", "toggle_switch", "My_SmartThings", "display_devices", "get_scenes", "display_scenes", "load_parameter", "log"]
