import asyncio
import io
from datetime import datetime

import discord
import pendulum

import Database
import constants

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
        reminders.extend(await Database.RemindersBD.get_due_daily())
        reminders.extend(await Database.RemindersBD.get_due_and_delete_date())

        if reminders:
            for reminder in reminders:
                await cls.send_reminder_message(reminder)

    @classmethod
    async def send_reminder_message(cls, reminder: Database.RemindersBD):
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

        if reminder.type == "Daily":
            timestamp = pendulum.now("UTC").replace(hour=reminder.timestamp // 3600, minute = reminder.timestamp // 60 % 60, second=reminder.timestamp % 60).timestamp()
            embed.timestamp = datetime.fromtimestamp(timestamp)
        else:
            embed.timestamp = datetime.fromtimestamp(reminder.timestamp)


        content = f"<@{reminder.user_id}>" if not isinstance(recipient, discord.DMChannel) else None
        return await recipient.send(content=content, embed=embed, file=file, view=view)
