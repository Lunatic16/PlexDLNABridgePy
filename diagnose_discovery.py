#!/usr/bin/env python3
"""
SSDP Discovery Diagnostic Tool

This script helps diagnose why Plex isn't discovering the DLNA bridge.
It will:
1. Test SSDP multicast sending
2. Listen for SSDP discovery requests
3. Monitor network interfaces
4. Test the description.xml endpoint
"""

import socket
import struct
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import xml.etree.ElementTree as ET

# Configuration
DLNA_SERVER_PORT = 32488
DEVICE_UUID = "3c202906-2b86-4f88-a79c-f6d4e7c8d1a3"
SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900


def get_local_ip():
    """Get the primary local IP address"""
    try:
        # Create a socket to determine the primary network interface
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return socket.gethostbyname(socket.gethostname())


def get_all_ips():
    """Get all local IP addresses"""
    import netifaces
    ips = []
    try:
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    if not ip.startswith('127.'):
                        ips.append(ip)
    except:
        # Fallback if netifaces not available
        ips = [get_local_ip()]
    return ips


def test_multicast_send():
    """Test if we can send SSDP multicast messages"""
    print("\n" + "="*60)
    print("Testing SSDP Multicast Send")
    print("="*60)
    
    local_ip = get_local_ip()
    print(f"Local IP: {local_ip}")
    
    message = (
        "NOTIFY * HTTP/1.1\r\n"
        f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
        "CACHE-CONTROL: max-age=1800\r\n"
        f"LOCATION: http://{local_ip}:{DLNA_SERVER_PORT}/description.xml\r\n"
        "NT: upnp:rootdevice\r\n"
        "NTS: ssdp:alive\r\n"
        "SERVER: Linux/4.0 UPnP/1.1 Samsung-DLNA-Bridge/1.0\r\n"
        f"USN: uuid:{DEVICE_UUID}::upnp:rootdevice\r\n"
        "\r\n"
    )
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        
        # Try binding to specific interface
        try:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(local_ip))
            print(f"✅ Bound to interface: {local_ip}")
        except Exception as e:
            print(f"⚠️  Could not bind to specific interface: {e}")
        
        sock.sendto(message.encode('utf-8'), (SSDP_ADDR, SSDP_PORT))
        print(f"✅ Sent SSDP NOTIFY to {SSDP_ADDR}:{SSDP_PORT}")
        print(f"   Location: http://{local_ip}:{DLNA_SERVER_PORT}/description.xml")
        
        sock.close()
        return True
    except Exception as e:
        print(f"❌ Failed to send SSDP multicast: {e}")
        return False


