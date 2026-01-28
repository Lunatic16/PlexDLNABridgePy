import asyncio
import logging
import socket
from bridge.config import settings
from bridge.core.speaker_manager import SpeakerManager
from bridge.core.ssdp import SSDPResponder
from bridge.core.dlna_server import DLNAServer

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

async def main():
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("bridge")
    
    local_ip = get_local_ip()
    logger.info(f"Starting Bridge on {local_ip}")

    # 1. Initialize Speaker Manager
    speaker_manager = SpeakerManager()
    await speaker_manager.discover_and_connect()

    # 2. Initialize DLNA Server (aiohttp)
    dlna_server = DLNAServer(speaker_manager, local_ip)
    await dlna_server.start()

    # 3. Initialize SSDP Responder
    ssdp = SSDPResponder(local_ip, settings.dlna_server_port)
    await ssdp.start()

    logger.info("Bridge is fully operational")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Shutting down...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
