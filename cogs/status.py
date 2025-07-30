import discord
from discord.ext import commands
from discord import app_commands

class GreetStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_owner_id = 489197156436148245  # ← حط هنا ID صاحب البوت

    @app_commands.command(name="setstatus", description="تغيير حالة البوت (مشاهدة، لعب، استماع)")
    async def set_status(self, interaction: discord.Interaction,
                         الحالة: str,
                         النص: str):
        if interaction.user.id != self.bot_owner_id:
            return await interaction.response.send_message("❌ هذا الأمر فقط لصاحب البوت.", ephemeral=True)

        الحالة = الحالة.lower()
        if الحالة == "watching":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=النص))
        elif الحالة == "playing":
            await self.bot.change_presence(activity=discord.Game(name=النص))
        elif الحالة == "listening":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=النص))
        else:
            return await interaction.response.send_message("❌ الحالة يجب أن تكون: watching أو playing أو listening", ephemeral=True)

        await interaction.response.send_message(f"✅ تم تغيير حالة البوت إلى `{الحالة}`: {النص}", ephemeral=True)

    @set_status.autocomplete('الحالة')
    async def status_autocomplete(self, interaction: discord.Interaction, current: str):
        الحالات = ['watching', 'playing', 'listening']
        return [app_commands.Choice(name=h, value=h) for h in الحالات if h.startswith(current.lower())]

async def setup(bot):
    await bot.add_cog(GreetStatus(bot))
