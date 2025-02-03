from smartthings_api import *
from datetime import datetime
import platform
from enum import Enum
import subprocess

os_name = platform.system()

# Auto startup on linux
# https://askubuntu.com/questions/584813/how-to-add-custom-applications-scripts-in-startup-applications-in-14-10

if os_name == "Linux":
    import dbus
    import dbus.mainloop.glib
    from gi.repository import GLib
    import subprocess
elif os_name == "Windows":
    import win32com.client
    import pythoncom

SMART_PLUG_ID = load_parameter(".config", "SMART_PLUG_ID")
BATTERY_CHARGED_THRESHOLD = 100
BATTERY_NOT_CHARGED_THRESHOLD = 60
WINDOWS_POOL_INTERVAL = 10
LOG_FILE = "log.txt"

class BatteryState(Enum):
    CHARGING = 1
    DISCHARGING = 2
    FULLY_CHARGED = 3
    UNKNOWN = 0

def handle_battery_status(percentage, state):
    global last_sent_percentage

    log(LOG_FILE, f"Status: {state.name} - {percentage}%")

    if percentage <= BATTERY_NOT_CHARGED_THRESHOLD and state == BatteryState.DISCHARGING:
        code = toggle_switch(SMART_PLUG_ID, "on")
        log(LOG_FILE, f"Smart plug {SMART_PLUG_ID} - oned with code {code}")
        showNotification("Charging...")

    if (percentage > BATTERY_CHARGED_THRESHOLD and state == BatteryState.CHARGING) or state == BatteryState.FULLY_CHARGED:
        code = toggle_switch(SMART_PLUG_ID, "off")
        log(LOG_FILE, f"Smart plug {SMART_PLUG_ID} - offed with code {code}")

def get_battery_path():
    """Fetch the battery device path using the 'upower' command"""
    try:
        result = subprocess.run(["upower", "-e"], capture_output=True, text=True, check=True)
        paths = result.stdout.splitlines()
        for path in paths:
            if "battery" in path:
                return path.strip()
        log(LOG_FILE, "No battery device found!")
    except Exception as e:
        log(LOG_FILE, f"Error fetching battery path: {e}")
    return None

def get_battery_percentage_and_state_linux(battery_path):
    """Fetch the battery percentage and state directly from UPower"""
    try:
        bus = dbus.SystemBus()
        battery = bus.get_object("org.freedesktop.UPower", battery_path)
        properties = dbus.Interface(battery, "org.freedesktop.DBus.Properties")
        percentage = properties.Get("org.freedesktop.UPower.Device", "Percentage")
        state_code = properties.Get("org.freedesktop.UPower.Device", "State")

        state = {
            1: BatteryState.CHARGING,
            2: BatteryState.DISCHARGING,
            4: BatteryState.FULLY_CHARGED
        }.get(state_code, BatteryState.UNKNOWN)

        return percentage, state
    except Exception as e:
        log(LOG_FILE, f"Error fetching battery details: {e}")
        return None, None

def battery_status_changed_linux(interface, changed_properties, invalidated_properties, battery_path):
    """Callback triggered when battery properties change"""
    percentage, state = get_battery_percentage_and_state_linux(battery_path)

    if percentage is None:
        log(LOG_FILE, "Could not fetch battery percentage.")
        return

    handle_battery_status(percentage, state)

def battery_status_listener_linux():
    battery_path = get_battery_path()
    if not battery_path:
        log(LOG_FILE, "Battery path could not be determined. Exiting.")
        return

    log(LOG_FILE, f"Using battery path: {battery_path}")

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    bus.add_signal_receiver(
        lambda interface, changed_properties, invalidated_properties: battery_status_changed_linux(
            interface, changed_properties, invalidated_properties, battery_path
        ),
        dbus_interface="org.freedesktop.DBus.Properties",
        path=battery_path
    )

    battery_status_changed_linux(None, None, None, battery_path)
    log(LOG_FILE, "Listening for battery status changes...")
    loop = GLib.MainLoop()
    loop.run()

def battery_event_handler_windows(event):
    battery = event.Properties_("TargetInstance").Value
    percentage = battery.Properties_("EstimatedChargeRemaining").Value
    charging = battery.Properties_("BatteryStatus").Value == 2  # Charging state
    state = BatteryState.CHARGING if charging else BatteryState.DISCHARGING if percentage < 100 else BatteryState.FULLY_CHARGED
    handle_battery_status(percentage, state)

def battery_status_listener_windows():
    wmi = win32com.client.Dispatch("WbemScripting.SWbemLocator")
    conn = wmi.ConnectServer(".", "root\\cimv2")
    query = f"SELECT * FROM __InstanceModificationEvent WITHIN {WINDOWS_POOL_INTERVAL} WHERE TargetInstance ISA 'Win32_Battery'"
    event_source = conn.ExecNotificationQuery(query)
    log(LOG_FILE, "Listening for battery status changes on Windows...")

    while True:
        try:
            pythoncom.PumpWaitingMessages()
            event = event_source.NextEvent()
            battery_event_handler_windows(event)
        except Exception as e:
            log(LOG_FILE, f"Error in WMI event listener: {e}")
            break

def showNotification(message):
    subprocess.Popen(['notify-send', message])
    return
            
def main():
    if os_name == "Linux":
        log(LOG_FILE, "Setting up event listener for Linux...")
        battery_status_listener_linux()  

    elif os_name == "Windows":
        log(LOG_FILE, "Setting up event listener for Windows...")
        battery_status_listener_windows()

    else:
        log(LOG_FILE, f"Unsupported OS: {os_name}. Exiting.")

if __name__ == "__main__":
    main()
