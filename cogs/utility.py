# =====================================================================
# ─── UTILITY COMMANDS
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
import base64
import uuid as uuid_lib
import secrets
import string
from datetime import datetime


class Utility(commands.Cog):
    """Utility: math, base64, password, uuid, timestamp"""

    def __init__(self, bot):
        self.bot = bot

    # ─── /math
    @app_commands.command(name="math", description="7sab riyadi")
    async def math(self, interaction: discord.Interaction, expression: str):
        try:
            allowed = set("0123456789+-*/().% ")
            if not all(c in allowed for c in expression):
                return await interaction.response.send_message("❌ Ghir chiffres!", ephemeral=True)
            result = eval(expression, {"__builtins__": {}}, {})
            await interaction.response.send_message(f"🧮 `{expression}` = **{result}**")
        except Exception as e:
            await interaction.response.send_message(f"❌ `{e}`", ephemeral=True)

    # ─── /base64
    @app_commands.command(name="base64", description="Encode/Decode base64")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Encode", value="encode"),
        app_commands.Choice(name="Decode", value="decode"),
    ])
    async def base64_cmd(self, interaction: discord.Interaction, text: str, mode: app_commands.Choice[str]):
        try:
            if mode.value == "encode":
                result = base64.b64encode(text.encode()).decode()
            else:
                result = base64.b64decode(text.encode()).decode()
            await interaction.response.send_message(f"🔐 **{mode.value.title()}:** `{result}`")
        except Exception as e:
            await interaction.response.send_message(f"❌ `{e}`", ephemeral=True)

    # ─── /password
    @app_commands.command(name="password", description="Password qwi")
    async def password(self, interaction: discord.Interaction, length: app_commands.Range[int, 8, 64] = 16):
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        await interaction.response.send_message(f"🔑 `{pwd}`", ephemeral=True)

    # ─── /uuid
    @app_commands.command(name="uuid", description="Générer UUID")
    async def uuid_cmd(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🆔 `{uuid_lib.uuid4()}`", ephemeral=True)

    # ─── /timestamp
    @app_commands.command(name="timestamp", description="Discord timestamp")
    async def timestamp(self, interaction: discord.Interaction, datetime_str: str):
        try:
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            ts = int(dt.timestamp())
            formats = {
                "Short Time": f"<t:{ts}:t>",
                "Long Time": f"<t:{ts}:T>",
                "Short Date": f"<t:{ts}:d>",
                "Long Date": f"<t:{ts}:D>",
                "Full": f"<t:{ts}:f>",
                "Relative": f"<t:{ts}:R>",
            }
            embed = discord.Embed(title="🕐 Timestamps", color=discord.Color.green())
            for name, val in formats.items():
                embed.add_field(name=name, value=f"`{val}`\n{val}", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Format `YYYY-MM-DD HH:MM`\n`{e}`", ephemeral=True)

    # ═══════════════ PREFIX COMMANDS ═══════════════

    @commands.command(name="math")
    async def math_prefix(self, ctx: commands.Context, *, expression: str):
        """&math <expression>"""
        try:
            allowed = set("0123456789+-*/().% ")
            if not all(c in allowed for c in expression):
                return await ctx.send("❌ Ghir chiffres!")
            result = eval(expression, {"__builtins__": {}}, {})
            await ctx.send(f"🧮 `{expression}` = **{result}**")
        except Exception as e:
            await ctx.send(f"❌ `{e}`")

    @commands.command(name="base64")
    async def base64_prefix(self, ctx: commands.Context, mode: str, *, text: str):
        """&base64 <encode|decode> <text>"""
        try:
            if mode.lower() == "encode":
                result = base64.b64encode(text.encode()).decode()
            elif mode.lower() == "decode":
                result = base64.b64decode(text.encode()).decode()
            else:
                return await ctx.send("❌ `encode` wla `decode`")
            await ctx.send(f"🔐 **{mode.title()}:** `{result}`")
        except Exception as e:
            await ctx.send(f"❌ `{e}`")

    @commands.command(name="password")
    async def password_prefix(self, ctx: commands.Context, length: int = 16):
        """&password [length]"""
        if length < 8 or length > 64:
            return await ctx.send("❌ 8-64!")
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        try:
            await ctx.author.send(f"🔑 `{pwd}`")
            await ctx.send("✅ Siftt lik f DM!")
        except discord.Forbidden:
            await ctx.send("❌ Ftah DM dyalk!")

    @commands.command(name="uuid")
    async def uuid_prefix(self, ctx: commands.Context):
        """&uuid"""
        await ctx.send(f"🆔 `{uuid_lib.uuid4()}`")

    @commands.command(name="timestamp")
    async def timestamp_prefix(self, ctx: commands.Context, date: str, time: str):
        """&timestamp <YYYY-MM-DD> <HH:MM>"""
        try:
            dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            ts = int(dt.timestamp())
            await ctx.send(f"`<t:{ts}:f>` → <t:{ts}:f>\n`<t:{ts}:R>` → <t:{ts}:R>")
        except Exception as e:
            await ctx.send(f"❌ `{e}`")


async def setup(bot):
    await bot.add_cog(Utility(bot))