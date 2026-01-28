import time
import threading
import socket
from xml.etree import ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import requests
from pywam.speaker import Speaker
from plexapi.server import PlexServer
import uuid
import logging
import asyncio
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

# Import configuration
try:
    import config
except ImportError:
    # Fallback or create default config if missing (though we just created it)
    import sys
    print("Error: config.py not found. Please copy config_template.py to config.py and configure it.")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, logging.INFO), 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global Background Loop
EVENT_LOOP = None
LOOP_THREAD = None

def start_background_loop(loop):
    """Run the asyncio event loop in a background thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()

class PlaybackState(Enum):
    """Playback state enumeration"""
    STOPPED = "STOPPED"
    PLAYING = "PLAYING"
    PAUSED_PLAYBACK = "PAUSED_PLAYBACK"
    TRANSITIONING = "TRANSITIONING"
    NO_MEDIA_PRESENT = "NO_MEDIA_PRESENT"


@dataclass
class MediaState:
    """Current media playback state"""
    transport_state: PlaybackState = PlaybackState.NO_MEDIA_PRESENT
    transport_status: str = "OK"
    current_track_uri: str = ""
    current_track_metadata: str = ""
    current_track_duration: str = "0:00:00"
    current_track: int = 1
    number_of_tracks: int = 1
    playback_position: str = "0:00:00"
    volume: int = 50
    mute: bool = False


class DLNADeviceHandler(BaseHTTPRequestHandler):
    """HTTP handler for DLNA device requests"""
    
    def __init__(self, speaker_group, media_state, *args, **kwargs):
        self.speaker_group = speaker_group
        self.media_state = media_state
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.debug(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        """Handle GET requests for DLNA device description"""
        if self.path == '/description.xml':
            self.send_response(200)
            self.send_header('Content-Type', 'text/xml; charset="utf-8"')
            self.end_headers()
            
            # Send DLNA device description XML
            device_xml = self.generate_device_description()
            self.wfile.write(device_xml.encode('utf-8'))
        
        elif self.path.startswith('/upnp/service/') and self.path.endswith('/scpd.xml'):
            # Service description requests
            service_type = self.path.split('/')[3]
            self.send_service_description(service_type)
        
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>DLNA Samsung Speaker Bridge</h1><p>Device is running</p></body></html>')
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests for UPnP actions"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        if self.path.startswith('/upnp/control/'):
            self.handle_upnp_action(post_data)
        else:
            self.send_response(404)
            self.end_headers()
    
    def generate_device_description(self):
        """Generate the DLNA/UPnP device description XML"""
        local_ip = self.get_local_ip()
        xml_desc = f'''<?xml version="1.0" encoding="utf-8"?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
  <specVersion>
    <major>1</major>
    <minor>0</minor>
  </specVersion>
  <device>
    <deviceType>urn:schemas-upnp-org:device:MediaRenderer:1</deviceType>
    <friendlyName>{config.DLNA_DEVICE_NAME}</friendlyName>
    <manufacturer>Samsung</manufacturer>
    <manufacturerURL>http://www.samsung.com</manufacturerURL>
    <modelDescription>Samsung Multiroom Speaker Group</modelDescription>
    <modelName>Samsung R1 Group</modelName>
    <modelNumber>1.0</modelNumber>
    <UDN>uuid:{config.DEVICE_UUID}</UDN>
    <serviceList>
      <service>
        <serviceType>urn:schemas-upnp-org:service:AVTransport:1</serviceType>
        <serviceId>urn:upnp-org:serviceId:AVTransport</serviceId>
        <SCPDURL>/upnp/service/AVTransport/scpd.xml</SCPDURL>
        <controlURL>/upnp/control/AVTransport1</controlURL>
        <eventSubURL>/upnp/event/AVTransport1</eventSubURL>
      </service>
      <service>
        <serviceType>urn:schemas-upnp-org:service:ConnectionManager:1</serviceType>
        <serviceId>urn:upnp-org:serviceId:ConnectionManager</serviceId>
        <SCPDURL>/upnp/service/ConnectionManager/scpd.xml</SCPDURL>
        <controlURL>/upnp/control/ConnectionManager1</controlURL>
        <eventSubURL>/upnp/event/ConnectionManager1</eventSubURL>
      </service>
      <service>
        <serviceType>urn:schemas-upnp-org:service:RenderingControl:1</serviceType>
        <serviceId>urn:upnp-org:serviceId:RenderingControl</serviceId>
        <SCPDURL>/upnp/service/RenderingControl/scpd.xml</SCPDURL>
        <controlURL>/upnp/control/RenderingControl1</controlURL>
        <eventSubURL>/upnp/event/RenderingControl1</eventSubURL>
      </service>
    </serviceList>
    <presentationURL>http://{local_ip}:{config.DLNA_SERVER_PORT}/</presentationURL>
  </device>
</root>'''
        return xml_desc
    
    def send_service_description(self, service_type):
        """Send service description SCPD XML"""
        # Simplified service descriptions - in production, these would be more detailed
        scpd = f'''<?xml version="1.0" encoding="utf-8"?>
<scpd xmlns="urn:schemas-upnp-org:service-1-0">
  <specVersion>
    <major>1</major>
    <minor>0</minor>
  </specVersion>
  <actionList>
    <action>
      <name>GetTransportInfo</name>
    </action>
    <action>
      <name>SetAVTransportURI</name>
    </action>
    <action>
      <name>Play</name>
    </action>
    <action>
      <name>Pause</name>
    </action>
    <action>
      <name>Stop</name>
    </action>
  </actionList>
</scpd>'''
        self.send_response(200)
        self.send_header('Content-Type', 'text/xml; charset="utf-8"')
        self.end_headers()
        self.wfile.write(scpd.encode('utf-8'))
    
    def handle_upnp_action(self, post_data):
        """Handle UPnP action requests"""
        try:
            # Parse the SOAP action
            soap_action = self.headers.get('SOAPACTION', '').strip('"')
            logger.info(f"Received SOAP action: {soap_action}")
            logger.debug(f"POST data: {post_data.decode('utf-8', errors='ignore')}")
            
            # Parse XML
            root = ET.fromstring(post_data)
            
            # Extract action name from SOAP action or XML body
            action_name = None
            if '#' in soap_action:
                action_name = soap_action.split('#')[1]
            else:
                # Try to find action in XML body
                for elem in root.iter():
                    if elem.tag.endswith('Body'):
                        for child in elem:
                            action_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                            break
            
            if not action_name:
                logger.warning("Could not determine action name")
                self.send_soap_error(401, "Invalid Action")
                return
            
            # Handle different actions
            response = None
            if action_name == 'SetAVTransportURI':
                response = self.action_set_av_transport_uri(root)
            elif action_name == 'Play':
                response = self.action_play(root)
            elif action_name == 'Pause':
                response = self.action_pause(root)
            elif action_name == 'Stop':
                response = self.action_stop(root)
            elif action_name == 'GetTransportInfo':
                response = self.action_get_transport_info()
            elif action_name == 'GetPositionInfo':
                response = self.action_get_position_info()
            elif action_name == 'SetVolume':
                response = self.action_set_volume(root)
            elif action_name == 'GetVolume':
                response = self.action_get_volume()
            elif action_name == 'SetMute':
                response = self.action_set_mute(root)
            elif action_name == 'GetMute':
                response = self.action_get_mute()
            elif action_name == 'GetProtocolInfo':
                response = self.action_get_protocol_info()
            else:
                logger.warning(f"Unhandled action: {action_name}")
                response = self.generate_generic_response(action_name)
            
            # Send response
            self.send_soap_response(response)
            
        except Exception as e:
            logger.error(f"Error handling UPnP action: {e}", exc_info=True)
            self.send_soap_error(500, str(e))
    
    def action_set_av_transport_uri(self, root):
        """Handle SetAVTransportURI action"""
        # Extract URI from SOAP body
        uri = None
        metadata = ""
        
        for elem in root.iter():
            if elem.tag.endswith('CurrentURI'):
                uri = elem.text
            elif elem.tag.endswith('CurrentURIMetaData'):
                metadata = elem.text or ""
        
        if uri:
            logger.info(f"Setting transport URI: {uri}")
            self.media_state.current_track_uri = uri
            self.media_state.current_track_metadata = metadata
            self.media_state.transport_state = PlaybackState.STOPPED
            
            # Prepare media for playback
            threading.Thread(target=self.prepare_media, args=(uri,), daemon=True).start()
        
        return '''<u:SetAVTransportURIResponse xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
</u:SetAVTransportURIResponse>'''
    
    def prepare_media(self, uri):
        """Prepare media for playback (runs in separate thread)"""
        try:
            # Get direct media URL from Plex if needed
            if 'plex' in uri.lower() or config.PLEX_URL.replace('http://', '') in uri:
                # This is a Plex URL, ensure it has the token
                if 'X-Plex-Token' not in uri:
                    separator = '&' if '?' in uri else '?'
                    uri = f"{uri}{separator}X-Plex-Token={config.PLEX_TOKEN}"
                
                self.media_state.current_track_uri = uri
                logger.info(f"Prepared Plex media URL: {uri}")
        except Exception as e:
            logger.error(f"Error preparing media: {e}")
    
    def action_play(self, root):
        """Handle Play action"""
        logger.info("Play command received")
        
        if self.media_state.current_track_uri:
            self.media_state.transport_state = PlaybackState.TRANSITIONING
            
            # Start playback in separate thread (which dispatches to async loop)
            threading.Thread(target=self.start_playback, daemon=True).start()
            
            return '''<u:PlayResponse xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
</u:PlayResponse>'''
        else:
            logger.warning("Play requested but no media URI set")
            return '''<u:PlayResponse xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
</u:PlayResponse>'''
    
    def start_playback(self):
        """Start playback on Samsung speakers"""
        try:
            uri = self.media_state.current_track_uri
            logger.info(f"Starting playback of: {uri}")
            
            # Use the persistent background loop
            future = asyncio.run_coroutine_threadsafe(
                self.speaker_group.play_url(uri), 
                self.speaker_group.loop
            )
            
            # Wait for result with timeout
            try:
                future.result(timeout=10)
                self.media_state.transport_state = PlaybackState.PLAYING
                logger.info("Playback started successfully")
            except Exception as e:
                logger.error(f"Playback start failed or timed out: {e}")
                self.media_state.transport_state = PlaybackState.STOPPED

        except Exception as e:
            logger.error(f"Error starting playback: {e}", exc_info=True)
            self.media_state.transport_state = PlaybackState.STOPPED
    
    def action_pause(self, root):
        """Handle Pause action"""
        logger.info("Pause command received")
        self.media_state.transport_state = PlaybackState.PAUSED_PLAYBACK
        
        # Pause playback
        threading.Thread(target=self.pause_playback, daemon=True).start()
        
        return '''<u:PauseResponse xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
</u:PauseResponse>'''
    
    def pause_playback(self):
        """Pause playback on Samsung speakers"""
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.speaker_group.pause(), 
                self.speaker_group.loop
            )
            future.result(timeout=5)
        except Exception as e:
            logger.error(f"Error pausing playback: {e}")
    
    def action_stop(self, root):
        """Handle Stop action"""
        logger.info("Stop command received")
        self.media_state.transport_state = PlaybackState.STOPPED
        self.media_state.playback_position = "0:00:00"
        
        # Stop playback
        threading.Thread(target=self.stop_playback, daemon=True).start()
        
        return '''<u:StopResponse xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
</u:StopResponse>'''
    
    def stop_playback(self):
        """Stop playback on Samsung speakers"""
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.speaker_group.stop(), 
                self.speaker_group.loop
            )
            future.result(timeout=5)
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
    
    def action_get_transport_info(self):
        """Handle GetTransportInfo action"""
        return f'''<u:GetTransportInfoResponse xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
  <CurrentTransportState>{self.media_state.transport_state.value}</CurrentTransportState>
  <CurrentTransportStatus>{self.media_state.transport_status}</CurrentTransportStatus>
  <CurrentSpeed>1</CurrentSpeed>
</u:GetTransportInfoResponse>'''
    
    def action_get_position_info(self):
        """Handle GetPositionInfo action"""
        return f'''<u:GetPositionInfoResponse xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
  <Track>{self.media_state.current_track}</Track>
  <TrackDuration>{self.media_state.current_track_duration}</TrackDuration>
  <TrackMetaData>{self.escape_xml(self.media_state.current_track_metadata)}</TrackMetaData>
  <TrackURI>{self.escape_xml(self.media_state.current_track_uri)}</TrackURI>
  <RelTime>{self.media_state.playback_position}</RelTime>
  <AbsTime>{self.media_state.playback_position}</AbsTime>
  <RelCount>2147483647</RelCount>
  <AbsCount>2147483647</AbsCount>
</u:GetPositionInfoResponse>'''
    
    def action_set_volume(self, root):
        """Handle SetVolume action"""
        volume = 50
        for elem in root.iter():
            if elem.tag.endswith('DesiredVolume'):
                volume = int(elem.text)
                break
        
        logger.info(f"Setting volume to: {volume}")
        self.media_state.volume = volume
        
        # Set volume on speakers
        threading.Thread(target=self.set_speaker_volume, args=(volume,), daemon=True).start()
        
        return '''<u:SetVolumeResponse xmlns:u="urn:schemas-upnp-org:service:RenderingControl:1">
</u:SetVolumeResponse>'''
    
    def set_speaker_volume(self, volume):
        """Set volume on Samsung speakers"""
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.speaker_group.set_volume(volume), 
                self.speaker_group.loop
            )
            future.result(timeout=5)
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
    
    def action_get_volume(self):
        """Handle GetVolume action"""
        return f'''<u:GetVolumeResponse xmlns:u="urn:schemas-upnp-org:service:RenderingControl:1">
  <CurrentVolume>{self.media_state.volume}</CurrentVolume>
</u:GetVolumeResponse>'''
    
    def action_set_mute(self, root):
        """Handle SetMute action"""
        mute = False
        for elem in root.iter():
            if elem.tag.endswith('DesiredMute'):
                mute = elem.text == '1' or elem.text.lower() == 'true'
                break
        
        logger.info(f"Setting mute to: {mute}")
        self.media_state.mute = mute
        
        return '''<u:SetMuteResponse xmlns:u="urn:schemas-upnp-org:service:RenderingControl:1">
</u:SetMuteResponse>'''
    
    def action_get_mute(self):
        """Handle GetMute action"""
        mute_value = '1' if self.media_state.mute else '0'
        return f'''<u:GetMuteResponse xmlns:u="urn:schemas-upnp-org:service:RenderingControl:1">
  <CurrentMute>{mute_value}</CurrentMute>
</u:GetMuteResponse>'''
    
    def action_get_protocol_info(self):
        """Handle GetProtocolInfo action"""
        # Declare supported protocols
        protocols = "http-get:*:audio/mpeg:*,http-get:*:audio/mp4:*,http-get:*:audio/flac:*,http-get:*:audio/x-flac:*,http-get:*:audio/wav:*,http-get:*:audio/x-wav:*,http-get:*:audio/aac:*"
        return f'''<u:GetProtocolInfoResponse xmlns:u="urn:schemas-upnp-org:service:ConnectionManager:1">
  <Source>{protocols}</Source>
  <Sink></Sink>
</u:GetProtocolInfoResponse>'''
    
    def generate_generic_response(self, action_name):
        """Generate a generic success response for unhandled actions"""
        return f'''<u:{action_name}Response xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
</u:{action_name}Response>'''
    
    def send_soap_response(self, body):
        """Send a SOAP response"""
        envelope = f'''<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
{body}
</s:Body>
</s:Envelope>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/xml; charset="utf-8"')
        self.send_header('EXT', '')
        self.send_header('Content-Length', str(len(envelope)))
        self.end_headers()
        self.wfile.write(envelope.encode('utf-8'))
    
    def send_soap_error(self, error_code, error_description):
        """Send a SOAP error response"""
        error = f'''<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<s:Fault>
<faultcode>s:Client</faultcode>
<faultstring>UPnPError</faultstring>
<detail>
<UPnPError xmlns="urn:schemas-upnp-org:control-1-0">
<errorCode>{error_code}</errorCode>
<errorDescription>{error_description}</errorDescription>
</UPnPError>
</detail>
</s:Fault>
</s:Body>
</s:Envelope>'''
        
        self.send_response(500)
        self.send_header('Content-Type', 'text/xml; charset="utf-8"')
        self.send_header('EXT', '')
        self.end_headers()
        self.wfile.write(error.encode('utf-8'))
    
    @staticmethod
    def escape_xml(text):
        """Escape XML special characters"""
        if not text:
            return ""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&apos;'))
    
    @staticmethod
    def get_local_ip():
        """Get local IP address"""
        try:
            # First try netifaces for best accuracy
            import netifaces
            for interface in netifaces.interfaces():
                if interface == 'lo': continue
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if not ip.startswith('127.'):
                            return ip
        except ImportError:
            pass
            
        # Fallback to connection attempt
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return socket.gethostbyname(socket.gethostname())


class SamsungSpeakerGroup:
    """Manages a group of Samsung speakers"""
    
    def __init__(self, speaker_ips, loop):
        self.speaker_ips = speaker_ips
        self.loop = loop  # Reference to the persistent event loop
        self.devices: List[Speaker] = []
        self.connected = False
        self.master_speaker: Optional[Speaker] = None
        
    async def connect_all(self):
        """Connect to all speakers in the group"""
        for ip in self.speaker_ips:
            try:
                # Create a speaker instance
                speaker = Speaker(ip)
                # Connect to the speaker
                await speaker.connect()
                self.devices.append(speaker)
                logger.info(f"Connected to speaker at {ip}")
                
                # Set first speaker as master
                if self.master_speaker is None:
                    self.master_speaker = speaker
                    
            except Exception as e:
                logger.error(f"Failed to connect to speaker at {ip}: {e}")
        
        self.connected = len(self.devices) > 0
        return self.connected
    
    async def disconnect_all(self):
        """Disconnect from all speakers"""
        for device in self.devices:
            try:
                await device.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from speaker: {e}")
        self.devices.clear()
        self.master_speaker = None
        self.connected = False
    
    async def set_volume(self, volume_level):
        """Set volume on all speakers in the group"""
        if not self.connected:
            logger.warning("Not connected to any speakers")
            return
        
        # Ensure volume is in valid range (0-100)
        volume_level = max(0, min(100, volume_level))
        
        for device in self.devices:
            try:
                await device.set_volume(volume_level)
                logger.info(f"Set volume to {volume_level} on {device.ip}")
            except Exception as e:
                logger.error(f"Failed to set volume on {device.ip}: {e}")
    
    async def play_url(self, url):
        """Play a media URL on all speakers in the group"""
        if not self.connected:
            logger.warning("Not connected to any speakers")
            return
        
        # Play on master speaker first, then group others if needed
        if self.master_speaker:
            try:
                # Set the URL on the master speaker
                logger.info(f"Playing URL on master speaker: {url}")
                await self.master_speaker.set_url_playback(url)
                
                # For grouped playback, other speakers should follow the master
                # This depends on whether speakers are already grouped via Samsung's app
                # If they're pre-grouped, playing on master will play on all
                
                # If speakers need to be individually controlled:
                for device in self.devices[1:]:  # Skip master
                    try:
                        await device.set_url_playback(url)
                    except Exception as e:
                        logger.error(f"Failed to play on speaker {device.ip}: {e}")
                
                logger.info("Media playback started on speaker group")
            except Exception as e:
                logger.error(f"Failed to play media: {e}")
                # Fallback: try playing on each speaker individually
                for device in self.devices:
                    try:
                        await device.set_url_playback(url)
                    except Exception as e:
                        logger.error(f"Fallback play failed on {device.ip}: {e}")
    
    async def pause(self):
        """Pause playback on all speakers"""
        if not self.connected:
            logger.warning("Not connected to any speakers")
            return
            
        for device in self.devices:
            try:
                await device.pause()
                logger.info(f"Paused playback on {device.ip}")
            except Exception as e:
                logger.error(f"Failed to pause on {device.ip}: {e}")
    
    async def stop(self):
        """Stop playback on all speakers"""
        if not self.connected:
            logger.warning("Not connected to any speakers")
            return
            
        for device in self.devices:
            try:
                await device.stop()
                logger.info(f"Stopped playback on {device.ip}")
            except Exception as e:
                logger.error(f"Failed to stop on {device.ip}: {e}")
    
    async def get_state(self):
        """Get playback state from master speaker"""
        if not self.master_speaker:
            return None
            
        try:
            state = await self.master_speaker.get_state()
            return state
        except Exception as e:
            logger.error(f"Failed to get state: {e}")
            return None


class DLNABridgeServer:
    """DLNA server that makes the Samsung speaker group discoverable to Plex"""
    
    def __init__(self, speaker_group, media_state, port=config.DLNA_SERVER_PORT):
        self.speaker_group = speaker_group
        self.media_state = media_state
        self.port = port
        self.server = None
        self.thread = None
        
    def start_server(self):
        """Start the DLNA server in a separate thread"""
        def run_server():
            # Create a custom handler class that has access to the speaker group and media state
            handler = lambda *args, **kwargs: DLNADeviceHandler(
                self.speaker_group, 
                self.media_state, 
                *args, 
                **kwargs
            )
            self.server = HTTPServer(('0.0.0.0', self.port), handler)
            logger.info(f"DLNA server started on port {self.port}")
            self.server.serve_forever()
        
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
        logger.info("DLNA server thread started")
    
    def stop_server(self):
        """Stop the DLNA server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("DLNA server stopped")


