# PlexDLNABridgePy - Project Overview

This project is a Python-based DLNA/UPnP bridge designed to make Samsung Multiroom speakers (WAM series) discoverable and controllable by Plex Media Server.

## 🏗 Architecture
- **Plex Integration:** Uses `plexapi` to connect to the Plex server.
- **Samsung Control:** Uses `pywam` for asynchronous control of Samsung speakers.
- **DLNA/UPnP:** Implements a custom SSDP/SOAP stack to mimic a DLNA Media Renderer.
- **Discovery:** Employs both passive SSDP NOTIFY and active M-SEARCH responding.

## 📁 Key Files
- `plex_dlna_bridge_full.py`: The main application logic.
- `diagnose_discovery.py`: Troubleshooting tool for SSDP/discovery issues.
- `test_connection.py`: Connectivity validator for Plex and Samsung speakers.
- `DISCOVERY_TROUBLESHOOTING.md`: Detailed network troubleshooting guide.

## 🚀 Development Quick Start
1. **Dependencies:** `pip install pywam plexapi requests`
2. **Configuration:** Update `PLEX_URL`, `PLEX_TOKEN`, and `SPEAKER_IPS` in the main script.
3. **Running:** `sudo python plex_dlna_bridge_full.py` (sudo required for SSDP port 1900).

## 🛠 Tech Stack
- **Language:** Python 3.7+
- **Protocols:** DLNA, UPnP, SSDP, SOAP, HTTP
- **Libraries:** `asyncio`, `pywam`, `plexapi`, `requests`

## 📝 Maintenance Notes
- **Port 1900 (UDP):** Crucial for SSDP discovery. Must be open in firewall.
- **Port 32488 (TCP):** Default port for the DLNA SOAP interface.
- **SSDP TTL:** Set to 4 to allow cross-subnet/switch traversal if necessary.
