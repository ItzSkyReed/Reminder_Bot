import asyncio
import os

from dotenv import load_dotenv
import discord

bot = discord.Bot(intents=discord.Intents.all())

from Dispatcher import Dispatcher

Dispatcher.bot = bot

@bot.event
async def on_ready():
    asyncio.create_task(Dispatcher.check_reminders())

load_dotenv()

bot.load_extension("cogs.ReminderCog")
bot.load_extension("cogs.TimezoneCog")
bot.load_extension("cogs.HelpCog")

token = os.getenv("REMINDER_BOT_TOKEN")

if not token:
    raise ValueError("REMINDER_BOT_TOKEN environment variable not set")

bot.run(token)