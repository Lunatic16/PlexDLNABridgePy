import asyncio
import socket
import logging
import struct
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
        return (
            "NOTIFY * HTTP/1.1\r\n"
            f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
            "CACHE-CONTROL: max-age=1800\r\n"
            f"LOCATION: http://{self.local_ip}:{self.port}/description.xml\r\n"
            "NT: upnp:rootdevice\r\n"
            "NTS: ssdp:alive\r\n"
            "SERVER: Linux/4.0 UPnP/1.1 Samsung-DLNA-Bridge/2.0\r\n"
            f"USN: uuid:{settings.device_uuid}::upnp:rootdevice\r\n"
            "\r\n"
        )

    def _get_msearch_response(self):
        return (
            "HTTP/1.1 200 OK\r\n"
            "CACHE-CONTROL: max-age=1800\r\n"
            "EXT:\r\n"
            f"LOCATION: http://{self.local_ip}:{self.port}/description.xml\r\n"
            "SERVER: Linux/4.0 UPnP/1.1 Samsung-DLNA-Bridge/2.0\r\n"
            "ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n"
            f"USN: uuid:{settings.device_uuid}::urn:schemas-upnp-org:device:MediaRenderer:1\r\n"
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

        sock.bind(('', SSDP_PORT))

        # Join multicast group
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
        # Should we respond to this?
        should_respond = any(st in message for st in [
            'ssdp:all',
            'upnp:rootdevice', 
            'MediaRenderer',
            'urn:schemas-upnp-org:device:MediaRenderer:1'
        ])
        
        if should_respond:
            logger.debug(f"Responding to M-SEARCH from {addr}")
            response = self._get_msearch_response()
            self.transport.sendto(response.encode('utf-8'), addr)

    async def _periodic_notify(self):
        while True:
            try:
                logger.debug("Sending periodic SSDP NOTIFY")
                message = self._get_notify_message()
                
                # Send to multicast group
                # We need a separate socket for sending multicast or just use the existing one?
                # Usually sending to multicast address works on the same socket if configured
                self.transport.sendto(message.encode('utf-8'), (SSDP_ADDR, SSDP_PORT))
                
            except Exception as e:
                logger.error(f"Error sending SSDP NOTIFY: {e}")
            
            await asyncio.sleep(600) # Every 10 minutes