#!/usr/bin/env python3
"""
Verify Discovery via Plex API

This script uses the plexapi library to ask the Plex Server what devices it sees.
Run this script WHILE the bridge is running.
"""
import sys
import time
from plexapi.server import PlexServer
from bridge.config import settings

def main():
    print("\n" + "="*60)
    print("  PLEX API DISCOVERY VERIFICATION")
    print("="*60)
    print(f"Connecting to Plex at {settings.plex_url}...")
    
    try:
        plex = PlexServer(settings.plex_url, settings.plex_token)
    except Exception as e:
        print(f"❌ Failed to connect to Plex: {e}")
        print("   Check PLEX_URL and PLEX_TOKEN in your .env file.")
        sys.exit(1)

    print(f"✅ Connected to Plex Server: {plex.friendlyName}")
    print("\nQuerying active clients (cast targets)...")
    print("Note: This checks if Plex has discovered the bridge via SSDP.")
    
    clients = plex.clients()
    
    found = False
    print(f"\nFound {len(clients)} clients:")
    for client in clients:
        print(f"  - {client.title} ({client.product}) at {client.address}")
        if client.title == settings.dlna_device_name:
            found = True
            print(f"    ✨ FOUND YOUR BRIDGE!")

    print("-" * 60)
    if found:
        print(f"✅ SUCCESS: Plex sees '{settings.dlna_device_name}'!")
        print("You can now try to cast music to it from any Plex client.")
    else:
        print(f"❌ FAILURE: Plex does not see '{settings.dlna_device_name}'.")
        print("   1. Ensure the bridge is RUNNING (python main.py)")
        print("   2. Ensure Firewall allows UDP 1900 and TCP 32488")
        print("   3. Run 'python diagnose_discovery.py' for network tests")

if __name__ == "__main__":
    main()