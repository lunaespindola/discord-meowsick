import discord
from discord.ext import commands
import asyncio
import os
from discord import Activity, ActivityType
from dotenv import load_dotenv

load_dotenv()

activity = Activity(name="!help", type=ActivityType.listening)
bot = commands.Bot(command_prefix='!', activity=activity, intents=discord.Intents.all())

token = os.getenv("TOKEN")

async def load():
    bot.remove_command('help')
    print("Loading extensions...")
    for filename in os.listdir("."):
        if filename.endswith(".py") and not filename.startswith("main"):
            await bot.load_extension(filename[:-3])
    print("Extensions loaded.")

async def main():
    async with bot:
        await load()
        await bot.start(token)

asyncio.run(main())
