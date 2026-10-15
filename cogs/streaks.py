# cogs/streaks.py
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from database import SqliteStore
from database.engine import execute, commit
from data_manager import ECONOMY, save_economy

STREAKS = SqliteStore("streaks")

def _ensure():
    execute("""CREATE TABLE IF NOT EXISTS streaks (
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (guild_id, user_id))""")
    commit()
_ensure()

REWARDS = {1:500, 2:700, 3:1000, 4:1300, 5:1700, 6:2200, 7:3000,
           14:6000, 21:10000, 30:50000, 60:150000, 100:500000}

def _reward(s: int) -> int:
    if s in REWARDS: return REWARDS[s]
    return min(3000 + (s - 7) * 500, 40000)

class Streaks(commands.Cog):
    """Daily streaks system"""
    def __init__(self, bot):
        self.bot = bot

    def _get(self, gid, uid):
        STREAKS.setdefault(gid, {}).setdefault(uid, {"streak":0,"best":0,"last":None,"total":0})
        return STREAKS[gid][uid]

    def _can_claim(self, d):
        if not d["last"]: return True, 0
        last = datetime.fromisoformat(d["last"])
        diff = datetime.now() - last
        if diff < timedelta(hours=20):
            return False, int((timedelta(hours=20) - diff).total_seconds())
        if diff > timedelta(hours=48):
            d["streak"] = 0
        return True, 0

    async def _do_claim(self, it_or_ctx, member):
        gid = it_or_ctx.guild.id
        d = self._get(gid, member.id)
        ok, wait = self._can_claim(d)
        if not ok:
            h, m = wait // 3600, (wait % 3600) // 60
            msg = f"⏰ 3awed mn ba3d `{h}h {m}m`!"
            if hasattr(it_or_ctx, "response"):
                return await it_or_ctx.response.send_message(msg, ephemeral=True)
            return await it_or_ctx.send(msg)

        d["streak"] += 1
        d["best"] = max(d["best"], d["streak"])
        d["last"] = datetime.now().isoformat()
        reward = _reward(d["streak"])
        d["total"] += reward

        eco = ECONOMY.setdefault(gid, {}).setdefault(member.id, {"balance":0,"bank":0,"inventory":[]})
        eco["balance"] += reward
        save_economy()

        embed = discord.Embed(
            title="🔥 Streak Claim!",
            description=f"**Streak:** `{d['streak']}` 🔥\n**Reward:** `{reward:,}` 🪙",
            color=discord.Color.orange(),
        )
        embed.add_field(name="📈 Best", value=f"`{d['best']}`", inline=True)
        embed.add_field(name="💰 Total earned", value=f"`{d['total']:,}` 🪙", inline=True)
        nxt = _reward(d["streak"] + 1)
        embed.set_footer(text=f"Next: {nxt:,} 🪙")
        if hasattr(it_or_ctx, "response"):
            await it_or_ctx.response.send_message(embed=embed)
        else:
            await it_or_ctx.send(embed=embed)

    @app_commands.command(name="claim", description="🔥 Claim daily b streak bonus")
    async def claim(self, it: discord.Interaction):
        await self._do_claim(it, it.user)

    @commands.command(name="claim")
    async def claim_prefix(self, ctx):
        await self._do_claim(ctx, ctx.author)

    @app_commands.command(name="streak", description="Chouf streak dyalk")
    async def streak(self, it: discord.Interaction, member: discord.Member = None):
        member = member or it.user
        d = self._get(it.guild.id, member.id)
        embed = discord.Embed(title=f"🔥 {member.display_name}", color=discord.Color.orange())
        embed.add_field(name="Streak", value=f"`{d['streak']}`", inline=True)
        embed.add_field(name="Best", value=f"`{d['best']}`", inline=True)
        embed.add_field(name="Total earned", value=f"`{d['total']:,}` 🪙", inline=True)
        if d["streak"] > 0:
            embed.add_field(name="Next reward", value=f"`{_reward(d['streak']+1):,}` 🪙", inline=False)
        await it.response.send_message(embed=embed)

    @commands.command(name="streak")
    async def streak_prefix(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        d = self._get(ctx.guild.id, member.id)
        await ctx.send(f"🔥 **{member.name}** — Streak: `{d['streak']}` | Best: `{d['best']}` | Total: `{d['total']:,}` 🪙")

    @commands.command(name="streaktop", aliases=["stop"])
    async def streaktop(self, ctx):
        STREAKS.bulk_load_all()
        gd = STREAKS.get(ctx.guild.id, {})
        top = sorted(gd.items(), key=lambda x: x[1].get("streak",0), reverse=True)[:10]
        if not top: return await ctx.send("❌ Ma kaynch data!")
        lines = []
        medals = ["🥇","🥈","🥉"]
        for i,(uid,d) in enumerate(top):
            try: u = await self.bot.fetch_user(uid); n = u.name
            except: n = f"User {uid}"
            lines.append(f"{medals[i] if i<3 else f'#{i+1}'} **{n}** — 🔥 `{d.get('streak',0)}`")
        await ctx.send("🔥 **Top Streaks:**\n" + "\n".join(lines))

async def setup(bot): await bot.add_cog(Streaks(bot))