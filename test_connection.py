#!/usr/bin/env python3
"""
Test Connection Script for Plex DLNA Bridge

This script tests your configuration before running the full bridge.
It will check:
1. Samsung speaker connectivity
2. Plex server connectivity
3. Network port availability
4. Configuration validity

Usage:
    python test_connection.py
"""

import socket
import asyncio
import sys
from plexapi.server import PlexServer

# Import configuration from config.py
try:
    from config import (
        PLEX_URL, PLEX_TOKEN, SPEAKER_IPS, 
        DLNA_SERVER_PORT, DLNA_DEVICE_NAME
    )
except ImportError:
    print("❌ Error: Could not import configuration from config.py")
    print("   Make sure the file exists in the same directory.")
    print("   If missing, copy config_template.py to config.py and configure it.")
    sys.exit(1)

# Try to import pywam
try:
    from pywam.speaker import Speaker
    PYWAM_AVAILABLE = True
except ImportError:
    PYWAM_AVAILABLE = False
    print("⚠️  Warning: pywam library not installed")
    print("   Install with: pip install pywam")


def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_result(test_name, passed, message=""):
    """Print a test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if message:
        print(f"        {message}")


def test_configuration():
    """Test basic configuration validity"""
    print_header("Testing Configuration")
    
    all_passed = True
    
    # Test Plex URL
    if PLEX_URL and PLEX_URL.startswith('http'):
        print_result("Plex URL format", True, PLEX_URL)
    else:
        print_result("Plex URL format", False, "URL should start with http://")
        all_passed = False
    
    # Test Plex Token
    if PLEX_TOKEN and PLEX_TOKEN != 'your_plex_token_here' and len(PLEX_TOKEN) > 10:
        print_result("Plex Token set", True, f"Length: {len(PLEX_TOKEN)} characters")
    else:
        print_result("Plex Token set", False, "Token not configured or too short")
        all_passed = False
    
    # Test Speaker IPs
    if SPEAKER_IPS and len(SPEAKER_IPS) > 0:
        print_result("Speaker IPs configured", True, f"{len(SPEAKER_IPS)} speaker(s)")
        for ip in SPEAKER_IPS:
            if not ip.replace('.', '').replace('192', '').replace('168', '').replace('0', '').replace('1', '').isdigit():
                print_result(f"  Speaker IP format: {ip}", False, "Invalid IP format")
                all_passed = False
    else:
        print_result("Speaker IPs configured", False, "No speaker IPs set")
        all_passed = False
    
    # Test DLNA Device Name
    if DLNA_DEVICE_NAME and DLNA_DEVICE_NAME != "":
        print_result("Device name set", True, DLNA_DEVICE_NAME)
    else:
        print_result("Device name set", False, "No device name configured")
        all_passed = False
    
    return all_passed


def test_network_connectivity():
    """Test basic network connectivity"""
    print_header("Testing Network Connectivity")
    
    all_passed = True
    
    # Test speaker reachability
    for ip in SPEAKER_IPS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, 55001))  # Samsung speakers typically use port 55001
            sock.close()
            
            if result == 0:
                print_result(f"Speaker reachable: {ip}", True)
            else:
                # Try ping as fallback
                import subprocess
                import platform
                
                param = '-n' if platform.system().lower() == 'windows' else '-c'
                command = ['ping', param, '1', ip]
                response = subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if response == 0:
                    print_result(f"Speaker reachable: {ip}", True, "Ping successful")
                else:
                    print_result(f"Speaker reachable: {ip}", False, "Cannot reach speaker")
                    all_passed = False
        except Exception as e:
            print_result(f"Speaker reachable: {ip}", False, str(e))
            all_passed = False
    
    # Test Plex server reachability
    try:
        plex_ip = PLEX_URL.replace('http://', '').replace('https://', '').split(':')[0]
        plex_port = int(PLEX_URL.split(':')[-1].rstrip('/'))
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((plex_ip, plex_port))
        sock.close()
        
        if result == 0:
            print_result("Plex server reachable", True, f"{plex_ip}:{plex_port}")
        else:
            print_result("Plex server reachable", False, f"Cannot connect to {plex_ip}:{plex_port}")
            all_passed = False
    except Exception as e:
        print_result("Plex server reachable", False, str(e))
        all_passed = False
    
    return all_passed


def test_port_availability():
    """Test if DLNA port is available"""
    print_header("Testing Port Availability")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', DLNA_SERVER_PORT))
        sock.close()
        
        if result != 0:
            print_result(f"Port {DLNA_SERVER_PORT} available", True)
            return True
        else:
            print_result(f"Port {DLNA_SERVER_PORT} available", False, 
                        "Port is already in use. Change DLNA_SERVER_PORT or stop the other service.")
            return False
    except Exception as e:
        print_result(f"Port {DLNA_SERVER_PORT} check", False, str(e))
        return False


def test_plex_connection():
    """Test Plex server connection"""
    print_header("Testing Plex Connection")
    
    try:
        plex = PlexServer(PLEX_URL, PLEX_TOKEN)
        print_result("Plex authentication", True)
        print(f"        Server: {plex.friendlyName}")
        print(f"        Version: {plex.version}")
        print(f"        Platform: {plex.platform}")
        
        # Test library access
        try:
            libraries = plex.library.sections()
            print_result("Library access", True, f"{len(libraries)} libraries found")
            for lib in libraries:
                print(f"          - {lib.title} ({lib.type})")
        except Exception as e:
            print_result("Library access", False, str(e))
            return False
        
        return True
    except Exception as e:
        print_result("Plex authentication", False, str(e))
        print("\n        Common issues:")
        print("        - Check PLEX_TOKEN is correct")
        print("        - Verify PLEX_URL is correct")
        print("        - Ensure Plex server is running")
        print("        - Check network connectivity")
        return False


async def test_speaker_connection():
    """Test Samsung speaker connection"""
    print_header("Testing Samsung Speaker Connection")
    
    if not PYWAM_AVAILABLE:
        print_result("pywam library", False, "Not installed. Run: pip install pywam")
        return False
    
    all_passed = True
    connected_speakers = []
    
    for ip in SPEAKER_IPS:
        try:
            print(f"\nConnecting to speaker at {ip}...")
            speaker = Speaker(ip)
            await speaker.connect()
            
            # Get speaker info
            try:
                name = await speaker.get_name()
                volume = await speaker.get_volume()
                
                print_result(f"Speaker {ip}", True)
                print(f"        Name: {name}")
                print(f"        Volume: {volume}")
                
                connected_speakers.append(speaker)
            except Exception as e:
                print_result(f"Speaker {ip}", True, f"Connected but info unavailable: {e}")
                connected_speakers.append(speaker)
            
        except Exception as e:
            print_result(f"Speaker {ip}", False, str(e))
            all_passed = False
    
    # Clean up connections
    for speaker in connected_speakers:
        try:
            await speaker.disconnect()
        except:
            pass
    
    if connected_speakers:
        print(f"\n✅ Successfully connected to {len(connected_speakers)}/{len(SPEAKER_IPS)} speakers")
    
    return all_passed


def test_dependencies():
    """Test if all required dependencies are installed"""
    print_header("Testing Dependencies")
    
    all_passed = True
    
    dependencies = [
        ('pywam', 'Samsung speaker control'),
        ('plexapi', 'Plex API'),
        ('requests', 'HTTP requests'),
    ]
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print_result(f"{module_name}", True, description)
        except ImportError:
            print_result(f"{module_name}", False, f"{description} - Install with: pip install {module_name}")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  PLEX DLNA BRIDGE - CONNECTION TEST")
    print("="*60)
    print("\nThis script will test your configuration and connections.")
    print("Running tests...\n")
    
    results = []
    
    # Run tests
    results.append(("Dependencies", test_dependencies()))
    results.append(("Configuration", test_configuration()))
    results.append(("Port Availability", test_port_availability()))
    results.append(("Network Connectivity", test_network_connectivity()))
    results.append(("Plex Connection", test_plex_connection()))
    
    # Run async speaker test
    if PYWAM_AVAILABLE:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            speaker_result = loop.run_until_complete(test_speaker_connection())
            results.append(("Speaker Connection", speaker_result))
        finally:
            loop.close()
    else:
        results.append(("Speaker Connection", False))
    
    # Print summary
    print_header("Test Summary")
    
    all_passed = all(result for _, result in results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)
    
    if all_passed:
        print("🎉 All tests passed! You're ready to run the bridge.")
        print("\nNext step:")
        print("    python plex_dlna_bridge_full.py")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  1. Install missing dependencies: pip install pywam plexapi requests")
        print("  2. Check your configuration in config.py")
        print("  3. Verify speaker IPs are correct")
        print("  4. Verify Plex token is correct")
        print("  5. Ensure speakers and Plex are on same network")
        return 1


if __name__ == "__main__":
    sys.exit(main())
