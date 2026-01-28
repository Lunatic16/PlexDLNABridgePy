# Plex Discovery Troubleshooting Guide

## Problem: Plex Cannot See the DLNA Bridge

If the bridge is running but Plex doesn't show your Samsung speakers in the cast menu, follow these steps:

---

## 🔍 Step 1: Run the Diagnostic Tool

First, run the diagnostic tool to identify the issue:

```bash
python diagnose_discovery.py
```

This will test:
- Multicast sending capability
- HTTP server accessibility
- M-SEARCH request detection

**Follow the on-screen instructions and note which tests fail.**

---

## 🔥 Step 2: Check Firewall Settings

The bridge needs these ports open:

### Linux (UFW)
```bash
# Check status
sudo ufw status

# Open required ports
sudo ufw allow 32488/tcp comment 'DLNA Bridge HTTP'
sudo ufw allow 1900/udp comment 'SSDP Discovery'

# Reload firewall
sudo ufw reload
```

### Linux (iptables)
```bash
# Check current rules
sudo iptables -L -n

# Add rules
sudo iptables -A INPUT -p tcp --dport 32488 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 1900 -j ACCEPT

# Save rules
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

### Windows
1. Open **Windows Defender Firewall**
2. Click **Advanced Settings**
3. Click **Inbound Rules** → **New Rule**
4. Select **Port** → **Next**
5. Choose **TCP** → Enter port **32488** → **Next**
6. Select **Allow the connection** → **Next**
7. Select all network types → **Next**
8. Name it "DLNA Bridge" → **Finish**
9. Repeat for **UDP port 1900**

### macOS
1. Open **System Preferences** → **Security & Privacy**
2. Click **Firewall** tab
3. Click lock icon to make changes
4. Click **Firewall Options**
5. Click **+** button
6. Add Python to allowed applications
7. Click **OK**

---

## 🌐 Step 3: Verify Network Configuration

### Same Network Check
```bash
# Get your computer's IP
# Linux/Mac:
ifconfig | grep "inet "

# Windows:
ipconfig

# Verify Plex server is on same subnet
# If your computer is 192.168.1.50
# Plex should be 192.168.1.X (same first 3 numbers)
```

### Test Connectivity
```bash
# Can you reach Plex from the bridge computer?
ping 192.168.1.100  # Replace with your Plex server IP

# Can you access Plex web interface?
curl http://192.168.1.100:32400/web
```

### Router Multicast Settings
Check your router settings for:
1. **IGMP Snooping** - Should be **ENABLED**
2. **Multicast Filtering** - Should be **DISABLED**
3. **AP Isolation** - Should be **DISABLED**
4. **Client Isolation** - Should be **DISABLED**

Common router admin addresses:
- `192.168.1.1`
- `192.168.0.1`
- `10.0.0.1`

---

## 🔄 Step 4: Restart Everything

Sometimes a simple restart fixes discovery issues:

```bash
# 1. Stop the bridge (Ctrl+C)

# 2. Restart Plex Media Server
# Linux:
sudo systemctl restart plexmediaserver

# Windows:
# Services → Plex Media Server → Restart

# macOS:
# System Preferences → Plex → Restart

# 3. Wait 30 seconds

# 4. Start the bridge again
python plex_dlna_bridge_full.py

# 5. Wait 30 seconds for discovery

# 6. Refresh Plex client (close and reopen app/browser)
```

---

## 🎯 Step 5: Test with Different Plex Clients

Try accessing from different clients:

1. **Plex Web** (app.plex.tv)
   - Open in browser
   - Play a track
   - Click cast icon (top right)

2. **Plex Desktop App**
   - Download from plex.tv
   - Play a track
   - Click cast icon

3. **Plex Mobile App**
   - iOS or Android
   - Play a track
   - Look for cast icon

**Note:** Some clients discover devices better than others. The web interface is usually the most reliable.

---

## 🔧 Step 6: Manual Verification

### Test the HTTP Server Directly
```bash
# From the same computer running the bridge:
curl http://localhost:32488/description.xml

# From another computer on the network:
curl http://192.168.1.50:32488/description.xml  # Replace with bridge computer IP
```

You should see XML output with:
```xml
<deviceType>urn:schemas-upnp-org:device:MediaRenderer:1</deviceType>
<friendlyName>Samsung Speaker Group</friendlyName>
```

If this fails:
- Bridge is not running
- Port 32488 is blocked
- Wrong IP address

### Test SSDP Multicast
```bash
# Install tcpdump (Linux/Mac) or Wireshark (Windows)

# Monitor SSDP traffic:
sudo tcpdump -i any -n -A 'udp port 1900'

# You should see NOTIFY messages every 5 minutes
# And M-SEARCH requests when Plex searches
```

---

## 🐛 Step 7: Enable Debug Logging

Edit `plex_dlna_bridge_full.py` and change:
```python
logging.basicConfig(level=logging.INFO, ...)
```
to:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

Run the bridge again and look for:
- `"SSDP responder listening for M-SEARCH requests"` 
- `"Received M-SEARCH from X.X.X.X, responding..."`

If you see M-SEARCH requests, the discovery mechanism is working!

---

## 📋 Step 8: Common Issues and Solutions

### Issue: "Permission denied" on port 1900
**Cause:** Port 1900 requires root/admin privileges on some systems

**Solution:**
```bash
# Linux:
sudo python plex_dlna_bridge_full.py

