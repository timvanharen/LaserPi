# Raspberry Pi Setup Files for LaserPi

This directory contains configuration files to set up your Raspberry Pi as a WiFi access point and configure LaserPi to run automatically on startup.

## Overview

1. **WiFi Access Point Setup** - Makes your Pi broadcast its own WiFi network so you can connect directly without needing an existing WiFi network
2. **Auto-Start Service** - Automatically runs your LaserPi Python script when the Pi boots up

---

## Part 1: WiFi Access Point Setup

This allows your Raspberry Pi to create its own WiFi network that you can connect to with your laptop.

### Files Needed
- `hostapd.conf` - Access point configuration
- `dnsmasq.conf` - DHCP server configuration
- `setup_wifi_ap.sh` - Automated setup script

### Installation Steps

1. **Copy files to your Raspberry Pi:**
   ```bash
   # From your laptop (adjust IP if different)
   scp hostapd.conf dnsmasq.conf setup_wifi_ap.sh pi@<pi-ip-address>:~/
   ```

2. **SSH into your Pi:**
   ```bash
   ssh pi@<pi-ip-address>
   ```

3. **IMPORTANT: Customize hostapd.conf before running setup:**
   ```bash
   nano hostapd.conf
   ```
   Change these settings:
   - `ssid=LaserPi-Network` - Change to your preferred network name
   - `wpa_passphrase=laserpi123` - Change to a secure password (8+ characters)
   - `country_code=US` - Change to your country code (US, GB, DE, etc.)

4. **Run the setup script:**
   ```bash
   sudo bash setup_wifi_ap.sh
   ```

5. **Reboot your Pi:**
   ```bash
   sudo reboot
   ```

6. **Connect to your Pi:**
   - Look for the WiFi network "LaserPi-Network" (or whatever you named it)
   - Connect using the password you set laserpi123
   - SSH to: `ssh pi@192.168.4.1`

### Troubleshooting WiFi AP

- **Can't see the network?** Check hostapd status:
  ```bash
  sudo systemctl status hostapd
  ```

- **Can't get an IP address?** Check dnsmasq status:
  ```bash
  sudo systemctl status dnsmasq
  ```

- **View logs:**
  ```bash
  sudo journalctl -u hostapd -f
  sudo journalctl -u dnsmasq -f
  ```

- **Disable AP and return to normal WiFi:**
  ```bash
  sudo systemctl stop hostapd
  sudo systemctl stop dnsmasq
  sudo systemctl disable hostapd
  sudo systemctl disable dnsmasq
  # Restore original dhcpcd.conf
  sudo cp /etc/dhcpcd.conf.backup /etc/dhcpcd.conf
  sudo reboot
  ```

---

## Part 2: Auto-Start LaserPi on Boot

This configures your LaserPi Python script to run automatically when the Raspberry Pi starts.

### Files Needed
- `laserpi.service` - Systemd service definition
- `startup_script.py` - Python script that runs on boot
- `setup_autostart.sh` - Automated setup script

### Installation Steps

1. **Ensure LaserPi code is on your Pi:**
   ```bash
   # Clone or copy your LaserPi repository to /home/pi/LaserPi
   cd /home/pi
   git clone <your-repo-url> LaserPi
   # Or use scp to copy files
   ```

2. **Copy the startup files to your Pi:**
   ```bash
   # From your laptop
   scp laserpi.service startup_script.py setup_autostart.sh pi@192.168.4.1:~/
   ```

3. **SSH into your Pi:**
   ```bash
   ssh pi@192.168.4.1
   ```

4. **Customize startup_script.py:**
   ```bash
   nano startup_script.py
   ```
   Edit the main() function to include your specific laser control logic.

5. **Run the setup script:**
   ```bash
   bash setup_autostart.sh
   ```

6. **Test the service:**
   ```bash
   # Start it manually
   sudo systemctl start laserpi
   
   # Check status
   sudo systemctl status laserpi
   
   # View logs
   sudo journalctl -u laserpi -f
   ```

7. **Reboot to test auto-start:**
   ```bash
   sudo reboot
   ```

### Useful Commands

- **Start service:** `sudo systemctl start laserpi`
- **Stop service:** `sudo systemctl stop laserpi`
- **Restart service:** `sudo systemctl restart laserpi`
- **Check status:** `sudo systemctl status laserpi`
- **View logs:** `sudo journalctl -u laserpi -f`
- **View all logs:** `sudo journalctl -u laserpi`
- **Disable auto-start:** `sudo systemctl disable laserpi`
- **Enable auto-start:** `sudo systemctl enable laserpi`

### Customization

The default service runs `/home/pi/LaserPi/startup_script.py`. To change this:

1. Edit the service file paths:
   ```bash
   sudo nano /etc/systemd/system/laserpi.service
   ```

2. Reload systemd:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Restart the service:
   ```bash
   sudo systemctl restart laserpi
   ```

---

## Complete Setup Workflow

If you're setting up a fresh Raspberry Pi:

1. **Initial Setup:**
   - Flash Raspberry Pi OS to SD card
   - Connect Pi to network temporarily (to install packages)
   - Update system: `sudo apt update && sudo apt upgrade -y`

2. **Copy all files to Pi:**
   ```bash
   scp -r "rpi startup files"/* pi@<pi-ip>:~/
   ```

3. **Set up WiFi AP:**
   ```bash
   ssh pi@<pi-ip>
   sudo bash setup_wifi_ap.sh
   ```

4. **Copy LaserPi code:**
   ```bash
   # From laptop or git clone
   ```

5. **Set up auto-start:**
   ```bash
   bash setup_autostart.sh
   ```

6. **Reboot and test:**
   ```bash
   sudo reboot
   ```

---

## Security Notes

- **Change the default WiFi password!** The default `laserpi123` is not secure.
- Consider setting up SSH key authentication instead of password authentication
- Keep your Raspberry Pi OS updated: `sudo apt update && sudo apt upgrade`
- If exposing to the internet, use a firewall (ufw)

---

## Additional Resources

- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [Systemd Service Files](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [hostapd Documentation](https://w1.fi/hostapd/)

---

## Troubleshooting

### LaserPi Service Issues

**Service won't start:**
- Check Python path: `which python3`
- Verify script location: `ls -l /home/pi/LaserPi/startup_script.py`
- Check permissions: `chmod +x /home/pi/LaserPi/startup_script.py`
- View detailed errors: `sudo journalctl -xe -u laserpi`

**Script runs but crashes:**
- Check the log file: `cat /home/pi/laserpi_startup.log`
- Verify dependencies installed: `pip3 list`
- Test script manually: `python3 /home/pi/LaserPi/startup_script.py`

### General Tips

- Always check logs: `sudo journalctl -u <service-name>`
- Test configurations before enabling auto-start
- Keep backups of working configurations
- Document any custom changes you make
