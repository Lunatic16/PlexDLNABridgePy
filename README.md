# Plex DLNA Bridge for Samsung Speakers

A complete DLNA/UPnP bridge that makes Samsung multiroom speakers discoverable and controllable by Plex Media Server. This allows you to cast audio from Plex directly to your Samsung speaker groups.

## Features

✅ **Full DLNA/UPnP Implementation**
- Complete AVTransport service (Play, Pause, Stop, SetURI)
- RenderingControl service (Volume, Mute)
- ConnectionManager service (Protocol info)
- Proper SOAP request/response handling
- SSDP device announcement and discovery
- M-SEARCH responder for active discovery

✅ **Samsung Speaker Control**
- Multi-speaker group management
- Synchronized playback across speakers
- Volume control across all speakers
- Play/Pause/Stop commands
- Direct URL playback

✅ **Plex Integration**
- Automatic device discovery
- Direct media streaming from Plex
- Metadata support
- Persistent device UUID

✅ **Diagnostic Tools**
- Connection testing script
- Discovery diagnostic tool
- Comprehensive troubleshooting guides
- Debug logging support

## Requirements

### Hardware
- Samsung multiroom speakers (R1, R3, R5, WAM series)
- Computer/server on the same network as speakers and Plex
- Plex Media Server

### Software
```bash
pip install pywam plexapi requests
```

## Setup Instructions

### 1. Find Your Speaker IPs

Find your Samsung speaker IP addresses using one of these methods:

**Method A: Router Admin Panel**
- Log into your router
- Look for connected devices
- Find Samsung speakers in the device list

**Method B: Network Scanner**
```bash
# Linux/Mac
sudo nmap -sn 192.168.1.0/24 | grep -B 2 "Samsung"

# Or use a GUI tool like Angry IP Scanner
```

**Method C: Samsung Multiroom App**
- Open the Samsung Multiroom app
- Go to Settings → Speaker Settings
- View network information for each speaker

### 2. Get Your Plex Token

