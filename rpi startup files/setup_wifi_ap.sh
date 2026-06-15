#!/bin/bash
# Setup script to configure Raspberry Pi as a WiFi Access Point
# Run this script with: sudo bash setup_wifi_ap.sh

set -e  # Exit on error

echo "========================================="
echo "Raspberry Pi WiFi Access Point Setup"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "Step 1: Installing required packages..."
apt-get update
apt-get install -y hostapd dnsmasq

echo ""
echo "Step 2: Stopping services..."
systemctl stop hostapd
systemctl stop dnsmasq

echo ""
echo "Step 3: Configuring static IP for wlan0..."
# Backup original dhcpcd.conf
cp /etc/dhcpcd.conf /etc/dhcpcd.conf.backup

# Add static IP configuration if not already present
if ! grep -q "interface wlan0" /etc/dhcpcd.conf; then
    cat >> /etc/dhcpcd.conf << EOF

# Static IP configuration for Access Point
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF
    echo "Static IP configured."
else
    echo "Static IP already configured."
fi

echo ""
echo "Step 4: Backing up dnsmasq configuration..."
mv /etc/dnsmasq.conf /etc/dnsmasq.conf.backup

echo ""
echo "Step 5: Copying configuration files..."
if [ -f "./dnsmasq.conf" ]; then
    cp ./dnsmasq.conf /etc/dnsmasq.conf
    echo "dnsmasq.conf copied."
else
    echo "ERROR: dnsmasq.conf not found in current directory!"
    exit 1
fi

if [ -f "./hostapd.conf" ]; then
    cp ./hostapd.conf /etc/hostapd/hostapd.conf
    echo "hostapd.conf copied."
else
    echo "ERROR: hostapd.conf not found in current directory!"
    exit 1
fi

echo ""
echo "Step 6: Configuring hostapd daemon..."
# Update hostapd default file
sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|g' /etc/default/hostapd

echo ""
echo "Step 7: Enabling services..."
systemctl unmask hostapd
systemctl enable hostapd
systemctl enable dnsmasq

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "IMPORTANT: Edit /etc/hostapd/hostapd.conf to change:"
echo "  - SSID (network name): currently 'LaserPi-Network'"
echo "  - Password: currently 'laserpi123'"
echo "  - Country code: currently 'US'"
echo ""
echo "To apply changes, reboot your Raspberry Pi:"
echo "  sudo reboot"
echo ""
echo "After reboot, you should see the WiFi network 'LaserPi-Network'"
echo "Connect with password: laserpi123"
echo "Then SSH to: ssh pi@192.168.4.1"
echo ""
