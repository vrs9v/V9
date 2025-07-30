from discord import app_commands
from discord.ext import commands
import discord
import json
import os
from utils.parser import parse_placeholders
from discord.ui import Modal, TextInput
from utils.webhook_utils import send_welcome_via_webhook


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/welcome_settings.json"

class WelcomeMessageModal(Modal):
    def __init__(self, bot, interaction, current_message):
        super().__init__(title="تعديل رسالة الترحيب")

        self.bot = bot
        self.interaction = interaction

        # حقل نص رسالة الإيمبد، نملأه بالرسالة القديمة
        self.embed_message = TextInput(
            label="نص رسالة الترحيب (الإيمبد)",
            style=discord.TextStyle.paragraph,
            default=current_message or "",
            required=True,
            max_length=1000
        )
        self.add_item(self.embed_message)

    async def on_submit(self, interaction: discord.Interaction):
        # تحميل البيانات الحالية
        cog: Welcome = self.bot.get_cog("Welcome")
        data = cog.load_data()

        guild_id = str(interaction.guild.id)
        if guild_id not in data:
            await interaction.response.send_message("❌ لا يوجد إعداد ترحيب محفوظ.", ephemeral=True)
            return

        # تحديث رسالة الإيمبد فقط (تقدر توسعها لتعديل باقي الإعدادات)
        data[guild_id]["embed_message"] = self.embed_message.value
        cog.save_data(data)

        await interaction.response.send_message("✅ تم تحديث رسالة الترحيب بنجاح.", ephemeral=True)


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/welcome_settings.json"
        if not os.path.exists(self.data_file):
            with open(self.data_file, "w") as f:
                json.dump({}, f, indent=4)

    def load_data(self):
        with open(self.data_file, "r") as f:
            return json.load(f)

    def save_data(self, data):
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=4)

    def has_welcome_config(self, guild_id: int):
        data = self.load_data()
        return str(guild_id) in data
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        data = self.load_data()
        settings = data.get(str(member.guild.id))
        if not settings:
            return

        webhook_url = settings.get("webhook_url")
        if not webhook_url:
            return

        embed = discord.Embed(
            description=parse_placeholders(settings["embed_message"], member),
            color=int(settings.get("embed_color", "#1c5d64").replace("#", "0x"), 16)
        )
        embed.set_footer(
            text="V9 system bot",
            icon_url=member.guild.me.display_avatar.url
        )

        sender_name = settings.get("sender_name")
        sender_avatar = settings.get("sender_avatar")

        if sender_name or sender_avatar:
            embed.set_author(
                name=parse_placeholders(sender_name, member) if sender_name else None,
                icon_url=sender_avatar if sender_avatar else None
            )

        if settings.get("embed_image"):
            embed.set_image(url=settings["embed_image"])
        if settings.get("embed_thumbnail"):
            embed.set_thumbnail(url=settings["embed_thumbnail"])

        content = parse_placeholders(settings.get("content_message", ""), member)
        await send_welcome_via_webhook(webhook_url, content=content, embed=embed)

    # أمر set_welcome مع تقييد الاستخدام مرة واحدة فقط
    @app_commands.command(name="set_welcome", description="إعداد رسالة الترحيب")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        channel="قناة الترحيب",
        embed_message="نص رسالة الإيمبد",
        embed_color="لون الإيمبد (Hex)",
        sender_name="اسم المرسل في الإيمبد",
        sender_avatar="رفع صورة للمرسل أو رابط صورة",
        embed_image="رفع صورة في الإيمبد",
        embed_thumbnail="رفع صورة مصغرة في الإيمبد",
        content_message="نص الرسالة العادية (خارج الإيمبد)"
    )
    async def set_welcome(self, interaction: discord.Interaction,
                          channel: discord.TextChannel,
                          embed_message: str,
                          embed_color: str = None,
                          sender_name: str = None,
                          sender_avatar: discord.Attachment = None,
                          embed_image: discord.Attachment = None,
                          embed_thumbnail: discord.Attachment = None,
                          content_message: str = None):

        if self.has_welcome_config(interaction.guild.id):
            await interaction.response.send_message(
                "❌ تم إعداد رسالة الترحيب مسبقًا. استخدم أمر delwelcome لحذف الإعداد أولاً.",
                ephemeral=True
            )
            return

        if not embed_message:
            await interaction.response.send_message("❌ يجب تحديد رسالة الإيمبد.", ephemeral=True)
            return

        sender_avatar_final = sender_avatar.url if sender_avatar else None
        embed_image_final = embed_image.url if embed_image else None
        embed_thumbnail_final = embed_thumbnail.url if embed_thumbnail else None

        settings = {
            "channel_id": channel.id,
            "embed_message": embed_message,
            "embed_color": embed_color or "#1c5d64",
            "sender_name": sender_name,
            "sender_avatar": sender_avatar_final,
            "embed_image": embed_image_final,
            "embed_thumbnail": embed_thumbnail_final,
            "content_message": content_message
        }

        data = self.load_data()
        data[str(interaction.guild.id)] = settings
        self.save_data(data)

        await interaction.response.send_message("✅ تم حفظ إعدادات الترحيب بنجاح.", ephemeral=True)

    # أمر test_welcome لإرسال رسالة الترحيب في نفس القناة لاختبارها
    @app_commands.command(name="test_welcome", description="يرسل رسالة الترحيب للتجربة")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def test_welcome(self, interaction: discord.Interaction):
        data = self.load_data()
        settings = data.get(str(interaction.guild.id))
        if not settings:
            await interaction.response.send_message("❌ لم يتم إعداد رسالة الترحيب بعد.", ephemeral=True)
            return

        embed = discord.Embed(
            description=parse_placeholders(settings["embed_message"], interaction.user),
            color=int(settings.get("embed_color", "#1c5d64").replace("#", "0x"), 16)
        )
        embed.set_footer(
            text="V9 system bot",
            icon_url=interaction.guild.me.display_avatar.url
        )

        if settings.get("sender_name"):
            embed.set_author(
                name=parse_placeholders(settings["sender_name"], interaction.user),
                icon_url=settings.get("sender_avatar") or interaction.guild.me.display_avatar.url
            )
        else:
            embed.set_author(
                name=self.bot.user.name,
                icon_url=self.bot.user.display_avatar.url
            )

        if settings.get("embed_image"):
            embed.set_image(url=settings["embed_image"])
        if settings.get("embed_thumbnail"):
            embed.set_thumbnail(url=settings["embed_thumbnail"])

        content = parse_placeholders(settings.get("content_message", ""), interaction.user)

        webhook_url = settings.get("webhook_url")

        if webhook_url:
            await send_welcome_via_webhook(webhook_url, content=content or None, embed=embed)
            await interaction.response.send_message("✅ تم إرسال رسالة الترحيب عبر الويبهوك.", ephemeral=True)
        else:
            await interaction.response.send_message(content or None, embed=embed)

    # أمر delwelcome لحذف إعداد الترحيب
    @app_commands.command(name="delwelcome", description="حذف إعداد رسالة الترحيب للسيرفر")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def delwelcome(self, interaction: discord.Interaction):
        data = self.load_data()
        if str(interaction.guild.id) not in data:
            await interaction.response.send_message("❌ لا يوجد إعداد ترحيب محفوظ لتحذفه.", ephemeral=True)
            return

        data.pop(str(interaction.guild.id))
        self.save_data(data)
        await interaction.response.send_message("✅ تم حذف إعداد الترحيب بنجاح.", ephemeral=True)

    # أمر help لإرسال رسالة مخصصة مخفية
    @app_commands.command(name="help", description="عرض المساعدة")
    async def help(self, interaction: discord.Interaction):
        help_message = (
            "لتواصل مع الدعم أو لمعرفة أحدث البوتات وإضافات البوتات، انضم إلى سيرفر البوت:\n"
            "https://discord.gg/X4HWdgVNYw"
        )

        await interaction.response.send_message(help_message, ephemeral=True)

    @app_commands.command(name="invite", description="ارسل رابط دعوة البوت لسيرفرك")
    async def invite(self, interaction: discord.Interaction):
        invite_link = (
            f"https://discord.com/oauth2/authorize?"
            f"client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands"
        )
        await interaction.response.send_message(
            f"🚀 تقدر تضيفني لسيرفرك من هنا:\n{invite_link}",
            ephemeral=True
        )

    @app_commands.command(name="welcome_message", description="تعديل رسالة الترحيب (الإيمبد) عبر مودال")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def welcome_message(self, interaction: discord.Interaction):
        data = self.load_data()
        current_message = data.get(str(interaction.guild.id), {}).get("embed_message", "")

        modal = WelcomeMessageModal(self.bot, interaction, current_message)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="set_welcome_webhook", description="تعيين رابط Webhook رسالة الترحيب")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def set_welcome_webhook(self, interaction: discord.Interaction, webhook_url: str):
        data = self.load_data()
        guild_id = str(interaction.guild.id)
        if guild_id not in data:
            data[guild_id] = {}

        data[guild_id]["webhook_url"] = webhook_url
        self.save_data(data)
        await interaction.response.send_message("✅ تم تعيين رابط الويبهوك للسيرفر.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
