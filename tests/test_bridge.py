import pytest
from bridge.core.models import MediaState, PlaybackState
from bridge.config import settings

def test_media_state_initialization():
    state = MediaState()
    assert state.transport_state == PlaybackState.NO_MEDIA_PRESENT
    assert state.volume == 50

def test_config_uuid():
    # Ensure UUID is generated if not provided
    assert settings.device_uuid is not None
    assert len(settings.device_uuid) > 0

@pytest.mark.asyncio
async def test_dlna_server_xml_gen():
    from bridge.core.dlna_server import DLNAServer
    from unittest.mock import MagicMock
    
    mock_manager = MagicMock()
    server = DLNAServer(mock_manager, "127.0.0.1")
    
    # Test description XML generation
    request = MagicMock()
    response = await server.handle_description(request)
    assert response.status == 200
    assert settings.dlna_device_name in response.text
    assert "MediaRenderer" in response.text
