from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import uuid

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # Plex Configuration
    plex_url: str = Field(default="http://192.168.1.100:32400", validation_alias="PLEX_URL")
    plex_token: str = Field(default="your_plex_token_here", validation_alias="PLEX_TOKEN")

    # Speaker Configuration
    group_name: str = Field(default="Samsung Group", validation_alias="GROUP_NAME")
    dlna_device_name: str = Field(default="Samsung Speaker Bridge", validation_alias="DLNA_DEVICE_NAME")
    speaker_ips: List[str] = Field(default_factory=list, validation_alias="SPEAKER_IPS")
    auto_discover_speakers: bool = Field(default=True, validation_alias="AUTO_DISCOVER_SPEAKERS")

    # Network Configuration
    dlna_server_port: int = Field(default=32488, validation_alias="DLNA_SERVER_PORT")
    device_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), validation_alias="DEVICE_UUID")
    
    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

settings = Settings()
