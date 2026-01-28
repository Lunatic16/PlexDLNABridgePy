from enum import Enum
from dataclasses import dataclass, field

class PlaybackState(Enum):
    STOPPED = "STOPPED"
    PLAYING = "PLAYING"
    PAUSED_PLAYBACK = "PAUSED_PLAYBACK"
    TRANSITIONING = "TRANSITIONING"
    NO_MEDIA_PRESENT = "NO_MEDIA_PRESENT"

@dataclass
class MediaState:
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