def setup_samsung_group(loop):
    """Discover and group Samsung R1 speakers using pywam"""
    logger.info("Setting up Samsung speaker group...")
    
    # Create the speaker group object
    speaker_group = SamsungSpeakerGroup(config.SPEAKER_IPS, loop)
    
    # Connect to all speakers using thread-safe call
    future = asyncio.run_coroutine_threadsafe(
        speaker_group.connect_all(), 
        loop
    )
    
    try:
        success = future.result(timeout=10)
    except Exception as e:
        logger.error(f"Timeout or error connecting to speakers: {e}")
        success = False
    
    if success:
        logger.info(f"Successfully connected to {len(speaker_group.devices)} Samsung speakers")
        return speaker_group
    else:
        logger.warning("Failed to connect to Samsung speakers")
        return None


def connect_to_plex():
    """Connect to Plex Media Server"""
    try:
        plex = PlexServer(config.PLEX_URL, config.PLEX_TOKEN)
        logger.info(f"Connected to Plex: {plex.friendlyName}")
        return plex
    except Exception as e:
        logger.error(f"Failed to connect to Plex: {e}")
        return None


def get_local_ip():
    """Get local IP address"""
    try:
        # First try netifaces for best accuracy
        import netifaces
        for interface in netifaces.interfaces():
            if interface == 'lo': continue
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    if not ip.startswith('127.'):
                        return ip
    except ImportError:
        pass
        
    # Fallback to connection attempt
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return socket.gethostbyname(socket.gethostname())


