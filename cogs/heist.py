# cogs/heist.py
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from datetime import datetime
import random
from database import KVStore
from database.engine import execute, commit
from data_manager import ECONOMY, save_economy

HEIST = KVStore("heist", {})  # {guild_id: heist_data}

class Heist(commands.Cog):
    """Heist — team-based bank robbery"""
    def __init__(self, bot):
        self.bot = bot

    def _get_heist(self, gid):
        h = HEIST.get(str(gid))
        return h

    def _set_heist(self, gid, data):
        HEIST[str(gid)] = data
        HEIST.mark_dirty()

    @commands.group(name="heist", invoke_without_command=True)
    async def heist_group(self, ctx):
        h = self._get_heist(ctx.guild.id)
        if not h:
            return await ctx.send("❌ Ma kaynch heist! `&heist start <amount>`")
        embed = discord.Embed(title="🏴‍☠️ Active Heist", color=discord.Color.dark_red())
        embed.add_field(name="Host", value=f"<@{h['host']}>", inline=True)
        embed.add_field(name="Entry", value=f"`{h['amount']:,}` 🪙", inline=True)
        embed.add_field(name="Players", value=f"`{len(h['players'])}/{h['max']}`", inline=True)
        embed.add_field(name="Potential pot", value=f"`{h['amount'] * len(h['players']) * 3:,}` 🪙", inline=False)
        members = "\n".join(f"<@{p}>" for p in h["players"])
        embed.add_field(name="🚨 Team", value=members or "—", inline=False)
        embed.set_footer(text="Host: &heist go")
        await ctx.send(embed=embed)

    @heist_group.command(name="start")
    async def start(self, ctx, amount: int):
        if amount < 1000:
            return await ctx.send("❌ Minimum `1,000` 🪙")
        if self._get_heist(ctx.guild.id):
            return await ctx.send("❌ Deja kayn heist!")
        eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(ctx.author.id, {"balance":0,"bank":0,"inventory":[]})
        if eco["balance"] < amount:
            return await ctx.send(f"❌ Khass `{amount:,}` 🪙!")
        eco["balance"] -= amount
        save_economy()
        self._set_heist(ctx.guild.id, {
            "host": ctx.author.id, "amount": amount,
            "players": [ctx.author.id], "max": 10, "started_at": datetime.now().isoformat(),
        })
        await ctx.send(f"🏴‍☠️ **Heist bda!** Entry: `{amount:,}` 🪙\n`&heist join` bash tdkhol!\nHost: `&heist go`")

    @heist_group.command(name="join")
    async def join(self, ctx):
        h = self._get_heist(ctx.guild.id)
        if not h: return await ctx.send("❌ Ma kaynch heist!")
        if ctx.author.id in h["players"]:
            return await ctx.send("❌ Deja fih!")
        if len(h["players"]) >= h["max"]:
            return await ctx.send("❌ 3amer!")
        eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(ctx.author.id, {"balance":0,"bank":0,"inventory":[]})
        if eco["balance"] < h["amount"]:
            return await ctx.send(f"❌ Khass `{h['amount']:,}` 🪙!")
        eco["balance"] -= h["amount"]
        save_economy()
        h["players"].append(ctx.author.id)
        self._set_heist(ctx.guild.id, h)
        await ctx.send(f"✅ Dkhelti! `{len(h['players'])}/{h['max']}`")

    @heist_group.command(name="go")
    async def go(self, ctx):
        h = self._get_heist(ctx.guild.id)
        if not h or h["host"] != ctx.author.id:
            return await ctx.send("❌ Ghir host!")
        if len(h["players"]) < 3:
            return await ctx.send("❌ Khass 3+ players!")
        total_pot = h["amount"] * len(h["players"])
        success_chance = min(0.75, 0.3 + len(h["players"]) * 0.08)
        roll = random.random()
        if roll < success_chance:
            multiplier = random.uniform(2.0, 3.5)
            share = int(total_pot * multiplier / len(h["players"]))
            for uid in h["players"]:
                eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(uid, {"balance":0,"bank":0,"inventory":[]})
                eco["balance"] += share
            save_economy()
            await ctx.send(f"🎉 **HEIST SUCCESS!**\n💰 Kol wa7ed rb7 `{share:,}` 🪙 (`{multiplier:.1f}x`)")
        else:
            await ctx.send(f"🚨 **HEIST FAILED!**\nL-policier qbadkom! Kolchi khser entry.")
        self._set_heist(ctx.guild.id, None)

async def setup(bot): await bot.add_cog(Heist(bot))