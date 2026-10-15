# cogs/levels.py
# =====================================================================
# ─── LEVELS & XP SYSTEM
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timedelta

# ✅ FIX: Import mn data_manager
from data_manager import LEVELS, save_levels as _save_levels


# ═══════════════════════════════════════════════════════════════════
# ─── CONFIG
# ═══════════════════════════════════════════════════════════════════
XP_PER_MESSAGE = (15, 25)
XP_COOLDOWN = 60


def xp_for_level(level: int) -> int:
    return 5 * (level ** 2) + 50 * level + 100


class Levels(commands.Cog):
    """Levels: XP, Rank, Leaderboard"""

    def __init__(self, bot):
        self.bot = bot

    def _get_user(self, guild_id: int, user_id: int) -> dict:
        LEVELS.setdefault(guild_id, {}).setdefault(user_id, {
            "xp": 0, "level": 0, "messages": 0, "last_xp": None,
        })
        return LEVELS[guild_id][user_id]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        if len(message.content) < 5:
            return

        data = self._get_user(message.guild.id, message.author.id)
        now = datetime.now()

        if data["last_xp"]:
            last = datetime.fromisoformat(data["last_xp"])
            if now - last < timedelta(seconds=XP_COOLDOWN):
                return

        xp_gained = random.randint(*XP_PER_MESSAGE)
        data["xp"] += xp_gained
        data["messages"] += 1
        data["last_xp"] = now.isoformat()

        needed = xp_for_level(data["level"] + 1)
        if data["xp"] >= needed:
            data["level"] += 1
            try:
                embed = discord.Embed(
                    title="🎉 Level Up!",
                    description=f"{message.author.mention} wsel l **Level {data['level']}**! 🎊",
                    color=discord.Color.gold(),
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                await message.channel.send(embed=embed)
            except Exception:
                pass

        _save_levels()

    @app_commands.command(name="rank", description="Chouf l-rank dyalek")
    @app_commands.describe(member="L-user")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user
        data = self._get_user(interaction.guild.id, member.id)

        needed = xp_for_level(data["level"] + 1)
        progress = int((data["xp"] / needed) * 20) if needed else 0
        bar = "█" * progress + "░" * (20 - progress)

        embed = discord.Embed(
            title=f"📊 Rank — {member.name}",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🎯 Level", value=f"`{data['level']}`", inline=True)
        embed.add_field(name="✨ XP", value=f"`{data['xp']:,} / {needed:,}`", inline=True)
        embed.add_field(name="💬 Messages", value=f"`{data['messages']:,}`", inline=True)
        embed.add_field(name="📈 Progress", value=f"`{bar}`", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="levels", description="Top 10 levels")
    async def levels(self, interaction: discord.Interaction):
        guild_data = LEVELS.get(interaction.guild.id, {})
        if not guild_data:
            return await interaction.response.send_message("❌ Ma kaynch data!", ephemeral=True)

        sorted_users = sorted(guild_data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)[:10]

        embed = discord.Embed(title="🏆 Levels Leaderboard", color=discord.Color.gold())
        medals = ["🥇", "🥈", "🥉"]
        for i, (user_id, data) in enumerate(sorted_users):
            try:
                user = await self.bot.fetch_user(user_id)
                name = user.name
            except Exception:
                name = f"User {user_id}"
            prefix = medals[i] if i < 3 else f"`#{i+1}`"
            embed.add_field(
                name=f"{prefix} {name}",
                value=f"Level `{data['level']}` — `{data['xp']:,}` XP",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)

    @commands.command(name="rank")
    async def rank_prefix(self, ctx: commands.Context, member: discord.Member = None):
        """&rank [@user]"""
        if member is None:
            member = ctx.author
        data = self._get_user(ctx.guild.id, member.id)
        needed = xp_for_level(data["level"] + 1)
        await ctx.send(
            f"📊 **{member.name}** — Level `{data['level']}` | XP: `{data['xp']:,}/{needed:,}` | Messages: `{data['messages']:,}`"
        )

    @commands.command(name="levels")
    async def levels_prefix(self, ctx: commands.Context):
        """&levels"""
        guild_data = LEVELS.get(ctx.guild.id, {})
        if not guild_data:
            return await ctx.send("❌ Ma kaynch data!")
        sorted_users = sorted(guild_data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)[:10]
        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for i, (user_id, data) in enumerate(sorted_users):
            try:
                user = await self.bot.fetch_user(user_id)
                name = user.name
            except Exception:
                name = f"User {user_id}"
            prefix = medals[i] if i < 3 else f"#{i+1}"
            lines.append(f"{prefix} **{name}** — Lvl `{data['level']}`")
        await ctx.send("🏆 **Levels:**\n" + "\n".join(lines))


async def setup(bot):
    await bot.add_cog(Levels(bot))