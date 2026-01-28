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
- Connection testing script (`diagnose_discovery.py`)
- Comprehensive troubleshooting guides
- Debug logging support

## Requirements

### Hardware
- Samsung multiroom speakers (R1, R3, R5, WAM series)
- Computer/server on the same network as speakers and Plex
- Plex Media Server

### Software
```bash
pip install -r requirements.txt
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

### 3. Configure the Bridge

Configuration is now managed via environment variables, ideally through a `.env` file.

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit the `.env` file and update these configuration values:

```ini
# --- CONFIGURATION ---
PLEX_URL="http://192.168.1.100:32400"  # Your Plex server IP and port
PLEX_TOKEN="your_plex_token_here"      # Token from step 2
GROUP_NAME="Living Room Group"         # Friendly name for your group
DLNA_DEVICE_NAME="Samsung Speaker Bridge" # Name shown in Plex
DLNA_SERVER_PORT=32488                 # Port for DLNA server (usually fine as-is)

# Your Samsung speaker IPs, comma-separated. Leave empty for auto-discovery.
SPEAKER_IPS="192.168.1.101,192.168.1.102"
# Set to True to enable automatic speaker discovery (recommended)
AUTO_DISCOVER_SPEAKERS=True

LOG_LEVEL="INFO"                       # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 4. Run the Bridge

Ensure you have installed the dependencies: `pip install -r requirements.txt`

**Option A: Python (Direct)**
```bash
python main.py
```

**Option B: Docker (Recommended)**
1. Ensure your `.env` file is configured.
2. Run:
```bash
docker-compose up -d --build
```
*Note: Docker requires `network_mode: host` for DLNA discovery to work, which is configured in `docker-compose.yml`.*

### 5. Use with Plex

1. Open Plex (web, mobile, or desktop app)
2. Start playing any audio track
3. Click the **Cast** icon (📡) in the player controls
4. Select **"Samsung Speaker Bridge"** (or whatever you set `DLNA_DEVICE_NAME` to) from the device list
5. Music will now play through your Samsung speakers!

**⚠️ If device doesn't appear in Plex:**
This is the most common issue. The device may not be discoverable due to firewall or network configuration. See the **Troubleshooting** section below, or run the diagnostic tool:
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
1. Verify speaker IPs are correct in `.env` or if auto-discovery is enabled, check network connectivity.
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
   
   # Run bridge with sudo for port 1900 access if binding to low port
   # Not typically needed with DLNA_SERVER_PORT=32488
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
   - Port 1900 requires elevated privileges on some systems. If you encounter issues, ensure `main.py` has necessary permissions or run with `sudo` if absolutely required (e.g., `sudo python main.py`).

**Step-by-Step Solutions:**
See the detailed guide: **DISCOVERY_TROUBLESHOOTING.md**

**Quick Fixes:**
```bash
# 1. Stop the bridge (Ctrl+C or docker-compose down)

# 2. Restart Plex Media Server
# Linux: sudo systemctl restart plexmediaserver
# Windows: Services → Plex Media Server → Restart
# macOS: System Preferences → Plex → Restart

# 3. Open firewall ports (if not already open)
sudo ufw allow 32488/tcp
sudo ufw allow 1900/udp

# 4. Run bridge (with elevated privileges if port 1900 binding fails)
python main.py # or docker-compose up -d

# 5. Wait 30 seconds, then refresh Plex client

# 6. Try Plex web interface (most reliable)
# Open app.plex.tv in browser
```

**Verification:**
When working correctly, you should see in the logs:
```
INFO - DLNA Server started on port 32488
INFO - Bridge is fully operational
```

And when Plex searches for devices:
```
DEBUG - Responding to M-SEARCH from (...)
```

If you don't see M-SEARCH requests, the issue is network/firewall related.

### Problem: Plex token invalid

**Symptoms:**
```
Failed to connect to Plex: 401 Client Error: Unauthorized
```

**Solutions:**
1. Verify token is correct in `.env` (no extra spaces or characters)
2. Token may have expired - get a fresh token from Plex
3. Ensure Plex server URL in `.env` is correct
4. Check that Plex server is running

### Problem: Media plays but no audio

**Symptoms:**
- Plex shows media is playing
- No sound from speakers
- Bridge logs show "Playback started successfully"

