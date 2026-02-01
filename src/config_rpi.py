"""
Configuration Module for Amiibo Emulator - Raspberry Pi Version

Contains all configuration constants and settings for Raspberry Pi.
"""

# Hardware Configuration
class HardwareConfig:
    """Hardware pin and address configuration for Raspberry Pi"""
    
    # I2C Configuration 
    I2C_BUS = 1  # I2C bus number (usually 1 on Raspberry Pi)
    I2C_FREQUENCY = 100000  # 100kHz
    
    # PN532 GPIO Pins (BCM numbering)
    PN532_IRQ_PIN = 16  # GPIO24 for interrupt
    PN532_RST_PIN = 17  # GPIO25 for reset
    PN532_I2C_ADDRESS = 0x24  # Default I2C address for PN532

    
# Application Configuration
class AppConfig:
    """Application behavior configuration"""
    
    # Power Management
    SLEEP_TIMEOUT = 30  # Seconds of inactivity before sleep
    TRANSMISSION_TIMEOUT = 10  # Seconds of transmission before timeout
    
    # Display Settings
    SCROLL_ENABLED = True
    SCROLL_SPEED = 0.5  # Seconds per character
    
    # File Management
    DATA_DIRECTORY = "amiibo_data"
    INDEX_FILE = "index.json"
    CATEGORIES_DIRECTORY = "categories"
    RAW_FILES_DIRECTORY = "raw_files"
    
    # NFC Settings
    NFC_RETRY_ATTEMPTS = 3
    NFC_COMMUNICATION_TIMEOUT = 1.0  # Seconds
    
    # Debug Settings
    DEBUG_MODE = True
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# UI Configuration
class UIConfig:
    """User interface configuration"""
    
    # Display Text
    WELCOME_MESSAGE_LINE1 = "Amiibo"
    WELCOME_MESSAGE_LINE2 = "Emulator Ready"
    
    # State Messages
    CATEGORY_BROWSER_PREFIX = "Category:"
    CHARACTER_BROWSER_PREFIX = "Char:"
    TRANSMISSION_LINE1 = "Transmitting..."
    SLEEP_MESSAGE_LINE1 = "Amiibo"
    SLEEP_MESSAGE_LINE2 = "Emulator Sleep"
    
    # Display Formatting
    MAX_CATEGORY_NAME_LENGTH = 16
    MAX_CHARACTER_NAME_LENGTH = 16
    MAX_SERIES_NAME_LENGTH = 16

# NFC Protocol Configuration
class NFCConfig:
    """NFC protocol and communication settings"""
    
    # PN532 Commands
    COMMAND_DIAGNOSE = 0x00
    COMMAND_GETFIRMWAREVERSION = 0x02
    COMMAND_GETGENERALSTATUS = 0x04
    COMMAND_SAMCONFIGURATION = 0x14
    COMMAND_INLISTPASSIVETARGET = 0x4A
    COMMAND_INDATAEXCHANGE = 0x40
    COMMAND_TGSETGENERALBYTES = 0x64
    COMMAND_TGGETDATA = 0x68
    COMMAND_TGSETDATA = 0x6A
    COMMAND_TGINITASTARGET = 0x8C
    COMMAND_TGSETMETADATA = 0x94
    
    # Mifare Commands
    MIFARE_CMD_AUTH_A = 0x60
    MIFARE_CMD_AUTH_B = 0x61
    MIFARE_CMD_READ = 0x30
    MIFARE_CMD_WRITE = 0xA0
    
    # NFC Data Structure Offsets
    UID_OFFSET = 0
    UID_LENGTH = 7
    CHARACTER_ID_OFFSET = 8
    CHARACTER_ID_LENGTH = 2
    GAME_ID_OFFSET = 10
    GAME_ID_LENGTH = 2
    WRITE_COUNTER_OFFSET = 12
    WRITE_COUNTER_LENGTH = 2
    AMIIBO_ID_OFFSET = 14
    AMIIBO_ID_LENGTH = 8
    NAME_OFFSET = 108
    NAME_LENGTH = 32
    
    # File Format
    NFC_FILE_SIZE = 540  # Standard Amiibo file size
    NFC_HEADER_SIZE = 16  # Header bytes before actual data

# Error Messages
class ErrorMessages:
    """Standardized error messages"""
    
    PN532_COMMUNICATION_FAILED = "PN532 communication failed"
    NFC_FILE_INVALID_SIZE = "Invalid .nfc file size"
    NFC_FILE_PARSE_ERROR = "Error parsing .nfc file"
    NO_CATEGORIES_FOUND = "No Amiibo categories found"
    NO_CHARACTERS_IN_CATEGORY = "No characters in selected category"
    AMIIBO_LOAD_FAILED = "Failed to load Amiibo"
    TRANSMISSION_FAILED = "NFC transmission failed"
    LCD_INITIALIZATION_FAILED = "LCD initialization failed"
    BUTTON_READ_FAILED = "Button read failed"
    FILE_NOT_FOUND = "File not found"

# Success Messages
class SuccessMessages:
    """Standardized success messages"""
    
    PN532_INITIALIZED = "PN532 NFC Controller initialized successfully"
    LCD_INITIALIZED = "LCD display initialized successfully"
    AMIIBO_LOADED = "Amiibo loaded successfully"
    TRANSMISSION_STARTED = "NFC transmission started"
    TRANSMISSION_STOPPED = "NFC transmission stopped"
    INDEX_CREATED = "Amiibo index created successfully"
    SYSTEM_READY = "Amiibo Emulator ready"

# Debug Configuration
class DebugConfig:
    """Debug and logging configuration"""
    
    ENABLE_DEBUG_LOGGING = True
    LOG_TO_FILE = False
    LOG_FILE_PATH = "amiibo_emulator.log"
    LOG_MAX_SIZE = 1024 * 1024  # 1MB
    LOG_BACKUP_COUNT = 3
    
    # Debug levels
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    
    # Components to debug
    DEBUG_NFC = True
    DEBUG_UI = True
    DEBUG_FILE = True
    DEBUG_POWER = True

# Performance Configuration
class PerformanceConfig:
    """Performance tuning configuration"""
    
    # Update intervals (in seconds)
    UI_UPDATE_INTERVAL = 0.1
    BUTTON_CHECK_INTERVAL = 0.05
    TRANSMISSION_CHECK_INTERVAL = 0.1
    
    # Memory management
    GC_INTERVAL = 10  # Run garbage collection every 10 seconds
    MEMORY_THRESHOLD = 1024 * 50  # 50KB threshold for warnings
    
    # Power saving
    SLEEP_DEEP_MODE = False  # Use deep sleep if True, light sleep if False
    WAKE_PIN = 17  # Pin to wake from sleep (UP button)
