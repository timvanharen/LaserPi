#!/bin/bash
# Setup script for Direct Laser Driver on Raspberry Pi
# Run as: bash scripts/setup.sh

set -e

echo "=== Direct Laser Driver Setup ==="
echo ""

# Check if running on a Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "Warning: This doesn't appear to be a Raspberry Pi."
    echo "Continuing anyway (useful for development)..."
    echo ""
fi

# Update package list
echo "Updating package list..."
sudo apt-get update -qq

# Install pigpio
echo "Installing pigpio..."
sudo apt-get install -y pigpio python3-pigpio

# Enable and start pigpiod daemon
echo "Enabling pigpio daemon..."
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Install Python dependencies
echo "Installing Python packages..."
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
pip3 install -r "$SCRIPT_DIR/requirements.txt"

# Enable UART (needed for TMC2209 communication)
echo "Configuring UART..."
if ! grep -q "enable_uart=1" /boot/config.txt 2>/dev/null; then
    echo "enable_uart=1" | sudo tee -a /boot/config.txt > /dev/null
    echo "  Added enable_uart=1 to /boot/config.txt"
else
    echo "  UART already enabled in /boot/config.txt"
fi

# Disable serial console (frees UART for TMC2209)
if grep -q "console=serial0" /boot/cmdline.txt 2>/dev/null; then
    sudo sed -i 's/console=serial0,[0-9]* //g' /boot/cmdline.txt
    echo "  Disabled serial console on UART"
else
    echo "  Serial console already disabled"
fi

# Add user to gpio group
echo "Adding user to gpio group..."
sudo usermod -aG gpio "$USER" 2>/dev/null || true

echo ""
echo "=== Setup Complete ==="
echo ""
echo "If UART was just enabled, please reboot: sudo reboot"
echo ""
echo "Quick test:"
echo "  python3 examples/motor_test.py"
echo "  python3 examples/laser_test.py"
