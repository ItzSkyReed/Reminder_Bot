from datetime import datetime
import pendulum
from discord import Permissions


def calculate_timestamp_for_discord_footer(timestamp: int, reminder_type: str) -> datetime:
    if reminder_type == "Daily":
        timestamp = pendulum.now("UTC").replace(hour=timestamp // 3600, minute = timestamp // 60 % 60, second=timestamp % 60).timestamp()
        return datetime.fromtimestamp(timestamp)
    else:
        return datetime.fromtimestamp(timestamp)

def can_user_tag_role(is_role_mentionable: bool, guild_permissions: Permissions) -> bool:
    return guild_permissions.administrator or guild_permissions.mention_everyone or is_role_mentionable