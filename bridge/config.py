from typing import List, Optional, Type, Tuple, Any
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, DotEnvSettingsSource, EnvSettingsSource
from pydantic import Field
from pydantic.fields import FieldInfo
import uuid

class CommaSeparatedListMixin:
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == 'device_uuid':
            # print(f"DEBUG: prepare_field_value for {field_name} value='{value}' source={self.__class__.__name__}")
            if value == '':
                return None
        if field_name == 'speaker_ips' and isinstance(value, str) and not value.strip().startswith('['):
            return [x.strip() for x in value.split(',') if x.strip()]
        return super().prepare_field_value(field_name, field, value, value_is_complex)

class CustomEnvSettingsSource(CommaSeparatedListMixin, EnvSettingsSource):
    pass

class CustomDotEnvSettingsSource(CommaSeparatedListMixin, DotEnvSettingsSource):
    pass

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

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            CustomEnvSettingsSource(settings_cls),
            CustomDotEnvSettingsSource(settings_cls, env_file='.env'),
            file_secret_settings,
        )

settings = Settings()
