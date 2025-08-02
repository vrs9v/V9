import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()

class V9Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="9!", intents=intents)

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")
        try:
            await self.tree.sync()
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")

    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")

bot = V9Bot()
bot.run(os.getenv("DISCORD_TOKEN"))