# Or use a higher port and port forwarding:
# Edit script: SSDP_PORT = 19000
sudo iptables -t nat -A PREROUTING -p udp --dport 1900 -j REDIRECT --to-port 19000
```

### Issue: "Address already in use" on port 32488
**Cause:** Another service is using the port

**Solution:**
```bash
# Find what's using the port:
# Linux/Mac:
sudo lsof -i :32488
sudo netstat -tulpn | grep 32488

# Windows:
netstat -ano | findstr :32488

# Kill the process or change the port in the script:
DLNA_SERVER_PORT = 32489
```

### Issue: Device appears then disappears
**Cause:** Network instability or multicast issues

**Solution:**
1. Use wired connection instead of WiFi
2. Increase announcement frequency (edit script):
   ```python
   announcement_interval = 60  # Changed from 300
   ```
3. Check router logs for multicast filtering

### Issue: Works on some devices, not others
**Cause:** Different Plex clients have different discovery capabilities

**Solution:**
1. Plex Web (app.plex.tv) - Most compatible ✅
2. Plex Desktop App - Usually good ✅  
3. Plex Mobile - May require manual device entry ⚠️
4. Plex Smart TVs - Often limited discovery ❌

For clients that can't discover automatically:
- Check if they support manual DLNA device entry
- Some clients only show devices when actively playing media

---

## 🆘 Step 9: Advanced Diagnostics

### Check Plex Logs
Plex logs may show why it's not discovering the device:

**Linux:**
```bash
tail -f "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log" | grep -i dlna
```

**Windows:**
```
%LOCALAPPDATA%\Plex Media Server\Logs\Plex Media Server.log
```

**macOS:**
```bash
tail -f "~/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log" | grep -i dlna
```

Look for errors like:
- "DLNA: Failed to fetch description"
- "DLNA: Invalid XML"
- "DLNA: Connection refused"

### Network Packet Capture
```bash
# Capture all DLNA/SSDP traffic
sudo tcpdump -i any -w dlna_capture.pcap 'port 1900 or port 32488'

# Analyze with Wireshark
wireshark dlna_capture.pcap
```

Look for:
1. NOTIFY messages being sent (every 5 minutes)
2. M-SEARCH requests from Plex
3. M-SEARCH responses being sent back

### Test with Another DLNA Client
Install another DLNA client to verify the bridge works:

**BubbleUPnP (Android):**
1. Install from Play Store
2. Open app → Devices
3. Should show "Samsung Speaker Group"

**VLC (Desktop):**
1. Open VLC
2. View → Playlist
3. Universal Plug'n'Play
4. Should show "Samsung Speaker Group"

If other clients see it but Plex doesn't:
- Issue is with Plex, not the bridge
- Try updating Plex to latest version
- Check Plex DLNA settings (Settings → Network → DLNA)

---

## ✅ Verification Checklist

Once working, you should see:

**In Bridge Logs:**
```
✓ Samsung speaker group 'Living Room R1 Group' is now discoverable
✓ Appearing to Plex as 'Samsung Speaker Group'
✓ DLNA server running on port 32488
✓ SSDP responder active on port 1900
✓ Ready for playback commands from Plex
```

**In Plex:**
1. Open Plex web/app
2. Start playing music
3. Click cast icon (📡)
4. See "Samsung Speaker Group" in device list ✅

**When Casting:**
```
DEBUG - Received M-SEARCH from 192.168.1.100, responding...
INFO - Setting transport URI: http://...
INFO - Starting playback of: http://...
INFO - Playback started successfully
```

---

## 🎉 Still Not Working?

If you've tried everything above:

1. **Ensure Prerequisites:**
   - Python 3.7+
   - All dependencies installed
   - Samsung speakers on same network
   - Plex server running

2. **Try Simplified Setup:**
   - Single speaker instead of group
   - Wired connection for bridge computer
   - Disable all firewalls temporarily to test
   - Use Plex web interface only

3. **Check Compatibility:**
   - Some Plex versions have DLNA bugs
   - Some Samsung speaker models have limitations
   - Some routers block multicast aggressively

4. **Alternative Approach:**
   - Use Plex's built-in DLNA renderer (if speakers support it)
   - Use Samsung's own streaming protocol
   - Use AirPlay/Bluetooth as fallback

---

## 📞 Getting More Help

If you're still stuck:

1. **Gather Information:**
   ```bash
   # Run diagnostic and save output
   python diagnose_discovery.py > diagnostic_output.txt
   
   # Include bridge logs
   python plex_dlna_bridge_full.py 2>&1 | tee bridge_output.txt
   
   # Include system info
   uname -a  # Linux/Mac
   systeminfo  # Windows
   ```

2. **Document Your Setup:**
   - Bridge computer OS and IP
   - Plex server OS and IP  
   - Samsung speaker models and IPs
   - Router model
   - Network topology (switches, VLANs, etc.)

3. **Check for Known Issues:**
   - Plex forums for DLNA problems
   - Samsung speaker compatibility lists
   - Router-specific multicast issues

---

**Good luck! Most discovery issues are firewall or network related and can be solved with the steps above.** 🎵
