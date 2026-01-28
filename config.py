# Configuration for Plex DLNA Bridge

# ==============================================================================
# PLEX CONFIGURATION
# ==============================================================================

# Your Plex Media Server URL
# Format: http://IP_ADDRESS:PORT
# Default Plex port is 32400
PLEX_URL = 'http://192.168.1.100:32400'

# Your Plex authentication token
# How to find: See README.md section "Get Your Plex Token"
PLEX_TOKEN = 'your_plex_token_here'


# ==============================================================================
# SPEAKER CONFIGURATION
# ==============================================================================

# Friendly name for your speaker group (for internal use)
GROUP_NAME = "Living Room R1 Group"

# Name that will appear in Plex's device list
DLNA_DEVICE_NAME = "Samsung Speaker Group"

# List of Samsung speaker IP addresses
# Add as many speakers as you have in your group
# Format: List of strings, each containing an IP address
SPEAKER_IPS = [
    '192.168.1.101',  # Speaker 1
    '192.168.1.102',  # Speaker 2
    # Add more speakers here as needed
]


# ==============================================================================
# NETWORK CONFIGURATION
# ==============================================================================

# Port for DLNA server (standard is 32488)
# Only change if this port is already in use
DLNA_SERVER_PORT = 32488

# Device UUID (should remain constant for device recognition)
# Don't change this unless you want Plex to see it as a new device
DEVICE_UUID = "3c202906-2b86-4f88-a79c-f6d4e7c8d1a3"


# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
# Use DEBUG for troubleshooting, INFO for normal operation
LOG_LEVEL = 'INFO'
