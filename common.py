from datetime import datetime
import pendulum


def calculate_timestamp_for_discord_footer(timestamp: int, reminder_type: str) -> datetime:
    if reminder_type == "Daily":
        timestamp = pendulum.now("UTC").replace(hour=timestamp // 3600, minute = timestamp // 60 % 60, second=timestamp % 60).timestamp()
        return datetime.fromtimestamp(timestamp)
    else:
        return datetime.fromtimestamp(timestamp)