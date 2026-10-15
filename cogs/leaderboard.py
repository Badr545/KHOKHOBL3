# =====================================================================
# ─── LEADERBOARD — Rank + Flous
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
from cogs.economy import ECONOMY
from cogs.levels import LEVELS


class Leaderboard(commands.Cog):
    """Leaderboard: flous + rank"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════════════════════════
    # ─── /topmoney
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="topmoney", description="Top 10 flous")
    async def topmoney(self, interaction: discord.Interaction):
        guild_data = ECONOMY.get(interaction.guild.id, {})
        if not guild_data:
            return await interaction.response.send_message("❌ Ma kaynch data!", ephemeral=True)

        sorted_users = sorted(
            guild_data.items(),
            key=lambda x: x[1].get("balance", 0) + x[1].get("bank", 0),
            reverse=True,
        )[:10]

        embed = discord.Embed(
            title="💰 **Top 10 — Flous**",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )
        medals = ["🥇", "🥈", "🥉"]
        for i, (user_id, data) in enumerate(sorted_users):
            try:
                user = await self.bot.fetch_user(user_id)
                name = user.name
            except Exception:
                name = f"User {user_id}"

            total = data.get("balance", 0) + data.get("bank", 0)
            prefix = medals[i] if i < 3 else f"`#{i+1}`"
            embed.add_field(
                name=f"{prefix} **{name}**",
                value=f"💵 `{total:,}` 🪙",
                inline=False,
            )
        embed.set_footer(text=f"Server: {interaction.guild.name}")
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /toprank
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="toprank", description="Top 10 rank")
    async def toprank(self, interaction: discord.Interaction):
        guild_data = LEVELS.get(interaction.guild.id, {})
        if not guild_data:
            return await interaction.response.send_message("❌ Ma kaynch data!", ephemeral=True)

        sorted_users = sorted(
            guild_data.items(),
            key=lambda x: (x[1].get("level", 0), x[1].get("xp", 0)),
            reverse=True,
        )[:10]

        embed = discord.Embed(
            title="📊 **Top 10 — Rank**",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )
        medals = ["🥇", "🥈", "🥉"]
        for i, (user_id, data) in enumerate(sorted_users):
            try:
                user = await self.bot.fetch_user(user_id)
                name = user.name
            except Exception:
                name = f"User {user_id}"

            prefix = medals[i] if i < 3 else f"`#{i+1}`"
            embed.add_field(
                name=f"{prefix} **{name}**",
                value=f"Level `{data.get('level', 0)}` — `{data.get('xp', 0):,}` XP",
                inline=False,
            )
        embed.set_footer(text=f"Server: {interaction.guild.name}")
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── PREFIX
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="topmoney")
    async def topmoney_prefix(self, ctx: commands.Context):
        """&topmoney"""
        guild_data = ECONOMY.get(ctx.guild.id, {})
        if not guild_data:
            return await ctx.send("❌ Ma kaynch data!")
        sorted_users = sorted(guild_data.items(), key=lambda x: x[1].get("balance", 0) + x[1].get("bank", 0), reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (user_id, data) in enumerate(sorted_users):
            try:
                user = await self.bot.fetch_user(user_id)
                name = user.name
            except Exception:
                name = f"User {user_id}"
            total = data.get("balance", 0) + data.get("bank", 0)
            prefix = medals[i] if i < 3 else f"#{i+1}"
            lines.append(f"{prefix} **{name}** — `{total:,}` 🪙")
        await ctx.send("💰 **Top 10 Flous:**\n" + "\n".join(lines))

    @commands.command(name="toprank")
    async def toprank_prefix(self, ctx: commands.Context):
        """&toprank"""
        guild_data = LEVELS.get(ctx.guild.id, {})
        if not guild_data:
            return await ctx.send("❌ Ma kaynch data!")
        sorted_users = sorted(guild_data.items(), key=lambda x: (x[1].get("level", 0), x[1].get("xp", 0)), reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (user_id, data) in enumerate(sorted_users):
            try:
                user = await self.bot.fetch_user(user_id)
                name = user.name
            except Exception:
                name = f"User {user_id}"
            prefix = medals[i] if i < 3 else f"#{i+1}"
            lines.append(f"{prefix} **{name}** — Lvl `{data.get('level', 0)}`")
        await ctx.send("📊 **Top 10 Rank:**\n" + "\n".join(lines))


async def setup(bot):
    await bot.add_cog(Leaderboard(bot))