def announce_dlna_device():
    """Announce the DLNA device using SSDP so Plex can discover it"""
    local_ip = get_local_ip()
    
    # Create SSDP announcement messages
    messages = [
        # Root device announcement
        (
            f"NOTIFY * HTTP/1.1\r\n"
            f"HOST: 239.255.255.250:1900\r\n"
            f"CACHE-CONTROL: max-age=1800\r\n"
            f"LOCATION: http://{local_ip}:{config.DLNA_SERVER_PORT}/description.xml\r\n"
            f"NT: upnp:rootdevice\r\n"
            f"NTS: ssdp:alive\r\n"
            f"SERVER: Linux/4.0 UPnP/1.1 Samsung-DLNA-Bridge/1.0\r\n"
            f"USN: uuid:{config.DEVICE_UUID}::upnp:rootdevice\r\n"
            f"\r\n"
        ),
        # Device announcement
        (
            f"NOTIFY * HTTP/1.1\r\n"
            f"HOST: 239.255.255.250:1900\r\n"
            f"CACHE-CONTROL: max-age=1800\r\n"
            f"LOCATION: http://{local_ip}:{config.DLNA_SERVER_PORT}/description.xml\r\n"
            f"NT: urn:schemas-upnp-org:device:MediaRenderer:1\r\n"
            f"NTS: ssdp:alive\r\n"
            f"SERVER: Linux/4.0 UPnP/1.1 Samsung-DLNA-Bridge/1.0\r\n"
            f"USN: uuid:{config.DEVICE_UUID}::urn:schemas-upnp-org:device:MediaRenderer:1\r\n"
            f"\r\n"
        ),
        # AVTransport service announcement
        (
            f"NOTIFY * HTTP/1.1\r\n"
            f"HOST: 239.255.255.250:1900\r\n"
            f"CACHE-CONTROL: max-age=1800\r\n"
            f"LOCATION: http://{local_ip}:{config.DLNA_SERVER_PORT}/description.xml\r\n"
            f"NT: urn:schemas-upnp-org:service:AVTransport:1\r\n"
            f"NTS: ssdp:alive\r\n"
            f"SERVER: Linux/4.0 UPnP/1.1 Samsung-DLNA-Bridge/1.0\r\n"
            f"USN: uuid:{config.DEVICE_UUID}::urn:schemas-upnp-org:service:AVTransport:1\r\n"
            f"\r\n"
        ),
    ]
    
    # Send SSDP announcements
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
    
    # Bind to specific interface for better multicast
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(local_ip))
    except:
        pass
    
    try:
        for message in messages:
            sock.sendto(message.encode('utf-8'), ("239.255.255.250", 1900))
        logger.debug("DLNA device announced via SSDP")
    except Exception as e:
        logger.error(f"Error sending SSDP announcement: {e}")
    finally:
        sock.close()