1. Open Plex Web App (https://app.plex.tv)
2. Play any media item
3. Click the three dots (•••) on the player
4. Select "Get Info"
5. Click "View XML"
6. Look for `X-Plex-Token=` in the URL
7. Copy the token value (everything after `X-Plex-Token=` until the next `&`)

Example URL:
```
https://plex.tv/library/metadata/12345?X-Plex-Token=abcdef123456789
                                        ^^^^^^^^^^^^^^^^^^^
                                        This is your token
```

### 3. Configure the Script

Edit `plex_dlna_bridge_full.py` and update these configuration values:

```python
# --- CONFIGURATION ---
PLEX_URL = 'http://192.168.1.100:32400'  # Your Plex server IP and port
PLEX_TOKEN = 'your_plex_token_here'      # Token from step 2
GROUP_NAME = "Living Room R1 Group"      # Friendly name for your group
DLNA_DEVICE_NAME = "Samsung Speaker Group"  # Name shown in Plex
DLNA_SERVER_PORT = 32488                 # Port for DLNA server (usually fine as-is)

# Your Samsung speaker IPs
SPEAKER_IPS = [
    '192.168.1.101',  # Replace with actual IPs from step 1
    '192.168.1.102',
    # Add more as needed
]
```

### 4. Run the Bridge

**First, test your configuration:**
```bash
python test_connection.py
```

This will verify:
- All dependencies are installed
- Configuration is valid
- Speakers are reachable
- Plex server is accessible

**If tests pass, run the bridge:**
```bash
python plex_dlna_bridge_full.py
```

**Note:** On Linux/Mac, you may need elevated privileges for port 1900:
```bash
sudo python plex_dlna_bridge_full.py
```

You should see:
```
============================================================
Starting Plex DLNA Bridge for Samsung Speakers
============================================================
INFO - Connected to speaker at 192.168.1.101
INFO - Connected to speaker at 192.168.1.102
INFO - Successfully connected to 2 Samsung speakers
INFO - DLNA server started on port 32488
INFO - SSDP responder listening for M-SEARCH requests
INFO - Connected to Plex: My Plex Server
============================================================
✓ Samsung speaker group 'Living Room R1 Group' is now discoverable
✓ Appearing to Plex as 'Samsung Speaker Group'
✓ DLNA server running on port 32488
✓ SSDP responder active on port 1900
✓ Ready for playback commands from Plex
============================================================
```

### 5. Use with Plex

1. Open Plex (web, mobile, or desktop app)
2. Start playing any audio track
3. Click the **Cast** icon (📡) in the player controls
4. Select **"Samsung Speaker Group"** from the device list
5. Music will now play through your Samsung speakers!

**⚠️ If device doesn't appear in Plex:**
This is the most common issue. The device may not be discoverable due to firewall or network configuration. See the **Troubleshooting** section below, or run:
```bash
python diagnose_discovery.py
```

This tool will identify exactly why Plex can't see the device and provide specific solutions.

## Troubleshooting

### Problem: Speakers not connecting

**Symptoms:**
```
Failed to connect to speaker at 192.168.1.101
```

**Solutions:**
1. Verify speaker IPs are correct
   ```bash
   ping 192.168.1.101
   ```
2. Ensure speakers are powered on and connected to WiFi
3. Check that you're on the same network as the speakers
4. Try resetting the speakers (hold power button for 10 seconds)
5. Update Samsung Multiroom app and speaker firmware

### Problem: Plex can't discover the device ⭐ MOST COMMON ISSUE

**Symptoms:**
- Device doesn't appear in Plex's cast menu
- Bridge shows "Ready for playback" but Plex doesn't see it
- Works on some clients but not others

**Quick Diagnosis:**
Run the diagnostic tool to identify the exact problem:
```bash
python diagnose_discovery.py
```

This will test:
- Firewall and port configuration
- SSDP multicast sending/receiving
- M-SEARCH request detection
- HTTP server accessibility

**Most Common Causes:**

1. **Firewall blocking port 1900** (80% of cases)
   ```bash
   # Linux
   sudo ufw allow 32488/tcp comment 'DLNA HTTP'
   sudo ufw allow 1900/udp comment 'SSDP Discovery'
   
   # Run bridge with sudo for port 1900 access
   sudo python plex_dlna_bridge_full.py
   ```

2. **Different network subnets**
   - Plex server: 192.168.1.100 ✅
   - Bridge: 192.168.1.50 ✅
   - Bridge: 192.168.2.50 ❌ (wrong subnet!)

3. **Router blocking multicast**
   - Check router settings for IGMP Snooping (should be ENABLED)
   - Check for Multicast Filtering (should be DISABLED)
   - Check for AP/Client Isolation (should be DISABLED)

4. **Permission denied on port 1900**
   ```bash
   # Port 1900 needs elevated privileges on most systems
   sudo python plex_dlna_bridge_full.py
   ```

**Step-by-Step Solutions:**
See the detailed guide: **DISCOVERY_TROUBLESHOOTING.md**

**Quick Fixes:**
```bash
# 1. Stop the bridge (Ctrl+C)

# 2. Restart Plex Media Server
# Linux: sudo systemctl restart plexmediaserver
# Windows: Services → Plex Media Server → Restart
# macOS: System Preferences → Plex → Restart

# 3. Open firewall ports
sudo ufw allow 32488/tcp
sudo ufw allow 1900/udp

# 4. Run bridge with elevated privileges
sudo python plex_dlna_bridge_full.py

# 5. Wait 30 seconds, then refresh Plex client

# 6. Try Plex web interface (most reliable)
# Open app.plex.tv in browser
```

**Verification:**
When working correctly, you should see in the logs:
```
✓ DLNA server running on port 32488
✓ SSDP responder active on port 1900
✓ Ready for playback commands from Plex
```

And when Plex searches for devices:
```
DEBUG - Received M-SEARCH from 192.168.1.100, responding...
```

If you don't see M-SEARCH requests, the issue is network/firewall related.

### Problem: Plex token invalid

**Symptoms:**
```
Failed to connect to Plex: 401 Client Error: Unauthorized
```

**Solutions:**
1. Verify token is correct (no extra spaces or characters)
2. Token may have expired - get a fresh token
3. Ensure Plex server URL is correct
4. Check that Plex server is running

### Problem: Media plays but no audio

**Symptoms:**
- Plex shows media is playing
- No sound from speakers
- Bridge logs show "Playback started successfully"

**Solutions:**
1. Check speaker volume isn't muted or set to 0
2. Verify audio format is supported:
   - Samsung speakers support: MP3, AAC, FLAC, WAV
   - Check Plex transcoding settings
3. Try playing a different audio file
4. Check speaker group is properly configured in Samsung app
5. Restart the speakers

### Problem: Only one speaker plays

**Symptoms:**
- Audio only comes from one speaker in the group
- Other speakers remain silent

**Solutions:**
1. Create a speaker group in Samsung Multiroom app first
2. Ensure all speakers are on the same network
3. Update all speaker firmware to the same version
4. Check that all speakers are added to `SPEAKER_IPS`

### Problem: Script crashes with async errors

**Symptoms:**
```
RuntimeError: Event loop is closed
asyncio.exceptions.InvalidStateError
```

**Solutions:**
1. Update Python to 3.7 or newer:
   ```bash
   python --version  # Should be 3.7+
   ```
2. Update pywam library:
   ```bash
   pip install --upgrade pywam
   ```
3. Check for conflicting async libraries

## Advanced Configuration

### Run as a System Service (Linux)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/plex-dlna-bridge.service
```

Add this content:
```ini
[Unit]
Description=Plex DLNA Bridge for Samsung Speakers
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/plex-bridge
ExecStart=/usr/bin/python3 /home/your_username/plex-bridge/plex_dlna_bridge_full.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable plex-dlna-bridge
sudo systemctl start plex-dlna-bridge
sudo systemctl status plex-dlna-bridge
```

View logs:
```bash
sudo journalctl -u plex-dlna-bridge -f
```

### Run on Startup (Windows)

1. Create a batch file `start_bridge.bat`:
```batch
@echo off
cd C:\path\to\plex-bridge
python plex_dlna_bridge_full.py
pause
```

2. Press `Win+R`, type `shell:startup`, press Enter
3. Create a shortcut to `start_bridge.bat` in the Startup folder

### Run on Startup (macOS)

Create a LaunchAgent plist:
```bash
nano ~/Library/LaunchAgents/com.plexbridge.plist
```

Add this content:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.plexbridge</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/plex_dlna_bridge_full.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.plexbridge.plist
```

### Change DLNA Port

If port 32488 is in use:
```python
DLNA_SERVER_PORT = 32489  # Use any available port
```

Remember to update firewall rules for the new port.

### Enable Debug Logging

Change logging level for more detailed output:
```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
```

## Technical Details

### UPnP/DLNA Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Plex Server   │────────▶│  DLNA Bridge     │────────▶│ Samsung Speakers│
│                 │  HTTP   │                  │  pywam  │                 │
│ - Media Library │  SOAP   │ - DLNA Server    │  API    │ - Speaker 1     │
│ - Transcoding   │  UPnP   │ - Protocol Trans │         │ - Speaker 2     │
│ - M-SEARCH      │         │ - State Manager  │         │ - Speaker N     │
└─────────────────┘         │ - SSDP Responder │         └─────────────────┘
        │                    └──────────────────┘                 │
        │                            │                            │
        │                            ▼                            │
        │                    ┌──────────────┐                    │
        └───────────────────▶│ SSDP/mDNS    │◀───────────────────┘
                             │ Discovery    │
                             │ Port 1900    │
                             └──────────────┘
```

### Discovery Mechanism

The bridge uses a two-pronged approach for device discovery:

1. **SSDP NOTIFY (Passive)**
   - Broadcasts device presence every 5 minutes
   - Announces on multicast address 239.255.255.250:1900
   - Includes device location URL

2. **M-SEARCH Response (Active)** ⭐ NEW
   - Listens for discovery requests on port 1900
   - Responds immediately when Plex searches
   - Significantly faster discovery
   - More reliable than passive announcements

This dual approach ensures maximum compatibility with all Plex clients.

### Supported UPnP Actions

**AVTransport Service:**
- `SetAVTransportURI` - Set media URL
- `Play` - Start playback
- `Pause` - Pause playback
- `Stop` - Stop playback
- `GetTransportInfo` - Get playback state
- `GetPositionInfo` - Get current position

**RenderingControl Service:**
- `SetVolume` - Set volume level (0-100)
- `GetVolume` - Get current volume
- `SetMute` - Mute/unmute
- `GetMute` - Get mute state

**ConnectionManager Service:**
- `GetProtocolInfo` - Get supported protocols

### Supported Audio Formats

The bridge supports any format that:
1. Plex can serve
2. Samsung speakers can decode

Common formats:
- MP3 (most compatible)
- AAC/M4A
- FLAC (lossless)
- WAV
- WMA

Plex will automatically transcode unsupported formats.

## Performance Tips

1. **Use Wired Connection:** Connect the computer running the bridge via Ethernet for best stability
2. **Static IPs:** Assign static IPs to Samsung speakers so configuration doesn't change
3. **Same Network:** Keep all devices on the same network/VLAN
4. **Router Quality:** Use a quality router with good multicast support
5. **Firmware Updates:** Keep Samsung speaker firmware updated

## Security Notes

- The Plex token provides full access to your Plex server - keep it secure
- The DLNA bridge listens on 0.0.0.0 (all interfaces) - use firewall rules if on public network
- Consider running on a dedicated machine or container for isolation

## Project Files

- **plex_dlna_bridge_full.py** - Main bridge application
- **test_connection.py** - Pre-flight connection testing
- **diagnose_discovery.py** - Discovery diagnostic tool
- **README.md** - Complete documentation
- **QUICKSTART.md** - 5-minute setup guide
- **DISCOVERY_TROUBLESHOOTING.md** - Detailed discovery troubleshooting
- **requirements.txt** - Python dependencies
- **config_template.py** - Configuration template

## Known Limitations

1. **Video Playback:** Only audio is supported (Samsung speakers are audio-only)
2. **Seeking:** Seek/skip functionality depends on pywam library support
3. **Multi-Zone:** Each speaker group needs a separate bridge instance
4. **Discovery Timing:** May take 30-60 seconds for Plex to discover device after starting
5. **Port 1900:** Requires elevated privileges on most systems (use sudo)

## Contributing

Found a bug? Have a feature request? Want to improve the code?

1. Test thoroughly with your setup
2. Document any changes clearly
3. Share your improvements!

## License

This project is provided as-is for personal use. Samsung and Plex are trademarks of their respective owners.

## Credits

- **pywam** - Samsung Wireless Audio Multiroom Python library
- **plexapi** - Python bindings for Plex API
- UPnP/DLNA specifications from upnp.org

## Changelog

### v1.1.0 (Discovery Fix)
- ✅ Added M-SEARCH responder for active discovery
- ✅ Significantly improved Plex discovery reliability
- ✅ Better network interface detection
- ✅ Higher multicast TTL for better propagation
- ✅ Added comprehensive discovery diagnostic tool
- ✅ Added detailed troubleshooting documentation
- ✅ Graceful handling of permission issues on port 1900

### v1.0.0 (Full Implementation)
- ✅ Complete UPnP/DLNA protocol implementation
- ✅ Full AVTransport service (Play, Pause, Stop)
- ✅ RenderingControl service (Volume, Mute)
- ✅ SOAP request/response handling
- ✅ Media state tracking
- ✅ Multi-speaker group support
- ✅ Proper error handling
- ✅ Async speaker control
- ✅ SSDP device announcement
- ✅ Persistent device UUID

---

**Enjoy your Samsung speakers with Plex! 🎵**
# PlexDLNABridgePy
