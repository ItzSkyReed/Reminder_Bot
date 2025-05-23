from datetime import datetime
from typing import Literal

import discord
import pendulum
from discord.ext import commands
from pendulum import Timezone

import Database
import constants
from ReminderEditPage import ReminderEditEmbed, ReminderListView
from ReminderTime import TimeInPastException, ExcessiveFutureTimeException, InvalidReminderTypeException, InvalidTimeFormatException, ReminderTime
from common import can_user_tag_role
from constants import UTC_ZONES, MAX_FILE_SIZE, SUCCESS_MESSAGE_COLOR


class ReminderCog(commands.Cog):
    reminder_group = discord.SlashCommandGroup("reminder", "A group for reminder-related commands")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    async def _send_error(ctx, description: str, time_footer: bool = False):
        embed = discord.Embed(
            title="An error occurred while creating the reminder",
            description=description,
            color=constants.ERROR_MESSAGE_COLOR
        )
        if time_footer:
            embed.set_footer(text='\u200b', icon_url=constants.CLOCK_ICON)
            embed.timestamp = datetime.fromtimestamp(pendulum.now("UTC").timestamp())
        await ctx.response.send_message(embed=embed, ephemeral=True)

    @reminder_group.command(
        name="create",
        description="A command to create reminders.",
    )
    @discord.option(
        name="name",
        input_type=str,
        required=True,
        description="The name of the reminder.",
        max_length=100
    )
    @discord.option(
        name="time",
        input_type=str,
        required=True,
        description="The time of the reminder, for better description use `/help time_formats`.",
        max_length=100
    )
    @discord.option(
        name="description",
        input_type=str,
        required=False,
        description="The description of the reminder.",
        max_length=1000
    )
    @discord.option(
        name="file",
        input_type=discord.Attachment,
        required=False,
        description="Any file that will be sent with your reminder.",
    )
    @discord.option(
        name="type",
        input_type=str,
        choices=["Daily", "Date"],
        default="Date",
        description="Daily reminder runs daily at a set time; date-based runs at a specified time.",
        parameter_name="rem_type"
    )
    @discord.option(
        name="is_private",
        input_type=str,
        choices=["Yes", "No"],
        default="No",
        description="Only you will see the reminder message, sent to your DMs instead of the command channel.",
        parameter_name="private"
    )
    @discord.option(
        name="link",
        input_type=str,
        description="The link that will be sent along with the reminder.",
        required=False,
        max_length=1000
    )
    @discord.option(
        name="mention_role",
        input_type=discord.Role,
        description="The role mentioned in the reminder; if none, the author will be mentioned. Does not work in DMs.",
        required=False
    )
    async def create_cmd(self,
                         ctx: discord.ApplicationContext,
                         name: str,
                         time: str,
                         rem_type: Literal['Daily', 'Date'],
                         link: str,
                         description: str,
                         file: discord.Attachment,
                         private: str,
                         mention_role: discord.Role
                         ):

        is_private: bool = private == "Yes" or isinstance(ctx.channel, discord.DMChannel)

        if mention_role and is_private:
            return await self._send_error(ctx, "A mention of the role cannot be added to a private message.")

        if mention_role and not can_user_tag_role(mention_role.mentionable, ctx.user.guild_permissions):
            return await self._send_error(ctx, "You can't create a reminder mentioning this role because you lack the necessary permissions.")

        if link is not None and not link.startswith("https://"):
            return await self._send_error(ctx, "The link should start with \"https://\"")

        if file is not None:
            if file.size >= MAX_FILE_SIZE:
                return await self._send_error(ctx, "Max file size is 10MB")

            file_data = await file.read()
            file_name = file.filename
        else:
            file_data = None
            file_name = None

        await Database.UserDB.create_user_if_not_exists(ctx.user.id)

        if await Database.RemindersDB.get_user_reminders_count(ctx.user.id) == 50:
            return await self._send_error(ctx, "The limit for reminders is 50. Please delete some reminders to create a new one.")

        utc_zone = (await Database.UserDB.get_user_timezone(ctx.user.id)).tz_name
        timezone = Timezone(UTC_ZONES[utc_zone])

        try:
            reminder_time = ReminderTime(unformatted_time=time, timezone=timezone, rem_type=rem_type)

        except TimeInPastException:
            return await self._send_error(ctx, "The specified time is in the past", True)

        except ExcessiveFutureTimeException:
            return await self._send_error(ctx, "The maximum reminder duration is 2 years.", True)

        except InvalidReminderTypeException:
            return await self._send_error(ctx, "\"Daily\" reminder type can not be used with \"Full Date\" time format", True)

        except InvalidTimeFormatException:
            return await self._send_error(ctx, "The specified time format cannot be parsed", True)

        await Database.RemindersDB.add_reminder(user_id=ctx.user.id, time=reminder_time, name=name, description=description,
                                                rem_type=rem_type, link=link, file=file_data, file_name=file_name, private=is_private,
                                                mention_role=mention_role.id if mention_role else None, channel_id=ctx.channel.id)

        embed = discord.Embed(title=f"Reminder \"{name}\" created!", color=SUCCESS_MESSAGE_COLOR)

        if rem_type == "Date":
            description = f"Triggers at <t:{int(reminder_time.bd_timestamp)}:t>; Current timezone: {utc_zone.upper()}"
            footer = "This is a one-time reminder"
        else:
            description = f"Will trigger <t:{int(reminder_time.time.timestamp())}:R>"
            footer = "This is a daily reminder"

        embed.add_field(name="", value=description, inline=False)
        embed.set_footer(text=footer, icon_url=constants.CLOCK_ICON)
        embed.timestamp = datetime.fromtimestamp(pendulum.now("UTC").timestamp())

        return await ctx.response.send_message(embed=embed, ephemeral=is_private)

    @reminder_group.command(
        name="edit",
        description="Edit or view active reminders.",
    )
    async def edit_cmd(self, ctx: discord.ApplicationContext):
        reminders = await Database.RemindersDB.get_user_reminders_without_file(ctx.user.id)
        if not reminders:
            return await self._send_error(ctx, "❌ You don't have any reminders.", True)

        reminder_embeds = []
        for reminder in reminders:
            embed = ReminderEditEmbed(reminder=reminder, embed_type="short", roles=ctx.guild.roles if ctx.guild else None)

            reminder_embeds.append(embed)
        view = ReminderListView(reminder_embeds=reminder_embeds)

        await ctx.response.send_message(content="### Choose reminder to edit", embeds=view.embeds[:view.per_page], view=view, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(ReminderCog(bot))
