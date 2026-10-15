# cogs/spy.py
import discord
from discord.ext import commands
from database import SqliteStore
from database.engine import execute, commit
from data_manager import ECONOMY, save_economy, LEVELS, BIR

SPY = SqliteStore("spy")
def _ensure():
    execute("""CREATE TABLE IF NOT EXISTS spy (
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (guild_id, user_id))""")
    commit()
_ensure()

SPY_COST = 500

class Spy(commands.Cog):
    """Spy system — chouf wallet/info dyal users"""
    def __init__(self, bot):
        self.bot = bot

    def _get(self, gid, uid):
        SPY.setdefault(gid, {}).setdefault(uid, {"count":0, "last_target":None})
        return SPY[gid][uid]

    @commands.command(name="spy")
    async def spy(self, ctx, member: discord.Member):
        if member.bot or member.id == ctx.author.id:
            return await ctx.send("❌ Ghir @user!")
        eco_self = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(ctx.author.id, {"balance":0,"bank":0,"inventory":[]})
        if eco_self["balance"] < SPY_COST:
            return await ctx.send(f"❌ Khass `{SPY_COST:,}` 🪙!")
        eco_self["balance"] -= SPY_COST
        save_economy()

        d = self._get(ctx.guild.id, ctx.author.id)
        d["count"] += 1
        d["last_target"] = member.id
        SPY.mark_dirty(ctx.guild.id)

        target_eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(member.id, {"balance":0,"bank":0,"inventory":[]})
        target_lvl = LEVELS.get(ctx.guild.id, {}).get(member.id, {"level":0,"xp":0})
        target_bir = BIR.get(ctx.guild.id, {}).get(member.id, {"bir":0})

        embed = discord.Embed(title=f"🕵️ Spy — {member.display_name}", color=discord.Color.dark_green())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👛 Wallet", value=f"`{target_eco.get('balance',0):,}` 🪙", inline=True)
        embed.add_field(name="🏦 Bank", value=f"`{target_eco.get('bank',0):,}` 🪙", inline=True)
        embed.add_field(name="📊 Level", value=f"`{target_lvl.get('level',0)}`", inline=True)
        embed.add_field(name="🔮 Bir", value=f"`{target_bir.get('bir',0):,}`", inline=True)
        embed.add_field(name="🎒 Inventory", value=f"`{len(target_eco.get('inventory',[]))}` items", inline=True)
        embed.set_footer(text=f"Cost: {SPY_COST:,} 🪙 • Spied by {ctx.author.name}")
        await ctx.send(embed=embed)

    @commands.command(name="steal-info")
    async def steal_info(self, ctx, member: discord.Member):
        """Reveal target inventory (costs 2000)"""
        if member.bot or member.id == ctx.author.id:
            return await ctx.send("❌ Ghir @user!")
        eco_self = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(ctx.author.id, {"balance":0,"bank":0,"inventory":[]})
        if eco_self["balance"] < 2000:
            return await ctx.send("❌ Khass `2,000` 🪙!")
        eco_self["balance"] -= 2000
        save_economy()
        target = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(member.id, {"balance":0,"bank":0,"inventory":[]})
        inv = target.get("inventory", [])
        items = "\n".join(f"• `{i}`" for i in inv[:20]) or "*Khawi*"
        embed = discord.Embed(title=f"📦 {member.display_name}'s Inventory", description=items, color=discord.Color.dark_red())
        await ctx.send(embed=embed)

    @commands.command(name="spystats")
    async def spystats(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        d = self._get(ctx.guild.id, member.id)
        await ctx.send(f"🕵️ **{member.name}** — Spied: `{d['count']}` times")

async def setup(bot): await bot.add_cog(Spy(bot))