#!/bin/bash
# Setup script to configure LaserPi Python script to run on startup
# Run this script with: bash setup_autostart.sh

set -e  # Exit on error

echo "========================================="
echo "LaserPi Auto-Start Setup"
echo "========================================="
echo ""

# Variables (modify these if your paths are different)
LASERPI_DIR="/home/pi/LaserPi"
SERVICE_FILE="laserpi.service"
STARTUP_SCRIPT="startup_script.py"

echo "Step 1: Checking if LaserPi directory exists..."
if [ ! -d "$LASERPI_DIR" ]; then
    echo "ERROR: LaserPi directory not found at $LASERPI_DIR"
    echo "Please clone/copy your LaserPi code to $LASERPI_DIR first"
    exit 1
fi
echo "LaserPi directory found."

echo ""
echo "Step 2: Copying startup script..."
if [ -f "./$STARTUP_SCRIPT" ]; then
    cp ./$STARTUP_SCRIPT $LASERPI_DIR/$STARTUP_SCRIPT
    chmod +x $LASERPI_DIR/$STARTUP_SCRIPT
    echo "Startup script copied and made executable."
else
    echo "WARNING: $STARTUP_SCRIPT not found. You'll need to create it manually."
fi

echo ""
echo "Step 3: Installing Python dependencies..."
if [ -f "$LASERPI_DIR/requirements.txt" ]; then
    pip3 install -r $LASERPI_DIR/requirements.txt
    echo "Dependencies installed."
else
    echo "WARNING: requirements.txt not found. You may need to install dependencies manually."
fi

echo ""
echo "Step 4: Installing systemd service..."
if [ -f "./$SERVICE_FILE" ]; then
    sudo cp ./$SERVICE_FILE /etc/systemd/system/$SERVICE_FILE
    echo "Service file copied."
else
    echo "ERROR: $SERVICE_FILE not found in current directory!"
    exit 1
fi

echo ""
echo "Step 5: Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable laserpi.service

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "The LaserPi service is now configured to start on boot."
echo ""
echo "Useful commands:"
echo "  Start service now:   sudo systemctl start laserpi"
echo "  Stop service:        sudo systemctl stop laserpi"
echo "  Check status:        sudo systemctl status laserpi"
echo "  View logs:           sudo journalctl -u laserpi -f"
echo "  Disable auto-start:  sudo systemctl disable laserpi"
echo ""
echo "IMPORTANT: Edit $LASERPI_DIR/$STARTUP_SCRIPT"
echo "to customize what runs when your Pi starts up!"
echo ""
