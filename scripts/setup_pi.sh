#!/bin/bash
# LaserPi Setup Script for Raspberry Pi 4
# Run this script once after cloning the repository

set -e  # Exit on error

echo "=============================="
echo "LaserPi Raspberry Pi Setup"
echo "=============================="
echo ""

# Check if running on a Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "   Continuing anyway..."
    echo ""
fi

# 1. Set hostname (optional)
echo "1. Setting hostname to 'laserpi'..."
CURRENT_HOSTNAME=$(hostname)
if [ "$CURRENT_HOSTNAME" != "laserpi" ]; then
    echo "   Current hostname: $CURRENT_HOSTNAME"
    read -p "   Change hostname to 'laserpi'? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo hostnamectl set-hostname laserpi
        echo "   ✓ Hostname changed to 'laserpi' (reboot required)"
    else
        echo "   Skipped hostname change"
    fi
else
    echo "   ✓ Hostname already set to 'laserpi'"
fi
echo ""

# 2. Add user to dialout group for serial port access
echo "2. Adding user to 'dialout' group for serial port access..."
if groups $USER | grep -q '\bdialout\b'; then
    echo "   ✓ User '$USER' already in 'dialout' group"
else
    sudo usermod -aG dialout $USER
    echo "   ✓ User '$USER' added to 'dialout' group"
    echo "   ⚠️  You must log out and back in for this to take effect!"
fi
echo ""

# 3. Create udev rule for USB-RS485 adapter
echo "3. Creating udev rule for CH340 USB-RS485 adapter..."
UDEV_RULE_FILE="/etc/udev/rules.d/99-dmx-adapter.rules"
if [ -f "$UDEV_RULE_FILE" ]; then
    echo "   ✓ udev rule already exists at $UDEV_RULE_FILE"
else
    echo "   Creating udev rule for stable device name '/dev/dmx0'..."
    echo '# DMX USB-RS485 Adapter' | sudo tee $UDEV_RULE_FILE > /dev/null
    echo '# CH340/CH341 adapter' | sudo tee -a $UDEV_RULE_FILE > /dev/null
    echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="dmx0", MODE="0666"' | sudo tee -a $UDEV_RULE_FILE > /dev/null
    echo '# FTDI FT232 adapter (uncomment if using FTDI)' | sudo tee -a $UDEV_RULE_FILE > /dev/null
    echo '#SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", SYMLINK+="dmx0", MODE="0666"' | sudo tee -a $UDEV_RULE_FILE > /dev/null
    
    # Reload udev rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    echo "   ✓ udev rule created and loaded"
fi
echo ""

# 4. Install Python dependencies
echo "4. Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    echo "   Installing from requirements.txt..."
    pip3 install --user -r requirements.txt
    echo "   ✓ Python dependencies installed"
else
    echo "   ❌ requirements.txt not found!"
    exit 1
fi
echo ""

# 5. Test USB adapter detection
echo "5. Checking for USB-RS485 adapter..."
if ls /dev/ttyUSB* 1> /dev/null 2>&1; then
    echo "   ✓ USB serial device(s) found:"
    ls -l /dev/ttyUSB* | awk '{print "      " $0}'
    echo ""
    echo "   Adapter information:"
    for dev in /dev/ttyUSB*; do
        echo "      Device: $dev"
        udevadm info -a -n $dev | grep -E 'idVendor|idProduct|manufacturer' | head -3 | sed 's/^/        /'
        echo ""
    done
else
    echo "   ⚠️  No /dev/ttyUSB* devices found"
    echo "      Make sure the USB-RS485 adapter is connected"
fi

if [ -e /dev/dmx0 ]; then
    echo "   ✓ /dev/dmx0 symlink exists (you can use this in config)"
else
    echo "   ℹ️  /dev/dmx0 symlink not created yet"
    echo "      Unplug and replug the adapter, or check vendor ID in udev rule"
fi
echo ""

# 6. Setup complete
echo "=============================="
echo "Setup Complete!"
echo "=============================="
echo ""
echo "Next steps:"
echo "  1. If you changed the hostname or added user to dialout group:"
echo "     Log out and log back in (or reboot)"
echo ""
echo "  2. Connect your USB-RS485 adapter to a USB port"
echo ""
echo "  3. Update src/laserpi/config.py if needed:"
echo "     - Set SERIAL_PORT to the correct device (e.g., '/dev/ttyUSB0' or '/dev/dmx0')"
echo "     - Verify LASER1_ADDRESS and LASER2_ADDRESS match your setup"
echo ""
echo "  4. Connect RS485 A/B wires to DMX connector:"
echo "     - RS485 A  → DMX Pin 3 (Data+)"
echo "     - RS485 B  → DMX Pin 2 (Data-)"
echo "     - Ground   → DMX Pin 1 (Common)"
echo ""
echo "  5. Test the setup:"
echo "     cd examples"
echo "     python3 basic_on.py"
echo ""
echo "Happy laser controlling! 🎆"
echo ""