class SSDPResponder:
    """Responds to SSDP M-SEARCH discovery requests"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.sock = None
        
    def start(self):
        """Start the SSDP responder"""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("SSDP responder started")
    
    def stop(self):
        """Stop the SSDP responder"""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
    
    def _run(self):
        """Main loop for SSDP responder"""
        import struct
        
        # Create socket for listening to multicast
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            # Bind to SSDP port
            self.sock.bind(('', 1900))
            
            # Join multicast group
            mreq = struct.pack("4sl", socket.inet_aton("239.255.255.250"), socket.INADDR_ANY)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            logger.info("SSDP responder listening for M-SEARCH requests")
            
        except Exception as e:
            logger.error(f"Failed to start SSDP responder: {e}")
            logger.error("This is usually caused by firewall blocking port 1900 or permission issues")
            return
        
        self.sock.settimeout(1.0)
        
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = data.decode('utf-8', errors='ignore')
                
                # Check if this is an M-SEARCH request
                if 'M-SEARCH' in message:
                    # Check if they're searching for something we match
                    search_targets = [
                        'ssdp:all',
                        'upnp:rootdevice',
                        'urn:schemas-upnp-org:device:MediaRenderer:1',
                        'urn:schemas-upnp-org:service:AVTransport:1',
                    ]
                    
                    should_respond = any(st in message for st in search_targets)
                    
                    if should_respond:
                        logger.debug(f"Received M-SEARCH from {addr[0]}, responding...")
                        self._respond_to_search(addr)
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:  # Only log if we didn't intentionally stop
                    logger.error(f"Error in SSDP responder: {e}")
    
    def _respond_to_search(self, addr):
        """Send M-SEARCH response to requester"""
        local_ip = get_local_ip()
        
        # Send multiple responses for different search targets
        responses = [
            # Root device
            (
                f"HTTP/1.1 200 OK\r\n"
                f"CACHE-CONTROL: max-age=1800\r\n"
                f"EXT:\r\n"
                f"LOCATION: http://{local_ip}:{config.DLNA_SERVER_PORT}/description.xml\r\n"
                f"SERVER: Linux/4.0 UPnP/1.1 Samsung-DLNA-Bridge/1.0\r\n"
                f"ST: upnp:rootdevice\r\n"
                f"USN: uuid:{config.DEVICE_UUID}::upnp:rootdevice\r\n"
                f"\r\n"
            ),
            # MediaRenderer device
            (
                f"HTTP/1.1 200 OK\r\n"
                f"CACHE-CONTROL: max-age=1800\r\n"
                f"EXT:\r\n"
                f"LOCATION: http://{local_ip}:{config.DLNA_SERVER_PORT}/description.xml\r\n"
                f"SERVER: Linux/4.0 UPnP/1.1 Samsung-DLNA-Bridge/1.0\r\n"
                f"ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n"
                f"USN: uuid:{config.DEVICE_UUID}::urn:schemas-upnp-org:device:MediaRenderer:1\r\n"
                f"\r\n"
            ),
            # UUID
            (
                f"HTTP/1.1 200 OK\r\n"
                f"CACHE-CONTROL: max-age=1800\r\n"
                f"EXT:\r\n"
                f"LOCATION: http://{local_ip}:{config.DLNA_SERVER_PORT}/description.xml\r\n"
                f"SERVER: Linux/4.0 UPnP/1.1 Samsung-DLNA-Bridge/1.0\r\n"
                f"ST: uuid:{config.DEVICE_UUID}\r\n"
                f"USN: uuid:{config.DEVICE_UUID}\r\n"
                f"\r\n"
            ),
        ]
        
        # Create a new socket for sending responses
        response_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            for response in responses:
                response_sock.sendto(response.encode('utf-8'), addr)
                time.sleep(0.1)  # Small delay between responses
        except Exception as e:
            logger.error(f"Error sending M-SEARCH response: {e}")
        finally:
            response_sock.close()


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Starting Plex DLNA Bridge for Samsung Speakers")
    logger.info("=" * 60)
    
    # 0. Initialize Background Event Loop
    global EVENT_LOOP, LOOP_THREAD
    EVENT_LOOP = asyncio.new_event_loop()
    LOOP_THREAD = threading.Thread(target=start_background_loop, args=(EVENT_LOOP,), daemon=True)
    LOOP_THREAD.start()
    logger.info("Background async loop started")

    # Create media state tracker
    media_state = MediaState()
    
    # 1. Physical Grouping
    speaker_group = setup_samsung_group(EVENT_LOOP)

    if not speaker_group:
        logger.warning("Failed to set up Samsung speaker group")
        logger.warning("Note: You'll need to configure your Samsung speakers with correct IPs")
        # Create a dummy group to at least provide DLNA server functionality
        speaker_group = SamsungSpeakerGroup(config.SPEAKER_IPS, EVENT_LOOP)

    # 2. Start DLNA server to make group discoverable to Plex
    dlna_server = DLNABridgeServer(speaker_group, media_state)
    dlna_server.start_server()
    
    # Give the server a moment to start
    time.sleep(1)
    
    # 3. Start SSDP responder to answer M-SEARCH requests
    ssdp_responder = SSDPResponder()
    ssdp_responder.start()
    
    # Give responder time to initialize
    time.sleep(0.5)
    
    # 4. Announce the device via SSDP so Plex can discover it
    announce_dlna_device()
    
    # 5. Connect to Plex
    plex = connect_to_plex()

    if plex:
        logger.info("=" * 60)
        logger.info(f"✓ Samsung speaker group '{config.GROUP_NAME}' is now discoverable")
        logger.info(f"✓ Appearing to Plex as '{config.DLNA_DEVICE_NAME}'")
        logger.info(f"✓ DLNA server running on port {config.DLNA_SERVER_PORT}")
        logger.info(f"✓ SSDP responder active on port 1900")
        logger.info("✓ Ready for playback commands from Plex")
        logger.info("=" * 60)
        logger.info("\nTo use:")
        logger.info("1. Open Plex and start playing media")
        logger.info("2. Click the cast icon")
        logger.info(f"3. Select '{config.DLNA_DEVICE_NAME}' from the device list")
        logger.info("4. Media will play through your Samsung speakers")
        logger.info("\nPress Ctrl+C to stop the bridge")
        logger.info("=" * 60)
    else:
        logger.warning("Could not connect to Plex, but DLNA bridge is running")
    
    # Periodic announcement interval (every 5 minutes)
    announcement_interval = 300
    last_announcement = time.time()
    
    try:
        # Keep the script running
        while True:
            time.sleep(10)
            
            # Periodically re-announce the device
            current_time = time.time()
            if current_time - last_announcement >= announcement_interval:
                announce_dlna_device()
                last_announcement = current_time
                
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Shutting down...")
        logger.info("=" * 60)
        
        # Stop SSDP responder
        ssdp_responder.stop()
        logger.info("Stopped SSDP responder")
        
        if speaker_group and speaker_group.connected:
            # Clean up async resources using thread-safe call
            future = asyncio.run_coroutine_threadsafe(
                speaker_group.disconnect_all(), 
                EVENT_LOOP
            )
            try:
                future.result(timeout=5)
                logger.info("Disconnected from Samsung speakers")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
        
        dlna_server.stop_server()
        logger.info("Bridge stopped successfully")


if __name__ == "__main__":
    main()