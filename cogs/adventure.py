# cogs/adventure.py
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random
from database import SqliteStore
from database.engine import execute, commit
from data_manager import ECONOMY, save_economy

ADV = SqliteStore("adventure")
def _ensure():
    execute("""CREATE TABLE IF NOT EXISTS adventure (
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (guild_id, user_id))""")
    commit()
_ensure()

MONSTERS = [
    {"name":"🐀 Rat","hp":30,"atk":5,"gold":200},
    {"name":"🐺 Wolf","hp":60,"atk":10,"gold":500},
    {"name":"🐗 Boar","hp":100,"atk":15,"gold":900},
    {"name":"🐉 Dragon","hp":300,"atk":40,"gold":5000},
    {"name":"👹 Ogre","hp":200,"atk":30,"gold":3000},
    {"name":"💀 Skeleton","hp":80,"atk":20,"gold":1200},
]

class Adventure(commands.Cog):
    """Simple dungeon adventure"""
    def __init__(self, bot): self.bot = bot

    def _get(self, gid, uid):
        ADV.setdefault(gid, {}).setdefault(uid, {"hp":100,"max_hp":100,"atk":15,"level":1,"xp":0,"gold":0,"monster":None,"kills":0})
        return ADV[gid][uid]

    @commands.group(name="adv", aliases=["adventure"], invoke_without_command=True)
    async def adv_group(self, ctx):
        d = self._get(ctx.guild.id, ctx.author.id)
        embed = discord.Embed(title="⚔️ Adventure", color=discord.Color.dark_red())
        embed.add_field(name="❤️ HP", value=f"`{d['hp']}/{d['max_hp']}`", inline=True)
        embed.add_field(name="⚔️ ATK", value=f"`{d['atk']}`", inline=True)
        embed.add_field(name="📊 Level", value=f"`{d['level']}`", inline=True)
        embed.add_field(name="🏆 Kills", value=f"`{d['kills']}`", inline=True)
        if d["monster"]:
            m = d["monster"]
            embed.add_field(name=f"👹 Fighting: {m['name']}", value=f"HP: `{m['hp']}/{m['max_hp']}`", inline=False)
        await ctx.send(embed=embed)

    @adv_group.command(name="start")
    async def start(self, ctx):
        d = self._get(ctx.guild.id, ctx.author.id)
        if d["monster"]:
            return await ctx.send("❌ Deja f combat!")
        if d["hp"] < 30:
            d["hp"] = d["max_hp"]
            await ctx.send("💊 Restored HP!")
        template = random.choice(MONSTERS)
        scale = 1 + d["level"] * 0.1
        m = {"name":template["name"], "hp":int(template["hp"]*scale), "max_hp":int(template["hp"]*scale),
             "atk":int(template["atk"]*scale), "gold":int(template["gold"]*scale)}
        d["monster"] = m
        ADV.mark_dirty(ctx.guild.id)
        await ctx.send(f"⚔️ Encountered **{m['name']}**!\nHP: `{m['hp']}/{m['max_hp']}` | ATK: `{m['atk']}`\n`&adv attack` bash thjjem")

    @adv_group.command(name="attack")
    async def attack(self, ctx):
        d = self._get(ctx.guild.id, ctx.author.id)
        if not d["monster"]: return await ctx.send("❌ Ma kaynch combat! `&adv start`")
        m = d["monster"]
        dmg = random.randint(d["atk"]//2, d["atk"])
        if random.random() < 0.2: dmg *= 2
        m["hp"] -= dmg
        msg = f"⚔️ Dert `{dmg}` damage! {m['name']} HP: `{m['hp']}/{m['max_hp']}`"
        if m["hp"] <= 0:
            d["kills"] += 1
            d["xp"] += 50
            d["gold"] += m["gold"]
            eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(ctx.author.id, {"balance":0,"bank":0,"inventory":[]})
            eco["balance"] += m["gold"]
            save_economy()
            if d["xp"] >= d["level"] * 100:
                d["level"] += 1
                d["atk"] += 5
                d["max_hp"] += 20
                d["hp"] = d["max_hp"]
                d["xp"] = 0
                msg += f"\n🎉 **LEVEL UP! → Lv{d['level']}**"
            msg += f"\n💰 +`{m['gold']:,}` 🪙"
            d["monster"] = None
        else:
            mdmg = random.randint(m["atk"]//2, m["atk"])
            d["hp"] = max(0, d["hp"] - mdmg)
            msg += f"\n💥 {m['name']} 3tak `{mdmg}` damage! HP: `{d['hp']}/{d['max_hp']}`"
            if d["hp"] <= 0:
                d["monster"] = None
                d["hp"] = d["max_hp"] // 2
                msg += "\n☠️ **Mtti!** Respawn m3a 50% HP"
        ADV.mark_dirty(ctx.guild.id)
        await ctx.send(msg)

    @adv_group.command(name="flee")
    async def flee(self, ctx):
        d = self._get(ctx.guild.id, ctx.author.id)
        if not d["monster"]: return await ctx.send("❌ Ma kaynch combat!")
        d["monster"] = None
        ADV.mark_dirty(ctx.guild.id)
        await ctx.send("🏃 Hrbti!")

    @adv_group.command(name="heal")
    async def heal(self, ctx):
        d = self._get(ctx.guild.id, ctx.author.id)
        cost = 500
        eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(ctx.author.id, {"balance":0,"bank":0,"inventory":[]})
        if eco["balance"] < cost: return await ctx.send("❌ Khass `500` 🪙!")
        eco["balance"] -= cost
        d["hp"] = d["max_hp"]
        save_economy()
        ADV.mark_dirty(ctx.guild.id)
        await ctx.send(f"💊 Restored kol HP! (-`{cost}` 🪙)")

async def setup(bot): await bot.add_cog(Adventure(bot))