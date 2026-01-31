import asyncio
import socket
import logging
import struct
from email.utils import formatdate
from bridge.config import settings

logger = logging.getLogger(__name__)

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900

class SSDPResponderProtocol(asyncio.DatagramProtocol):
    def __init__(self, responder):
        self.responder = responder
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            message = data.decode('utf-8', errors='ignore')
            if 'M-SEARCH' in message:
                self.responder.handle_msearch(message, addr)
        except Exception as e:
            logger.error(f"Error handling SSDP datagram: {e}")

class SSDPResponder:
    def __init__(self, local_ip: str, port: int):
        self.local_ip = local_ip
        self.port = port
        self.transport = None
        self.protocol = None

    def _get_notify_message(self):
        date_str = formatdate(timeval=None, localtime=False, usegmt=True)
        return (
            "NOTIFY * HTTP/1.1\r\n"
            f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
            "CACHE-CONTROL: max-age=1800\r\n"
            f"LOCATION: http://{self.local_ip}:{self.port}/description.xml\r\n"
            "NT: upnp:rootdevice\r\n"
            "NTS: ssdp:alive\r\n"
            "SERVER: Linux/4.0 UPnP/1.1 Samsung-DLNA-Bridge/2.0\r\n"
            "X-DLNADOC: DMR-1.50\r\n"
            f"USN: uuid:{settings.device_uuid}::upnp:rootdevice\r\n"
            f"DATE: {date_str}\r\n"
            "BOOTID.UPNP.ORG: 1\r\n"
            "CONFIGID.UPNP.ORG: 1\r\n"
            "\r\n"
        )

    def _get_response(self, st):
        date_str = formatdate(timeval=None, localtime=False, usegmt=True)
        
        if st == 'upnp:rootdevice':
            usn = f"uuid:{settings.device_uuid}::upnp:rootdevice"
        elif st == 'urn:schemas-upnp-org:device:MediaRenderer:1':
            usn = f"uuid:{settings.device_uuid}::urn:schemas-upnp-org:device:MediaRenderer:1"
        elif st == f"uuid:{settings.device_uuid}":
            usn = f"uuid:{settings.device_uuid}"
        else:
            usn = f"uuid:{settings.device_uuid}::{st}"

        return (
            "HTTP/1.1 200 OK\r\n"
            "CACHE-CONTROL: max-age=1800\r\n"
            "EXT:\r\n"
            f"LOCATION: http://{self.local_ip}:{self.port}/description.xml\r\n"
            "SERVER: Linux/4.0 UPnP/1.1 Samsung-DLNA-Bridge/2.0\r\n"
            "X-DLNADOC: DMR-1.50\r\n"
            f"ST: {st}\r\n"
            f"USN: {usn}\r\n"
            f"DATE: {date_str}\r\n"
            "BOOTID.UPNP.ORG: 1\r\n"
            "CONFIGID.UPNP.ORG: 1\r\n"
            "\r\n"
        )

    async def start(self):
        loop = asyncio.get_running_loop()
        
        # Create multicast socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # On some platforms we need SO_REUSEPORT
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass

        # Set TTL for multicast to ensure it reaches other devices
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        sock.bind(('', SSDP_PORT))

        # Join multicast group
        # Try to join on the specific interface if possible
        try:
            if self.local_ip and self.local_ip != '127.0.0.1':
                # Join on specific interface
                mreq = struct.pack("4s4s", socket.inet_aton(SSDP_ADDR), socket.inet_aton(self.local_ip))
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                logger.info(f"SSDP bound to interface {self.local_ip}")
            else:
                # Fallback to default
                mreq = struct.pack("4sl", socket.inet_aton(SSDP_ADDR), socket.INADDR_ANY)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except Exception as e:
            logger.warning(f"Failed to bind multicast to specific interface: {e}. Falling back to default.")
            mreq = struct.pack("4sl", socket.inet_aton(SSDP_ADDR), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        # Start transport
        self.transport, self.protocol = await loop.create_datagram_endpoint(
            lambda: SSDPResponderProtocol(self),
            sock=sock
        )
        
        logger.info(f"SSDP Responder started on {SSDP_ADDR}:{SSDP_PORT}")
        
        # Start periodic NOTIFY
        asyncio.create_task(self._periodic_notify())

    def handle_msearch(self, message, addr):
        # Extract ST header
        st_header = None
        for line in message.splitlines():
            if line.upper().startswith('ST:'):
                st_header = line[3:].strip()
                break
        
        if not st_header:
            return

        # Responses to send
        responses = []
        
        if st_header == 'ssdp:all':
            responses.append(self._get_response('upnp:rootdevice'))
            responses.append(self._get_response(f"uuid:{settings.device_uuid}"))
            responses.append(self._get_response('urn:schemas-upnp-org:device:MediaRenderer:1'))
        elif st_header == 'upnp:rootdevice':
            responses.append(self._get_response('upnp:rootdevice'))
        elif st_header == f"uuid:{settings.device_uuid}":
            responses.append(self._get_response(f"uuid:{settings.device_uuid}"))
        elif 'MediaRenderer' in st_header:
            responses.append(self._get_response('urn:schemas-upnp-org:device:MediaRenderer:1'))
        
        for response in responses:
            logger.debug(f"Responding to M-SEARCH from {addr}")
            self.transport.sendto(response.encode('utf-8'), addr)

    async def _periodic_notify(self):
        while True:
            try:
                logger.debug("Sending periodic SSDP NOTIFY")
                message = self._get_notify_message()
                
                # Use a fresh socket for sending NOTIFY to ensure correct interface binding
                # This matches the behavior of the working diagnostic tool
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                    if self.local_ip and self.local_ip != '127.0.0.1':
                        try:
                            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(self.local_ip))
                        except Exception:
                            pass
                    sock.sendto(message.encode('utf-8'), (SSDP_ADDR, SSDP_PORT))
                
            except Exception as e:
                logger.error(f"Error sending SSDP NOTIFY: {e}")
            
            await asyncio.sleep(60) # Every 60 seconds