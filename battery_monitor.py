import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import subprocess
import requests

SMARTTHINGS_OFF_SCENE_ID = "id"
SMARTTHINGS_ON_SCENE_ID = "id"
AUTHORIZATION_TOKEN = "token"
BATTERY_CHARGED_THRESHOLD = 95
BATTERY_NOT_CHARGED_THRESHOLD = 90
PLUG_OFF_URL = f"https://api.smartthings.com/v1/scenes/{SMARTTHINGS_OFF_SCENE_ID}/execute"
PLUG_ON_URL = f"https://api.smartthings.com/v1/scenes/{SMARTTHINGS_ON_SCENE_ID}/execute"

last_sent_percentage = None  # To prevent duplicate requests

def get_battery_path():
    """Fetch the battery device path using the 'upower' command."""
    try:
        result = subprocess.run(["upower", "-e"], capture_output=True, text=True, check=True)
        paths = result.stdout.splitlines()
        for path in paths:
            if "battery" in path:
                return path.strip()
        print("No battery device found!")
    except Exception as e:
        print(f"Error fetching battery path: {e}")
    return None


def get_battery_percentage_and_state(battery_path):
    """Fetch the battery percentage and state directly from UPower."""
    try:
        bus = dbus.SystemBus()
        battery = bus.get_object("org.freedesktop.UPower", battery_path)
        properties = dbus.Interface(battery, "org.freedesktop.DBus.Properties")
        percentage = properties.Get("org.freedesktop.UPower.Device", "Percentage")
        state = properties.Get("org.freedesktop.UPower.Device", "State")
        return percentage, state
    except Exception as e:
        print(f"Error fetching battery details: {e}")
        return None, None


def send_http_request(url):
    """Send an HTTP POST request to the SmartThings API."""
    try:
        headers = {"Authorization": f"Bearer {AUTHORIZATION_TOKEN}"}
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            print("HTTP request sent successfully!")
        else:
            print(f"Failed to send HTTP request: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending HTTP request: {e}")


def battery_status_changed(interface, changed_properties, invalidated_properties, battery_path):
    """Callback triggered when battery properties change."""
    global last_sent_percentage

    percentage, state = get_battery_percentage_and_state(battery_path)

    if percentage is None:
        print("Could not fetch battery percentage.")
        return

    if state == 1:
        print(f"Status: Charging - {percentage}%")
    elif state == 2:
        print(f"Status: Discharging - {percentage}%")
    elif state == 4:
        print(f"Status: Fully Charged - {percentage}%")
    else:
        print(f"Unknown state {state}")

    if percentage <= BATTERY_NOT_CHARGED_THRESHOLD and state == 2:
        print("Battery below threshold. Sending HTTP request...")
        send_http_request(PLUG_ON_URL)
        last_sent_percentage = percentage  # Update last sent percentage

    if (percentage > BATTERY_CHARGED_THRESHOLD and state == 1) or (state == 4 and percentage == 100):
        print("Battery above threshold. Sending HTTP request...")
        send_http_request(PLUG_OFF_URL)
        last_sent_percentage = percentage  # Update last sent percentage

    print()

def main():
    battery_path = get_battery_path()
    if not battery_path:
        print("Battery path could not be determined. Exiting.")
        return

    print(f"Using battery path: {battery_path}")

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    bus.add_signal_receiver(
        lambda interface, changed_properties, invalidated_properties: battery_status_changed(
            interface, changed_properties, invalidated_properties, battery_path
        ),
        dbus_interface="org.freedesktop.DBus.Properties",
        path=battery_path
    )

    print("Listening for battery status changes...")
    loop = GLib.MainLoop()
    loop.run()

if __name__ == "__main__":
    main()