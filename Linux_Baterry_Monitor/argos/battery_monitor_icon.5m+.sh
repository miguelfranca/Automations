#!/bin/bash

SERVICE_NAME="battery_monitor.service"

if systemctl is-active --quiet $SERVICE_NAME; then
    echo "🟢"
else
    echo "🔴"
fi

echo "---" 
echo "Restart Service | bash='systemctl restart $SERVICE_NAME' terminal=false"
echo "Stop Service | bash='systemctl stop $SERVICE_NAME' terminal=false"
