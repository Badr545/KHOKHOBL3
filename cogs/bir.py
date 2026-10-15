# cogs/bir.py
# =====================================================================
# ─── BIR — Prefix Only (&bir, &bw, &bt)
# =====================================================================
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random

# ✅ FIX: Import mn data_manager (central)
from data_manager import BIR, save_bir as _save_bir


class Bir(commands.Cog):
    """Bir: prefix only"""

    def __init__(self, bot):
        self.bot = bot

    def _get_user(self, guild_id: int, user_id: int) -> dict:
        BIR.setdefault(guild_id, {}).setdefault(user_id, {
            "bir": 0, "last_bir": None, "total_earned": 0,
        })
        return BIR[guild_id][user_id]

    @commands.command(name="bir")
    async def bir_prefix(self, ctx: commands.Context, member: discord.Member = None):
        """&bir [@user]"""
        if member is None:
            member = ctx.author
        data = self._get_user(ctx.guild.id, member.id)

        embed = discord.Embed(
            title=f"🔮 Bir — {member.name}",
            description=(
                f"**Balance:** `{data['bir']:,}` 🔮\n"
                f"**Total earned:** `{data['total_earned']:,}` 🔮"
            ),
            color=discord.Color.from_rgb(138, 43, 226),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Bir machi transferable")
        await ctx.send(embed=embed)

    @commands.command(name="bw", aliases=["birwork"])
    async def bw_prefix(self, ctx: commands.Context):
        """&bw — Bir work"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        now = datetime.now()

        if data["last_bir"]:
            last = datetime.fromisoformat(data["last_bir"])
            if now - last < timedelta(hours=2):
                remaining = timedelta(hours=2) - (now - last)
                h = remaining.seconds // 3600
                m = (remaining.seconds % 3600) // 60
                return await ctx.send(f"⏰ 3awed mn ba3d `{h}h {m}m`!")

        amount = random.randint(5, 25)
        data["bir"] += amount
        data["total_earned"] += amount
        data["last_bir"] = now.isoformat()
        _save_bir()

        await ctx.send(f"🔮 **+{amount}** Bir!")

    @commands.command(name="bt", aliases=["birtop"])
    async def bt_prefix(self, ctx: commands.Context):
        """&bt — Bir top"""
        guild_data = BIR.get(ctx.guild.id, {})
        if not guild_data:
            return await ctx.send("❌ Ma kaynch data!")

        sorted_users = sorted(guild_data.items(), key=lambda x: x[1].get("bir", 0), reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (user_id, data) in enumerate(sorted_users):
            try:
                user = await self.bot.fetch_user(user_id)
                name = user.name
            except Exception:
                name = f"User {user_id}"
            prefix = medals[i] if i < 3 else f"#{i+1}"
            lines.append(f"{prefix} **{name}** — `{data.get('bir', 0):,}` 🔮")

        await ctx.send("🔮 **Top 10 Bir:**\n" + "\n".join(lines))


async def setup(bot):
    await bot.add_cog(Bir(bot))