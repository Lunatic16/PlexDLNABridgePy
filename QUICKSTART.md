# Quick Start Guide - Plex DLNA Bridge

## 🚀 Get Up and Running in 5 Minutes

### Step 1: Install Dependencies (1 minute)

```bash
pip install pywam plexapi requests
```

### Step 2: Find Your Speaker IPs (2 minutes)

**Option A - Use Samsung App:**
1. Open Samsung Multiroom app on your phone
2. Tap Settings (gear icon)
3. Select your speaker
4. Go to "Speaker Settings"
5. View "Network Info"
6. Write down the IP address
7. Repeat for each speaker

**Option B - Check Your Router:**
1. Log into your router admin panel (usually 192.168.1.1 or 192.168.0.1)
2. Look for "Connected Devices" or "DHCP Clients"
3. Find devices named "Samsung" or your speaker model
4. Write down their IP addresses

### Step 3: Get Your Plex Token (1 minute)

1. Go to https://app.plex.tv in your browser
2. Click on any song/album to start playing
3. Click the three dots (•••) icon
4. Select "Get Info"
5. Click "View XML"
6. In the URL bar, find `X-Plex-Token=XXXXXXXX`
7. Copy everything after the equals sign until the next `&`

Example:
```
https://app.plex.tv/...?X-Plex-Token=abc123xyz789&...
                                      ^^^^^^^^^^^^
                                      Copy this part
```

### Step 4: Configure the Bridge (1 minute)

Edit `plex_dlna_bridge_full.py`:

```python
# Find this section near the top:
PLEX_URL = 'http://192.168.1.100:32400'     # ← Change to your Plex IP
PLEX_TOKEN = 'your_plex_token_here'         # ← Paste your token here
DLNA_DEVICE_NAME = "Samsung Speaker Group"  # ← Optional: customize name

SPEAKER_IPS = [
    '192.168.1.101',  # ← Change to your speaker IPs
    '192.168.1.102',  # ← Add/remove lines as needed
]
```

**Save the file!**

### Step 5: Run It! (30 seconds)

```bash
python plex_dlna_bridge_full.py
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
INFO - Connected to Plex: My Plex Server
============================================================
✓ Samsung speaker group 'Living Room R1 Group' is now discoverable
✓ Appearing to Plex as 'Samsung Speaker Group'
✓ DLNA server running on port 32488
✓ Ready for playback commands from Plex
============================================================
```

### Step 6: Play Music!

1. Open Plex (web, phone, or desktop app)
2. Start playing any song
3. Click the **Cast icon** (📡) in the player
4. Select **"Samsung Speaker Group"**
5. 🎵 Enjoy your music!

---

## ⚠️ Troubleshooting Quick Fixes

### "Failed to connect to speaker"
- ✅ Check speaker is powered on
- ✅ Check IP address is correct: `ping 192.168.1.101`
- ✅ Restart the speaker

### "Failed to connect to Plex"
- ✅ Check Plex server IP is correct
- ✅ Check Plex token is correct (no extra spaces)
- ✅ Make sure Plex is running

### "Device not showing in Plex"
- ✅ Wait 30-60 seconds (discovery takes time)
- ✅ Restart Plex app/web page
- ✅ Check firewall isn't blocking port 32488

### Still having issues?
See the full README.md for detailed troubleshooting.

---

## 🎯 Pro Tips

1. **Static IPs**: In your router, assign static IPs to your speakers so they don't change
2. **Auto-start**: Set up the bridge to run automatically (see README.md)
3. **Volume Control**: Use Plex's volume slider to control all speakers at once
4. **Keep It Running**: The bridge needs to stay running to control speakers

---

## 📋 Command Cheat Sheet

```bash
# Install dependencies
pip install pywam plexapi requests

# Run the bridge
python plex_dlna_bridge_full.py

# Stop the bridge
Press Ctrl+C

# Find speaker IPs (Linux/Mac)
sudo nmap -sn 192.168.1.0/24 | grep -B 2 "Samsung"

# Test if speaker is reachable
ping 192.168.1.101

# Check if port is open
netstat -an | grep 32488
```

---

## ✅ Success Checklist

- [ ] Python 3.7+ installed
- [ ] Dependencies installed (pywam, plexapi, requests)
- [ ] Samsung speaker IPs found
- [ ] Plex token obtained
- [ ] Configuration updated in script
- [ ] Script runs without errors
- [ ] Speakers show "Connected" in logs
- [ ] Plex connection successful
- [ ] Device appears in Plex cast menu
- [ ] Music plays through speakers

---

## 🆘 Need More Help?

1. **Read the full README.md** - Has detailed troubleshooting
2. **Check the logs** - Script prints detailed info about what's happening
3. **Enable debug logging** - Change `logging.INFO` to `logging.DEBUG` in the script
4. **Test individual components** - Use the test script (test_connection.py)

---

## 🎉 You're All Set!

The bridge is now running and your Samsung speakers are connected to Plex!

Remember:
- Keep the script running (terminal window open or run as service)
- Speakers and Plex server must be on same network
- Bridge computer must stay on and connected to network

**Enjoy your Samsung speakers with Plex! 🎵**
