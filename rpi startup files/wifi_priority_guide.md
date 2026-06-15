# WiFi Network Priority Configuration for Raspberry Pi

Your Pi is using NetworkManager, which makes managing multiple WiFi networks easy.

## Current Network

You have one network configured:
- **Name:** Tim's A53
- **Device:** wlan0
- **Status:** Connected

## Adding Multiple WiFi Networks with Priority

NetworkManager uses `connection.autoconnect-priority` to determine which network to prefer. **Higher numbers = higher priority** (range: -999 to 999, default: 0).

### Step 1: View Current Priority

```bash
nmcli connection show "Tim's A53" | grep autoconnect
```

### Step 2: Set Priority for Current Network

```bash
# Set Tim's A53 as highest priority (e.g., priority 100)
sudo nmcli connection modify "Tim's A53" connection.autoconnect-priority 100
```

### Step 3: Add Additional WiFi Networks

For each WiFi network you want to add:

```bash
# Add a new WiFi network with specific priority
sudo nmcli device wifi connect "NetworkName" password "NetworkPassword" name "MyNetworkName"

# Then set its priority (lower than your main network)
sudo nmcli connection modify "MyNetworkName" connection.autoconnect-priority 50
```

**Example - Adding a home and office network:**

```bash
# Home network (highest priority - 100)
sudo nmcli connection modify "Tim's A53" connection.autoconnect-priority 100

# Office network (medium priority - 50)
sudo nmcli device wifi connect "OfficeWiFi" password "office123" name "Office"
sudo nmcli connection modify "Office" connection.autoconnect-priority 50

# Backup/Guest network (low priority - 10)
sudo nmcli device wifi connect "GuestWiFi" password "guest123" name "Guest"
sudo nmcli connection modify "Guest" connection.autoconnect-priority 10
```

### Step 4: Verify Configuration

```bash
# List all connections with priorities
nmcli -f NAME,UUID,TYPE,AUTOCONNECT,AUTOCONNECT-PRIORITY connection show
```

## How It Works

1. When Pi boots, it scans for available networks
2. If multiple known networks are in range, it connects to the one with **highest priority**
3. If that network disconnects, it automatically tries the next highest priority network
4. Networks with `autoconnect-priority: 0` or negative values are only used if higher priority ones aren't available

## Quick Reference Commands

### List All WiFi Networks

```bash
# Scan for available networks
sudo nmcli device wifi rescan
nmcli device wifi list
```

### View All Saved Connections

```bash
nmcli connection show
```

### View Detailed Connection Info

```bash
nmcli connection show "Tim's A53"
```

### Connect to a Network Manually

```bash
# If network is already saved
nmcli connection up "NetworkName"

# New network
sudo nmcli device wifi connect "SSID" password "password"
```

### Disconnect from Current Network

```bash
nmcli connection down "Tim's A53"
```

### Delete a Saved Network

```bash
sudo nmcli connection delete "NetworkName"
```

### Disable Auto-Connect for a Network

```bash
sudo nmcli connection modify "NetworkName" connection.autoconnect no
```

### Re-enable Auto-Connect

```bash
sudo nmcli connection modify "NetworkName" connection.autoconnect yes
```

## Testing Your Priority Setup

1. **Set priorities for all your networks** (higher = more preferred)

2. **Test automatic switching:**
   ```bash
   # Disconnect current network
   nmcli connection down "Tim's A53"
   
   # Watch it reconnect (should go to next available priority network)
   watch -n 1 nmcli device status
   ```

3. **Verify which network is active:**
   ```bash
   nmcli connection show --active
   ```

## Recommended Priority Strategy

Here's a suggested priority scheme:

- **100+** : Most preferred networks (home, main office)
- **50-99** : Secondary networks (backup locations)
- **10-49** : Guest/public networks (lower security)
- **0**     : Default (no preference)
- **Negative** : Only connect if nothing else available

## Example: My Setup

```bash
# Home (best connection)
sudo nmcli connection modify "Tim's A53" connection.autoconnect-priority 100

# Workshop (good connection)
sudo nmcli device wifi connect "WorkshopWiFi" password "workshop123" name "Workshop"
sudo nmcli connection modify "Workshop" connection.autoconnect-priority 80

# Mobile hotspot (backup)
sudo nmcli device wifi connect "iPhone" password "hotspot123" name "MobileHotspot"
sudo nmcli connection modify "MobileHotspot" connection.autoconnect-priority 20
```

## Next Steps: Adding Access Point

Once you've tested WiFi priority and you're happy with automatic network switching, you can add the WiFi Access Point feature so you'll have:

1. **wlan0**: Automatically connects to your preferred WiFi networks (for internet)
2. **wlan0 AP mode** OR **wlan1 (USB adapter) AP mode**: Your own "LaserPi-Network" for direct SSH access

This gives you maximum flexibility - your Pi will always be accessible!

---

## Troubleshooting

### Pi Won't Auto-Connect

```bash
# Check if auto-connect is enabled
nmcli connection show "NetworkName" | grep autoconnect

# Enable it
sudo nmcli connection modify "NetworkName" connection.autoconnect yes
```

### Check WiFi Status

```bash
nmcli radio wifi
# If off, turn it on:
nmcli radio wifi on
```

### View Connection Logs

```bash
sudo journalctl -u NetworkManager -f
```

### Reset Network Settings (if things get messed up)

```bash
# Restart NetworkManager
sudo systemctl restart NetworkManager

# Or reboot
sudo reboot
```