**Solutions:**
1. Check speaker volume isn't muted or set to 0 via the Samsung Multiroom app or Plex client.
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
4. Check that all speakers are added to `SPEAKER_IPS` in your `.env` file or are discoverable.

### Problem: Script crashes with async errors

**Symptoms:**
```
RuntimeError: Event loop is closed
asyncio.exceptions.InvalidStateError
```

**Solutions:**
1. Update Python to 3.8 or newer:
   ```bash
   python --version  # Should be 3.8+
   ```
2. Update pywam library and other dependencies:
   ```bash
   pip install --upgrade -r requirements.txt
   ```
3. Ensure no conflicting async libraries are running.

## Advanced Configuration

Configuration is primarily handled via the `.env` file. Refer to `bridge/config.py` for default values and available settings.

### Run as a System Service (Linux)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/plex-dlna-bridge.service
```

Add this content (update `User`, `WorkingDirectory`, and `ExecStart` paths):
```ini
[Unit]
Description=Plex DLNA Bridge for Samsung Speakers
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/PlexDLNABridgePy
ExecStart=/usr/bin/python3 /home/your_username/PlexDLNABridgePy/main.py
Restart=always
RestartSec=10
EnvironmentFile=/home/your_username/PlexDLNABridgePy/.env

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

1. Create a batch file `start_bridge.bat` in your project root:
```batch
@echo off
cd "C:\path\to\PlexDLNABridgePy"
"C:\path\to\python.exe" main.py
pause
```
   *(Update paths to match your Python installation and project directory)*

2. Press `Win+R`, type `shell:startup`, press Enter
3. Create a shortcut to `start_bridge.bat` in the Startup folder

### Run on Startup (macOS)

Create a LaunchAgent plist:
```bash
nano ~/Library/LaunchAgents/com.plexbridge.plist
```

Add this content (update `/path/to/python3` and `/path/to/PlexDLNABridgePy/main.py`):
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
        <string>/path/to/PlexDLNABridgePy/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/path/to/PlexDLNABridgePy</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.plexbridge.plist
```

## Testing

To run the basic test suite:

1. Install `pytest` if you haven't already:
   ```bash
   pip install pytest pytest-asyncio
   ```
2. Run tests from the project root:
   ```bash
   pytest tests/
   ```

## Technical Details

### UPnP/DLNA Architecture (Updated)

```
┌─────────────────┐          ┌──────────────────┐          ┌─────────────────┐
│   Plex Server   │────────▶│  DLNA Bridge     │────────▶│ Samsung Speakers│
│                 │  HTTP    │                  │  pywam   │                 │
│ - Media Library │  SOAP    │ - aiohttp Server │  API     │ - Speaker 1     │
│ - Transcoding   │  UPnP    │ - Media State    │          │ - Speaker 2     │
│ - M-SEARCH      │          │ - Speaker Mgr    │          │ - Speaker N     │
└─────────────────┘          │ - SSDP Responder │          └─────────────────┘
        │                    └──────────────────┘                  │
        │                            │                             │
        │                            ▼                             │
        │                    ┌──────────────┐                      │
        └──────────────────▶│ SSDP/mDNS    │◀────────────────────┘
                             │ Discovery    │
                             │ Port 1900    │
                             └──────────────┘
