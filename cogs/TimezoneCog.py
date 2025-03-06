import discord
import pendulum
from discord.ext import commands

import Database

from constants import UTC_ZONES


class TimezoneCog(commands.Cog):
    _utc_zones_keys: list = sorted(list(UTC_ZONES.keys()))

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="timezone",
        description="A command to change timezone.",
    )
    @discord.option(
        name="timezone",
        input_type=str,
        required=True,
        description="The UTC timezone",
        autocomplete=discord.utils.basic_autocomplete(_utc_zones_keys)
    )
    async def timezone_cmd(self,
                           ctx: discord.ApplicationContext,
                           timezone: str,
                           ):

        await Database.UserDB.create_user_if_not_exists(ctx.user.id)
        await Database.UserDB.update_user_timezone(ctx.user.id, timezone)

        embed = discord.Embed(
            title="Your timezone has been changed",
            description=f"New timezone: {timezone}",
            color=0x2ADCFF
        )
        embed.set_footer(text=f"Current time in your timezone is: {pendulum.now(UTC_ZONES[timezone]).format("HH:mm")}")
        await ctx.response.send_message(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(TimezoneCog(bot))
