import asyncio
import logging
from typing import List, Optional
from pywam.speaker import Speaker
from bridge.config import settings
from bridge.core.models import PlaybackState

logger = logging.getLogger(__name__)

class SpeakerManager:
    def __init__(self):
        self.speakers: List[Speaker] = []
        self._lock = asyncio.Lock()

    async def discover_and_connect(self):
        """Connect to configured speakers and optionally discover more."""
        ips = set(settings.speaker_ips)
        
        # Simple discovery could be added here using pywam.scanner
        # For now, we use the provided IPs
        
        for ip in ips:
            try:
                speaker = Speaker(ip)
                # pywam is mostly synchronous, we wrap calls in threads if needed
                # but Speaker(ip) just initializes the object.
                self.speakers.append(speaker)
                logger.info(f"Connected to speaker at {ip}")
            except Exception as e:
                logger.error(f"Failed to connect to speaker at {ip}: {e}")

    async def play(self, uri: str):
        async with self._lock:
            for speaker in self.speakers:
                try:
                    # Wrapping sync pywam calls
                    await asyncio.to_thread(speaker.play_url, uri)
                except Exception as e:
                    logger.error(f"Error playing on {speaker.ip}: {e}")

    async def pause(self):
        async with self._lock:
            for speaker in self.speakers:
                try:
                    await asyncio.to_thread(speaker.pause)
                except Exception as e:
                    logger.error(f"Error pausing on {speaker.ip}: {e}")

    async def stop(self):
        async with self._lock:
            for speaker in self.speakers:
                try:
                    await asyncio.to_thread(speaker.stop)
                except Exception as e:
                    logger.error(f"Error stopping on {speaker.ip}: {e}")

    async def set_volume(self, volume: int):
        async with self._lock:
            for speaker in self.speakers:
                try:
                    await asyncio.to_thread(speaker.set_volume, volume)
                except Exception as e:
                    logger.error(f"Error setting volume on {speaker.ip}: {e}")
