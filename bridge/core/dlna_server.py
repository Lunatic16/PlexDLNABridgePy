import logging
import xml.etree.ElementTree as ET
from aiohttp import web
from bridge.config import settings
from bridge.core.models import MediaState, PlaybackState
from bridge.core.speaker_manager import SpeakerManager

logger = logging.getLogger(__name__)

class DLNAServer:
    def __init__(self, speaker_manager: SpeakerManager, local_ip: str):
        self.speaker_manager = speaker_manager
        self.local_ip = local_ip
        self.media_state = MediaState()
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        self.app.router.add_get('/description.xml', self.handle_description)
        self.app.router.add_get('/upnp/service/{service}/scpd.xml', self.handle_scpd)
        self.app.router.add_post('/upnp/control/{service}', self.handle_control)
        self.app.router.add_get('/', self.handle_index)

    async def handle_index(self, request):
        return web.Response(text="Samsung DLNA Bridge Running", content_type='text/html')

    async def handle_description(self, request):
        xml_desc = f'''<?xml version="1.0" encoding="utf-8"?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
  <specVersion><major>1</major><minor>0</minor></specVersion>
  <device>
    <deviceType>urn:schemas-upnp-org:device:MediaRenderer:1</deviceType>
    <friendlyName>{settings.dlna_device_name}</friendlyName>
    <manufacturer>Samsung</manufacturer>
    <manufacturerURL>http://www.samsung.com</manufacturerURL>
    <modelDescription>Samsung Multiroom Speaker Group</modelDescription>
    <modelName>Samsung R1 Group</modelName>
    <modelNumber>2.0</modelNumber>
    <UDN>uuid:{settings.device_uuid}</UDN>
    <serviceList>
      <service>
        <serviceType>urn:schemas-upnp-org:service:AVTransport:1</serviceType>
        <serviceId>urn:upnp-org:serviceId:AVTransport</serviceId>
        <SCPDURL>/upnp/service/AVTransport/scpd.xml</SCPDURL>
        <controlURL>/upnp/control/AVTransport1</controlURL>
        <eventSubURL>/upnp/event/AVTransport1</eventSubURL>
      </service>
      <service>
        <serviceType>urn:schemas-upnp-org:service:RenderingControl:1</serviceType>
        <serviceId>urn:upnp-org:serviceId:RenderingControl</serviceId>
        <SCPDURL>/upnp/service/RenderingControl/scpd.xml</SCPDURL>
        <controlURL>/upnp/control/RenderingControl1</controlURL>
        <eventSubURL>/upnp/event/RenderingControl1</eventSubURL>
      </service>
    </serviceList>
  </device>
</root>'''
        return web.Response(text=xml_desc, content_type='text/xml')

    async def handle_scpd(self, request):
        # Simplified SCPD
        scpd = '''<?xml version="1.0" encoding="utf-8"?>
<scpd xmlns="urn:schemas-upnp-org:service-1-0">
  <specVersion><major>1</major><minor>0</minor></specVersion>
  <actionList>
    <action><name>GetTransportInfo</name></action>
    <action><name>SetAVTransportURI</name></action>
    <action><name>Play</name></action>
    <action><name>Pause</name></action>
    <action><name>Stop</name></action>
    <action><name>SetVolume</name></action>
    <action><name>GetVolume</name></action>
  </actionList>
</scpd>'''
        return web.Response(text=scpd, content_type='text/xml')

    async def handle_control(self, request):
        soap_action = request.headers.get('SOAPACTION', '').strip('"')
        body = await request.read()
        logger.debug(f"SOAP Action: {soap_action}")
        
        try:
            root = ET.fromstring(body)
            action_name = soap_action.split('#')[-1] if '#' in soap_action else None
            
            if action_name == 'SetAVTransportURI':
                await self.action_set_uri(root)
                response = self.wrap_response('SetAVTransportURI', '')
            elif action_name == 'Play':
                await self.speaker_manager.play(self.media_state.current_track_uri)
                self.media_state.transport_state = PlaybackState.PLAYING
                response = self.wrap_response('Play', '')
            elif action_name == 'Pause':
                await self.speaker_manager.pause()
                self.media_state.transport_state = PlaybackState.PAUSED_PLAYBACK
                response = self.wrap_response('Pause', '')
            elif action_name == 'Stop':
                await self.speaker_manager.stop()
                self.media_state.transport_state = PlaybackState.STOPPED
                response = self.wrap_response('Stop', '')
            elif action_name == 'GetTransportInfo':
                data = f'<CurrentTransportState>{self.media_state.transport_state.value}</CurrentTransportState><CurrentTransportStatus>OK</CurrentTransportStatus><CurrentSpeed>1</CurrentSpeed>'
                response = self.wrap_response('GetTransportInfo', data)
            elif action_name == 'SetVolume':
                vol = int(root.find('.//DesiredVolume').text)
                await self.speaker_manager.set_volume(vol)
                self.media_state.volume = vol
                response = self.wrap_response('SetVolume', '')
            else:
                response = self.wrap_response(action_name, '')
                
            return web.Response(text=response, content_type='text/xml')
        except Exception as e:
            logger.error(f"Error handling SOAP: {e}")
            return web.Response(status=500)

    async def action_set_uri(self, root):
        uri = root.find('.//CurrentURI').text
        if 'X-Plex-Token' not in uri and settings.plex_token:
            sep = '&' if '?' in uri else '?'
            uri = f"{uri}{sep}X-Plex-Token={settings.plex_token}"
        self.media_state.current_track_uri = uri
        logger.info(f"URI set to: {uri}")

    def wrap_response(self, action, data):
        return f'''<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:{action}Response xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
      {data}
    </u:{action}Response>
  </s:Body>
</s:Envelope>'''

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', settings.dlna_server_port)
        await site.start()
        logger.info(f"DLNA Server started on port {settings.dlna_server_port}")