def listen_for_msearch(duration=30):
    """Listen for M-SEARCH discovery requests"""
    print("\n" + "="*60)
    print(f"Listening for SSDP M-SEARCH requests ({duration}s)")
    print("="*60)
    print("Waiting for Plex or other devices to search for DLNA devices...")
    print("(Open Plex and try to cast something now)")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Join multicast group
    try:
        sock.bind(('', SSDP_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(SSDP_ADDR), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print("✅ Joined multicast group")
    except Exception as e:
        print(f"❌ Failed to join multicast group: {e}")
        print("   This is often caused by firewall blocking multicast")
        return False
    
    sock.settimeout(1)
    
    start_time = time.time()
    request_count = 0
    
    while time.time() - start_time < duration:
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8', errors='ignore')
            
            if 'M-SEARCH' in message:
                request_count += 1
                print(f"\n📡 M-SEARCH received from {addr[0]}:{addr[1]}")
                
                # Parse the search target
                for line in message.split('\r\n'):
                    if line.startswith('ST:'):
                        search_target = line.split(':', 1)[1].strip()
                        print(f"   Search Target: {search_target}")
                    elif line.startswith('MAN:'):
                        print(f"   {line}")
                
                # Should we respond to this?
                should_respond = any(st in message for st in [
                    'ssdp:all',
                    'upnp:rootdevice', 
                    'MediaRenderer',
                    'urn:schemas-upnp-org:device:MediaRenderer:1'
                ])
                
                if should_respond:
                    print("   ✅ This is a relevant search - we should respond")
                    # Send response
                    respond_to_msearch(sock, addr, message)
                else:
                    print("   ⚠️  Not a MediaRenderer search")
                    
        except socket.timeout:
            continue
        except Exception as e:
            print(f"❌ Error receiving: {e}")
    
    sock.close()
    
    print(f"\n{'='*60}")
    print(f"Received {request_count} M-SEARCH requests in {duration}s")
    
    if request_count == 0:
        print("\n⚠️  WARNING: No M-SEARCH requests detected!")
        print("   Possible issues:")
        print("   1. Plex is not searching for devices")
        print("   2. Firewall blocking multicast (port 1900 UDP)")
        print("   3. Not on same network as Plex")
        print("   4. Router blocking multicast traffic")
        return False
    else:
        print("✅ Successfully receiving discovery requests")
        return True


def respond_to_msearch(sock, addr, request):
    """Respond to an M-SEARCH request"""
    local_ip = get_local_ip()
    
    response = (
        "HTTP/1.1 200 OK\r\n"
        "CACHE-CONTROL: max-age=1800\r\n"
        "EXT:\r\n"
        f"LOCATION: http://{local_ip}:{DLNA_SERVER_PORT}/description.xml\r\n"
        "SERVER: Linux/4.0 UPnP/1.1 Samsung-DLNA-Bridge/1.0\r\n"
        "ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n"
        f"USN: uuid:{DEVICE_UUID}::urn:schemas-upnp-org:device:MediaRenderer:1\r\n"
        "\r\n"
    )
    
    try:
        sock.sendto(response.encode('utf-8'), addr)
        print(f"   📤 Sent response to {addr[0]}:{addr[1]}")
    except Exception as e:
        print(f"   ❌ Failed to send response: {e}")


def test_description_xml():
    """Test if description.xml is accessible"""
    print("\n" + "="*60)
    print("Testing Description XML Endpoint")
    print("="*60)
    
    local_ip = get_local_ip()
    url = f"http://{local_ip}:{DLNA_SERVER_PORT}/description.xml"
    
    print(f"Testing: {url}")
    
    try:
        # Start a simple HTTP server
        class SimpleHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/description.xml':
                    xml = f'''<?xml version="1.0" encoding="utf-8"?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
  <specVersion>
    <major>1</major>
    <minor>0</minor>
  </specVersion>
  <device>
    <deviceType>urn:schemas-upnp-org:device:MediaRenderer:1</deviceType>
    <friendlyName>Samsung Speaker Group</friendlyName>
    <manufacturer>Samsung</manufacturer>
    <modelName>Samsung R1 Group</modelName>
    <UDN>uuid:{DEVICE_UUID}</UDN>
  </device>
</root>'''
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/xml')
                    self.end_headers()
                    self.wfile.write(xml.encode('utf-8'))
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                pass  # Suppress logs
        
        # Start server in background
        server = HTTPServer(('0.0.0.0', DLNA_SERVER_PORT), SimpleHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        time.sleep(0.5)
        
        # Test the endpoint
        response = urllib.request.urlopen(url, timeout=5)
        content = response.read().decode('utf-8')
        
        # Parse XML
        root = ET.fromstring(content)
        
        print("✅ Description XML is accessible")
        print(f"   Status: {response.status}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        
        # Check XML structure
        if 'MediaRenderer' in content:
            print("   ✅ Contains MediaRenderer device type")
        else:
            print("   ❌ Missing MediaRenderer device type")
        
        if DEVICE_UUID in content:
            print(f"   ✅ Contains device UUID: {DEVICE_UUID}")
        else:
            print("   ❌ Missing device UUID")
        
        server.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ Failed to access description.xml: {e}")
        print("\n   Possible issues:")
        print(f"   1. Port {DLNA_SERVER_PORT} is blocked by firewall")
        print(f"   2. Another service is using port {DLNA_SERVER_PORT}")
        print("   3. Bridge server is not running")
        return False


def test_network_interfaces():
    """Test network interface configuration"""
    print("\n" + "="*60)
    print("Network Interface Information")
    print("="*60)
    
    try:
        import netifaces
        
        for interface in netifaces.interfaces():
            print(f"\nInterface: {interface}")
            addrs = netifaces.ifaddresses(interface)
            
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    print(f"  IPv4: {addr['addr']}")
                    
                    # Check if multicast-capable
                    if not addr['addr'].startswith('127.'):
                        print(f"    ✅ Can be used for DLNA")
    except ImportError:
        print("⚠️  netifaces not installed, using basic detection")
        print(f"Primary IP: {get_local_ip()}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_firewall():
    """Test firewall rules"""
    print("\n" + "="*60)
    print("Firewall Check")
    print("="*60)
    
    import platform
    system = platform.system()
    
    print(f"Operating System: {system}")
    print(f"\nRequired open ports:")
    print(f"  - {DLNA_SERVER_PORT}/TCP (DLNA HTTP server)")
    print(f"  - 1900/UDP (SSDP discovery)")
    
    if system == "Linux":
        print("\nTo check/open ports on Linux:")
        print(f"  sudo ufw status")
        print(f"  sudo ufw allow {DLNA_SERVER_PORT}/tcp")
        print(f"  sudo ufw allow 1900/udp")
    elif system == "Windows":
        print("\nTo check firewall on Windows:")
        print("  Control Panel → Windows Defender Firewall → Advanced Settings")
        print("  → Inbound Rules → New Rule → Port")
    elif system == "Darwin":
        print("\nTo check firewall on macOS:")
        print("  System Preferences → Security & Privacy → Firewall")
        print("  → Firewall Options → Add Python to allowed apps")


def main():
    """Run all diagnostics"""
    print("\n" + "="*60)
    print("  PLEX DLNA BRIDGE - DISCOVERY DIAGNOSTICS")
    print("="*60)
    print("\nThis tool will help diagnose why Plex isn't discovering the bridge.")
    print("Make sure the bridge is NOT running before starting these tests.")
    
    input("\nPress Enter to start diagnostics...")
    
    # Run tests
    test_network_interfaces()
    test_firewall()
    
    multicast_ok = test_multicast_send()
    
    xml_ok = test_description_xml()
    
    print("\n" + "="*60)
    print("Starting M-SEARCH Listener")
    print("="*60)
    print("\n🔍 Now open Plex and try to cast to a device.")
    print("   Click the cast icon in the Plex player.")
    print("   This tool will detect if Plex is searching for devices.\n")
    
    input("Press Enter when ready to start listening...")
    
    msearch_ok = listen_for_msearch(30)
    
    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    tests = [
        ("Multicast Send", multicast_ok),
        ("Description XML", xml_ok),
        ("M-SEARCH Detection", msearch_ok),
    ]
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)
    
    if not multicast_ok:
        print("\n⚠️  MULTICAST ISSUE DETECTED")
        print("Fix: Check firewall settings and router multicast support")
    
    if not xml_ok:
        print(f"\n⚠️  HTTP SERVER ISSUE DETECTED")
        print(f"Fix: Ensure port {DLNA_SERVER_PORT} is open and not in use")
    
    if not msearch_ok:
        print("\n⚠️  NOT RECEIVING DISCOVERY REQUESTS")
        print("Possible causes:")
        print("1. Plex and bridge not on same network")
        print("2. Firewall blocking UDP port 1900")
        print("3. Router blocking multicast (IGMP snooping disabled)")
        print("4. Plex not actively searching (try casting something)")
    
    if multicast_ok and xml_ok and msearch_ok:
        print("\n✅ All tests passed!")
        print("The discovery mechanism should be working.")
        print("\nIf Plex still doesn't see the device:")
        print("1. Restart Plex Media Server")
        print("2. Clear Plex cache")
        print("3. Try a different Plex client (web/mobile/desktop)")
        print("4. Check Plex server logs for DLNA errors")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnostics interrupted by user")
        sys.exit(0)
