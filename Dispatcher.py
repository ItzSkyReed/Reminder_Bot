import asyncio
import io

import discord

import Database
import constants
from common import calculate_timestamp_for_discord_footer

from constants import REMINDER_MESSAGE_COLOR, DISPATCHER_PERIOD, EMBED_IMAGE_TYPES


class Dispatcher:
    bot: discord.Bot

    @classmethod
    async def check_reminders(cls):
        while True:
            await cls.send_reminders()
            await asyncio.sleep(DISPATCHER_PERIOD)

    @classmethod
    async def send_reminders(cls):
        reminders = []
        reminders.extend(await Database.RemindersDB.get_due_daily())
        reminders.extend(await Database.RemindersDB.get_due_and_delete_date())

        if reminders:
            for reminder in reminders:
                await cls.send_reminder_message(reminder)

    @classmethod
    async def send_reminder_message(cls, reminder: Database.RemindersDB):
        embed = (discord.Embed(
            title=f'Reminder: "{reminder.name}"',
            color=REMINDER_MESSAGE_COLOR,
            description=reminder.description
        ))
        embed.set_footer(
            text="This is a daily reminder" if reminder.type == "Daily" else "This is a one-time reminder",
            icon_url=constants.CLOCK_ICON)

        file = None
        if reminder.file:
            file = discord.File(io.BytesIO(reminder.file), filename=reminder.file_name)
            if reminder.file_name.split(".")[-1].lower() in EMBED_IMAGE_TYPES:
                embed.set_image(url=f"attachment://{reminder.file_name}")

        if reminder.private:
            recipient = await cls.bot.get_or_fetch_user(reminder.user_id)
        else:
            recipient = cls.bot.get_channel(reminder.channel_id)
            if recipient is None:
                recipient = await cls.bot.fetch_channel(reminder.channel_id)

        if reminder.link:
            view = discord.ui.View()
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.url, url=reminder.link, label="Link", emoji="🔗"))
        else:
            view = None

        embed.timestamp = calculate_timestamp_for_discord_footer(reminder.timestamp, reminder_type=reminder.type)

        mention = f"<@{reminder.user_id}>" if not reminder.mention_role else f"<@&{reminder.mention_role}>"
        content = mention if not isinstance(recipient, discord.DMChannel) else None

        return await recipient.send(content=content, embed=embed, file=file, view=view)
