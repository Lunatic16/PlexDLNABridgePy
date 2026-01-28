import asyncio
import socket
import logging
import struct
from bridge.config import settings

logger = logging.getLogger(__name__)

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900

class SSDPResponder:
    def __init__(self, local_ip: str, port: int):
        self.local_ip = local_ip
        self.port = port
        self.transport = None

    def _get_notify_message(self):
        return (
            "NOTIFY * HTTP/1.1\r\n"
            f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
            "CACHE-CONTROL: max-age=1800\r\n"
            f"LOCATION: http://{self.local_ip}:{self.port}/description.xml\r\n"
            