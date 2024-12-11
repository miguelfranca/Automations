from smartthings_api import *
import platform
os_name = platform.system()

if os_name == "Linux":
    import dbus
    import dbus.mainloop.glib
    from gi.repository import GLib
    import subprocess
elif os_name == "Windows":
    import win32com.client
    import pythoncom

# Example usage
SMART_PLUG_ID = load_parameter(".config", "SMART_PLUG_ID")
# toggle_switch(SMART_PLUG_ID, "on")  # Turn on the smart plug
# toggle_switch(SMART_PLUG_ID, "off")  # Turn off the smart plug

BATTERY_CHARGED_THRESHOLD = 95
BATTERY_NOT_CHARGED_THRESHOLD = 20

last_sent_percentage = None  # To prevent duplicate requests

def handle_battery_status(percentage, state):
    """Handle battery status changes for both Linux and Windows."""
    global last_sent_percentage

    if state == 1:
        print(f"Status: Charging - {percentage}%")
    elif state == 2:
        print(f"Status: Discharging - {percentage}%")
    elif state == 4:
        print(f"Status: Fully Charged - {percentage}%")
    else:
        print(f"Unknown state {state}")

    if percentage <= BATTERY_NOT_CHARGED_THRESHOLD and state == 2:
        toggle_switch(SMART_PLUG_ID, "on")
        last_sent_percentage = percentage  # Update last sent percentage

    if (percentage > BATTERY_CHARGED_THRESHOLD and state == 1) or (state == 4 and percentage == 100):
        toggle_switch(SMART_PLUG_ID, "off")
        last_sent_percentage = percentage  # Update last sent percentage

    print()

def get_battery_path():
    """Fetch the battery device path using the 'upower' command (Linux only)."""
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

def get_battery_percentage_and_state_linux(battery_path):
    """Fetch the battery percentage and state directly from UPower (Linux only)."""
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

def battery_status_changed_linux(interface, changed_properties, invalidated_properties, battery_path):
    """Callback triggered when battery properties change (Linux only)."""
    global last_sent_percentage

    percentage, state = get_battery_percentage_and_state_linux(battery_path)

    if percentage is None:
        print("Could not fetch battery percentage.")
        return

    handle_battery_status(percentage, state)

def battery_status_listener_linux():
    battery_path = get_battery_path()
    if not battery_path:
        print("Battery path could not be determined. Exiting.")
        return

    print(f"Using battery path: {battery_path}")

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    bus.add_signal_receiver(
        lambda interface, changed_properties, invalidated_properties: battery_status_changed_linux(
            interface, changed_properties, invalidated_properties, battery_path
        ),
        dbus_interface="org.freedesktop.DBus.Properties",
        path=battery_path
    )

    print("Listening for battery status changes...")
    loop = GLib.MainLoop()
    loop.run()

def battery_event_handler_windows(event):
    battery = event.TargetInstance
    percentage = battery.EstimatedChargeRemaining
    charging = battery.BatteryStatus == 1  # Charging state
    state = 1 if charging else 2 if percentage < 100 else 4
    handle_battery_status(percentage, state)

def battery_status_listener_windows():
    wmi = win32com.client.Dispatch("WbemScripting.SWbemLocator")
    conn = wmi.ConnectServer(".", "root\\cimv2")
    query = "SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_Battery'"
    event_source = conn.ExecNotificationQuery(query)
    print("Listening for battery status changes on Windows...")

    while True:
        try:
            pythoncom.PumpWaitingMessages()
            event = event_source.NextEvent()
            battery_event_handler_windows(event)
        except Exception as e:
            print(f"Error in WMI event listener: {e}")
            break

def main():
    if os_name == "Linux":
        print("Setting up event listener for Linux...")
        battery_status_listener_linux()  

    elif os_name == "Windows":
        print("Setting up event listener for Windows...")
        battery_status_listener_windows()

    else:
        print(f"Unsupported OS: {os_name}. Exiting.")

if __name__ == "__main__":
    main()
