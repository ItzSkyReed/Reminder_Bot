import re

# Time patterns
HH_MM_pattern: re.Pattern = re.compile(r"^(?:[01]?[0-9]|2[0-3]):([0-5][0-9])$")
FULL_DATE_pattern: re.Pattern = re.compile(r"^(\d{2})\.(\d{2})(?:\.(\d{4}))? (\d{2}):(\d{2})$")

# Timer duration patterns
TIMER_TIME_patterns = {
    'weeks': re.compile(r'(\d+)[wн]', re.IGNORECASE),
    'days': re.compile(r'(\d+)[dд]', re.IGNORECASE),
    'hours': re.compile(r'(\d+)[hч]', re.IGNORECASE),
    'minutes': re.compile(r'(\d+)[mм]', re.IGNORECASE),
    'seconds': re.compile(r'(\d+)[sс]', re.IGNORECASE),
}

# Time zones mapping
UTC_ZONES = {
    "UTC+0": "Europe/London",
    "UTC-12": "Etc/GMT+12",
    "UTC-11": "Pacific/Samoa",
    "UTC-10": "Pacific/Honolulu",
    "UTC-9": "America/Anchorage",
    "UTC-8": "America/Los_Angeles",
    "UTC-7": "America/Denver",
    "UTC-6": "America/Chicago",
    "UTC-5": "America/New_York",
    "UTC-4": "America/Halifax",
    "UTC-3": "America/Argentina/Buenos_Aires",
    "UTC-2": "Atlantic/Azores",
    "UTC-1": "Atlantic/Cape_Verde",
    "UTC+1": "Europe/Paris",
    "UTC+2": "Europe/Bucharest",
    "UTC+3": "Europe/Moscow",
    "UTC+4": "Asia/Baku",
    "UTC+5": "Asia/Karachi",
    "UTC+6": "Asia/Dhaka",
    "UTC+7": "Asia/Bangkok",
    "UTC+8": "Asia/Singapore",
    "UTC+9": "Asia/Tokyo",
    "UTC+10": "Australia/Sydney",
    "UTC+11": "Pacific/Guadalcanal",
    "UTC+12": "Pacific/Fiji",
    "UTC+13": "Pacific/Tongatapu",
    "UTC+14": "Pacific/Kiritimati"
}

# Icons
CLOCK_ICON = r"https://i.imgur.com/RwucE6D.png"  # Clock icon
FILE_ICON = r"https://i.imgur.com/c5oRe54.png"   # File icon

# Message colors
ERROR_MESSAGE_COLOR = 0xFF1638      # Error message color
INFO_MESSAGE_COLOR = 0x2ADCFF       # Info message color
SUCCESS_MESSAGE_COLOR = 0x3AFF64    # Success message color
REMINDER_MESSAGE_COLOR = 0xB991FF   # Reminder message color

# Allowed embedded image types
EMBED_IMAGE_TYPES = {"png", "jpg", "jpeg", "webp", "gif", "tiff", "ico"}

# Reminder settings
DISPATCHER_PERIOD = 20     # How often reminders are fetched from the database (in seconds)
MAX_FILE_SIZE = 10485760   # Maximum file size that can be attached to a reminder

# Database Settings
DATABASE_NAME = "database.db"