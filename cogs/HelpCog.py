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

        embed.set_footer(text=f"Current UTC time: {pendulum.now(tz="UTC").format("HH:mm")}")
        embed.set_image(url=r"https://images-ext-1.discordapp.net/external/oo9_KzTRfsMZNPHXZCMiPl7yI97JZuXt37_hEuw8TVk/https/upload.wikimedia.org/wikipedia/commons/8/88/World_Time_Zones_Map.png?format=webp&quality=lossless&width=1588&height=856")
        view = discord.ui.View()
        button = discord.ui.Button(style=discord.ButtonStyle.url, label="UTC offsets", emoji="🗺️",
                                   url=r"https://en.wikipedia.org/wiki/List_of_UTC_offsets")
        view.add_item(button)
        await ctx.response.send_message(embed=embed, view=view)


def setup(bot: commands.Bot):
    bot.add_cog(HelpCog(bot))