```

### Discovery Mechanism

The bridge uses a two-pronged approach for device discovery:

1. **SSDP NOTIFY (Passive)**
   - Broadcasts device presence periodically on multicast address 239.255.255.250:1900
   - Includes device location URL

2. **M-SEARCH Response (Active)**
   - Listens for discovery requests on port 1900
   - Responds immediately when Plex searches
   - Significantly faster and more reliable discovery

This dual approach ensures maximum compatibility with all Plex clients, now powered by an `aiohttp` based asynchronous server.

### Supported UPnP Actions

**AVTransport Service:**
- `SetAVTransportURI` - Set media URL
- `Play` - Start playback
- `Pause` - Pause playback
- `Stop` - Stop playback
- `GetTransportInfo` - Get playback state

**RenderingControl Service:**
- `SetVolume` - Set volume level (0-100)
- `GetVolume` - Get current volume
- (Mute functionality is planned for future updates)

**ConnectionManager Service:**
- (Basic `GetProtocolInfo` for compatibility)

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

- The Plex token provides full access to your Plex server - keep it secure and never commit it to version control.
- The DLNA bridge listens on 0.0.0.0 (all interfaces) - use firewall rules if on a public network or if running in a non-isolated environment.
- Consider running on a dedicated machine or container for isolation.

## Project Files (New Structure)

- **`main.py`** - The main entry point for the application.
- **`bridge/config.py`** - Configuration loaded via `pydantic-settings` from `.env`.
- **`bridge/core/dlna_server.py`** - Implements the asynchronous DLNA/UPnP HTTP server using `aiohttp`.
- **`bridge/core/models.py`** - Data models for playback state and media information.
- **`bridge/core/speaker_manager.py`** - Manages connections and controls for Samsung speakers via `pywam`.
- **`bridge/core/ssdp.py`** - Handles SSDP announcements and M-SEARCH responses.
- **`diagnose_discovery.py`** - Standalone diagnostic tool to troubleshoot discovery issues.
- **`requirements.txt`** - Python dependencies.
- **`.env.example`** - Template for environment-based configuration.
- **`Dockerfile`** - Docker multi-stage build definition.
- **`docker-compose.yml`** - Docker Compose setup for easy deployment.
- **`tests/`** - Directory containing unit and integration tests.
  - **`tests/test_bridge.py`** - Basic test suite.
- **`README.md`** - This documentation.
- **`QUICKSTART.md`** - 5-minute setup guide (will be updated separately if needed).
- **`DISCOVERY_TROUBLESHOOTING.md`** - Detailed discovery troubleshooting guide.

## Known Limitations

1. **Video Playback:** Only audio is supported (Samsung speakers are audio-only).
2. **Seeking:** Seek/skip functionality depends on `pywam` library support.
3. **Multi-Zone:** Each speaker group needs a separate bridge instance.
4. **Discovery Timing:** May still take some seconds for Plex to discover the device after starting.

## Contributing

Found a bug? Have a feature request? Want to improve the code?

1. Test thoroughly with your setup.
2. Document any changes clearly.
3. Share your improvements!

## License

This project is provided as-is for personal use. Samsung and Plex are trademarks of their respective owners.

## Credits

- **`pywam`** - Samsung Wireless Audio Multiroom Python library
- **`plexapi`** - Python bindings for Plex API
- UPnP/DLNA specifications from upnp.org
- **`aiohttp`** - Asynchronous HTTP client/server framework
- **`pydantic-settings`** - Settings management using Pydantic

## Changelog

### v2.0.0 (Major Refactor & Modernization)
- ✅ **Modular Architecture**: Complete refactor into `bridge/core` modules for `DLNAServer`, `SpeakerManager`, `SSDPResponder`, and `models`.
- ✅ **Asynchronous Server**: Replaced `http.server` with `aiohttp` for a fully asynchronous and non-blocking web server.
- ✅ **Modern Configuration**: Switched to `pydantic-settings` for robust environment variable (`.env`) based configuration.
- ✅ **Improved Speaker Discovery**: Added support for automatic speaker discovery (configurable).
- ✅ **Comprehensive Testing**: Introduced a `tests/` directory with `pytest` for unit and integration testing.
- ✅ **Optimized Docker**: Implemented multi-stage Docker builds for smaller images and added a Docker healthcheck.
- ✅ **Updated Diagnostics**: `diagnose_discovery.py` now uses the new configuration system.
- Removed deprecated `plex_dlna_bridge_full.py`, `config.py`, and `config_template.py`.

### v1.3.0 (Docker Support)
- ✅ **Dockerized**: Added `Dockerfile` and `docker-compose.yml` for easy deployment.
- ✅ **Environment Variables**: Configuration can now be set via Environment Variables for better security.

### v1.2.0 (Architecture & Configuration)
- ✅ **Secure Configuration**: Moved all settings to `config.py` to separate secrets from code.
- ✅ **Robust Async Architecture**: Implemented persistent background event loop to prevent concurrency crashes.
- ✅ **Improved Network Stability**: Added multi-interface IP detection for better connectivity.
- ✅ **Updated Tools**: Connection tester and diagnostic tools now respect `config.py`.
- ✅ **Dependencies**: Added `netifaces` for robust network detection.

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