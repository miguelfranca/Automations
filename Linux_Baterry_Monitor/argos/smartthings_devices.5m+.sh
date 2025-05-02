#!/bin/bash
SMARTTHINGS_ICON=$(cat "/home/miguel/.config/argos/smartthings_icon.png")
echo " | image='$SMARTTHINGS_ICON' imageHeight=27  href='https://en.wikipedia.org'"
echo "---"

if [ "$ARGOS_MENU_OPEN" == "false" ]; then
  echo "Loading..."
  exit 0
fi

PYTHON_SCRIPT_PATH="/home/miguel/Documents/MiguelFranca/Programing/Python/Automations/Linux_Baterry_Monitor/smartthings_api.py"
DEVICE_LOG="/home/miguel/Documents/MiguelFranca/Programing/Python/Automations/Linux_Baterry_Monitor/smartthings_devices.log"

# Refresh the list of devices and their states
python3 $PYTHON_SCRIPT_PATH --display-devices > $DEVICE_LOG

# Check if the device log is empty
if [ ! -s $DEVICE_LOG ]; then
    echo "No Smart Plugs found | color=red"
else
    CURRENT_DEVICE_NAME=""
    CURRENT_DEVICE_ID=""
    CURRENT_SWITCH_STATUS=""

    while IFS= read -r line; do
        # Capture device name
        if [[ $line == Device\ Name:* ]]; then
            CURRENT_DEVICE_NAME=$(echo "$line" | sed 's/^Device Name: //')
        elif [[ $line == Device\ ID:* ]]; then
            CURRENT_DEVICE_ID=$(echo "$line" | sed 's/^Device ID: //')
        elif [[ $line == Switch\ Status:* ]]; then
            CURRENT_SWITCH_STATUS=$(echo "$line" | sed 's/^Switch Status: //')

            # Check if the device is a Smart Plug
            if [[ $CURRENT_DEVICE_NAME == *Smart\ Plug* ]]; then
                TOGGLE_STATE="on"
                [[ "$CURRENT_SWITCH_STATUS" == "On" ]] && TOGGLE_STATE="off"

                # Display the device name and toggle action
                echo "$CURRENT_DEVICE_NAME ($CURRENT_SWITCH_STATUS)"
                echo "-- Toggle | bash='python3 $PYTHON_SCRIPT_PATH --toggle-switch $CURRENT_DEVICE_ID $TOGGLE_STATE' terminal=false refresh=true"
            fi

            # Reset variables for the next device
            CURRENT_DEVICE_NAME=""
            CURRENT_DEVICE_ID=""
            CURRENT_SWITCH_STATUS=""
        fi
    done < $DEVICE_LOG
fi

echo "Refresh | bash='python3 $PYTHON_SCRIPT_PATH --display-devices' refresh=true terminal=false"
