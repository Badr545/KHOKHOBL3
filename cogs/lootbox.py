# cogs/lootbox.py
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import random
from database import SqliteStore
from database.engine import execute, commit
from data_manager import ECONOMY, save_economy

LOOT = SqliteStore("lootbox")
def _ensure():
    execute("""CREATE TABLE IF NOT EXISTS lootbox (
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (guild_id, user_id))""")
    commit()
_ensure()

TIERS = {
    "common":    {"price":500,    "min":100,   "max":800,    "win_chance":0.65, "emoji":"📦"},
    "rare":      {"price":5000,   "min":2000,  "max":15000,  "win_chance":0.55, "emoji":"🎁"},
    "epic":      {"price":25000,  "min":10000, "max":80000,  "win_chance":0.45, "emoji":"💎"},
    "legendary": {"price":100000, "min":50000, "max":400000, "win_chance":0.35, "emoji":"👑"},
}

class Lootbox(commands.Cog):
    """Lootbox system"""
    def __init__(self, bot):
        self.bot = bot

    def _get(self, gid, uid):
        LOOT.setdefault(gid, {}).setdefault(uid, {"last_daily":None,"opened":0,"total_won":0,"won":0})
        return LOOT[gid][uid]

    def _open(self, tier: str):
        t = TIERS[tier]
        if random.random() < t["win_chance"]:
            prize = random.randint(t["min"], t["max"])
            return True, prize
        return False, 0

    @app_commands.command(name="lootbox", description="📦 Buy + open lootbox")
    @app_commands.choices(tier=[
        app_commands.Choice(name="📦 Common (500)", value="common"),
        app_commands.Choice(name="🎁 Rare (5,000)", value="rare"),
        app_commands.Choice(name="💎 Epic (25,000)", value="epic"),
        app_commands.Choice(name="👑 Legendary (100,000)", value="legendary"),
    ])
    async def lootbox(self, it: discord.Interaction, tier: app_commands.Choice[str]):
        await self._play(it, it.user, tier.value, is_slash=True)

    @commands.command(name="lootbox", aliases=["lb2","box"])
    async def lootbox_prefix(self, ctx, tier: str = "common"):
        await self._play(ctx, ctx.author, tier.lower(), is_slash=False)

    async def _play(self, it_or_ctx, user, tier, is_slash):
        if tier not in TIERS:
            msg = f"❌ Tiers: `{', '.join(TIERS.keys())}`"
            return await (it_or_ctx.response.send_message(msg, ephemeral=True) if is_slash else it_or_ctx.send(msg))
        t = TIERS[tier]
        eco = ECONOMY.setdefault(it_or_ctx.guild.id, {}).setdefault(user.id, {"balance":0,"bank":0,"inventory":[]})
        if eco["balance"] < t["price"]:
            msg = f"❌ Khass `{t['price']:,}` 🪙!"
            return await (it_or_ctx.response.send_message(msg, ephemeral=True) if is_slash else it_or_ctx.send(msg))

        eco["balance"] -= t["price"]
        won, prize = self._open(tier)
        if won:
            eco["balance"] += prize
        save_economy()

        d = self._get(it_or_ctx.guild.id, user.id)
        d["opened"] += 1
        if won:
            d["won"] += 1
            d["total_won"] += prize
        LOOT.mark_dirty(it_or_ctx.guild.id)

        if won:
            net = prize - t["price"]
            embed = discord.Embed(title=f"{t['emoji']} **WIN!**", description=f"Rb7ti `{prize:,}` 🪙!\nNet: `{net:+,}` 🪙", color=discord.Color.green())
        else:
            embed = discord.Embed(title=f"{t['emoji']} **Empty!**", description=f"Khserti `{t['price']:,}` 🪙 😢", color=discord.Color.red())
        embed.set_footer(text=f"Opened: {d['opened']} | Won: {d['won']} ({d['won']/d['opened']*100:.0f}%)")
        if is_slash: await it_or_ctx.response.send_message(embed=embed)
        else: await it_or_ctx.send(embed=embed)

    @app_commands.command(name="lootdaily", description="🎁 Free daily lootbox")
    async def lootdaily(self, it: discord.Interaction):
        d = self._get(it.guild.id, it.user.id)
        if d["last_daily"]:
            last = datetime.fromisoformat(d["last_daily"])
            if datetime.now() - last < timedelta(hours=24):
                rem = timedelta(hours=24) - (datetime.now() - last)
                return await it.response.send_message(f"⏰ 3awed mn ba3d `{rem.seconds//3600}h {(rem.seconds%3600)//60}m`!", ephemeral=True)
        d["last_daily"] = datetime.now().isoformat()
        prize = random.randint(500, 5000)
        eco = ECONOMY.setdefault(it.guild.id, {}).setdefault(it.user.id, {"balance":0,"bank":0,"inventory":[]})
        eco["balance"] += prize
        save_economy()
        LOOT.mark_dirty(it.guild.id)
        embed = discord.Embed(title="🎁 Free Lootbox!", description=f"**+{prize:,}** 🪙!", color=discord.Color.green())
        await it.response.send_message(embed=embed)

    @commands.command(name="lootdaily")
    async def lootdaily_prefix(self, ctx):
        d = self._get(ctx.guild.id, ctx.author.id)
        if d["last_daily"]:
            last = datetime.fromisoformat(d["last_daily"])
            if datetime.now() - last < timedelta(hours=24):
                rem = timedelta(hours=24) - (datetime.now() - last)
                return await ctx.send(f"⏰ 3awed mn ba3d `{rem.seconds//3600}h {(rem.seconds%3600)//60}m`!")
        d["last_daily"] = datetime.now().isoformat()
        prize = random.randint(500, 5000)
        eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(ctx.author.id, {"balance":0,"bank":0,"inventory":[]})
        eco["balance"] += prize
        save_economy()
        LOOT.mark_dirty(ctx.guild.id)
        await ctx.send(f"🎁 **Free Lootbox!** +`{prize:,}` 🪙!")

    @commands.command(name="lootstats")
    async def lootstats(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        d = self._get(ctx.guild.id, member.id)
        embed = discord.Embed(title=f"📦 {member.display_name}", color=discord.Color.purple())
        embed.add_field(name="Opened", value=f"`{d['opened']}`", inline=True)
        embed.add_field(name="Won", value=f"`{d['won']}`", inline=True)
        embed.add_field(name="Total won", value=f"`{d['total_won']:,}` 🪙", inline=True)
        await ctx.send(embed=embed)

async def setup(bot): await bot.add_cog(Lootbox(bot))