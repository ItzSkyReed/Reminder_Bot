from datetime import datetime

import discord
import pendulum
from discord.ext import commands

import constants


class HelpCog(commands.Cog):
    help = discord.SlashCommandGroup("help", "Command group of useful information about commands")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @help.command(
        name="timezones",
        description="Information about the time zones",
    )
    async def timezone_help_cmd(self,
                                ctx: discord.ApplicationContext,
                                ):
        embed = discord.Embed(
            title="Time Zones",
            description=f"**UTC time format**\n"
                        f"To set your own time zone, determine your UTC offset. Then, type the `/timezone` command and select the correct time zone.\n"
                        r"For example: \"UTC+3:00\" - Moscow time.",
            color=constants.INFO_MESSAGE_COLOR
        )
        embed.add_field(name="**Be careful!**", value="When changing the time zone, previously created reminders will not be updated with the new time zone!", inline=False)

        embed.set_footer(text='\u200b', icon_url=constants.CLOCK_ICON)
        embed.timestamp = datetime.fromtimestamp(pendulum.now("UTC").timestamp())
        embed.set_image(
            url=r"https://images-ext-1.discordapp.net/external/oo9_KzTRfsMZNPHXZCMiPl7yI97JZuXt37_hEuw8TVk/https/upload.wikimedia.org/wikipedia/commons/8/88/World_Time_Zones_Map.png?format=webp&quality=lossless&width=1588&height=856")
        view = discord.ui.View()
        button = discord.ui.Button(style=discord.ButtonStyle.url, label="UTC offsets", emoji="🗺️",
                                   url=r"https://en.wikipedia.org/wiki/List_of_UTC_offsets")
        view.add_item(button)
        await ctx.response.send_message(embed=embed, view=view)

    @help.command(
        name="time_formats",
        description="Information about the time formats",
    )
    async def timezone_help_cmd(self,
                                ctx: discord.ApplicationContext,
                                ):
        embed = discord.Embed(title="Time Formats", color=constants.INFO_MESSAGE_COLOR)
        embed.add_field(name="**HH:MM Format**", value="> Example: `21:45`\n"
                                                       "> For `Daily` reminders, the specified time will trigger a reminder every day for your time zone.\n"
                                                       "> For `Date` reminders, the current day will be used unless the specified time has already passed, "
                                                       "in which case the next day will be selected.", inline=False)

        embed.add_field(name="**DD.MM.YYYY HH:MM Format**", value="> Example: `21.07.2024 15:34`\n"
                                                                  "> Cannot be used for `Daily` reminders.\n"
                                                                  "> For `Date` reminders, the exact specified date will be used.\n"
                                                                  "> *If year is not specified, current year will be used.*", inline=False)

        embed.add_field(name="**Timer Format**", value="> Example: `3h 4m 2s`\n"
                                                       "> For `Daily` reminders, the current time will be taken, the specified duration will be added to it, "
                                                       "and the reminder will trigger every day at the calculated time.\n"
                                                       "> For `Date` reminders, the specified duration will be added to the current time.", inline=False)

        embed.add_field(name="**Restrictions**", value="> A reminder can be set for at least 2 minutes when created and at least 10 minutes when edited, "
                                                       "but no more than 2 years in advance.", inline=False)

        embed.set_footer(text='\u200b', icon_url=constants.CLOCK_ICON)
        embed.timestamp = datetime.fromtimestamp(pendulum.now("UTC").timestamp())

        return await ctx.response.send_message(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(HelpCog(bot))
