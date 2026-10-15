# cogs/quests.py
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import random
from database import SqliteStore
from database.engine import execute, commit
from data_manager import ECONOMY, save_economy

QUESTS = SqliteStore("quests")
def _ensure():
    execute("""CREATE TABLE IF NOT EXISTS quests (
        guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (guild_id, user_id))""")
    commit()
_ensure()

DAILY_POOL = [
    {"type":"messages","goal":50,"reward":1000,"desc":"Send 50 messages"},
    {"type":"messages","goal":100,"reward":2000,"desc":"Send 100 messages"},
    {"type":"casino","goal":5,"reward":1500,"desc":"Play 5 casino games"},
    {"type":"casino","goal":10,"reward":3000,"desc":"Play 10 casino games"},
    {"type":"work","goal":3,"reward":1200,"desc":"Use /work 3 times"},
    {"type":"daily","goal":1,"reward":800,"desc":"Claim daily"},
    {"type":"rob","goal":1,"reward":2000,"desc":"Rob 1 user"},
    {"type":"collect","goal":2,"reward":1500,"desc":"Collect income 2 times"},
]
WEEKLY_POOL = [
    {"type":"messages","goal":500,"reward":15000,"desc":"Send 500 messages"},
    {"type":"casino","goal":50,"reward":20000,"desc":"Play 50 casino games"},
    {"type":"work","goal":30,"reward":10000,"desc":"Use /work 30 times"},
    {"type":"rob","goal":5,"reward":10000,"desc":"Rob 5 users successfully"},
    {"type":"daily","goal":7,"reward":25000,"desc":"Claim daily 7 times"},
]

def _roll_daily():
    return random.sample(DAILY_POOL, 3)
def _roll_weekly():
    return random.sample(WEEKLY_POOL, 3)

def _today(): return datetime.now().strftime("%Y-%m-%d")
def _week(): 
    d = datetime.now()
    return f"{d.year}-W{d.isocalendar()[1]}"

class Quests(commands.Cog):
    """Daily + weekly quests"""
    def __init__(self, bot):
        self.bot = bot

    def _get(self, gid, uid):
        QUESTS.setdefault(gid, {}).setdefault(uid, {"daily":None,"weekly":None})
        return QUESTS[gid][uid]

    def _refresh(self, d):
        t, w = _today(), _week()
        if not d["daily"] or d["daily"].get("date") != t:
            quests = _roll_daily()
            d["daily"] = {"date":t, "quests":[{"id":i,"type":q["type"],"goal":q["goal"],"progress":0,"reward":q["reward"],"desc":q["desc"],"claimed":False} for i,q in enumerate(quests)]}
        if not d["weekly"] or d["weekly"].get("date") != w:
            quests = _roll_weekly()
            d["weekly"] = {"date":w, "quests":[{"id":i,"type":q["type"],"goal":q["goal"],"progress":0,"reward":q["reward"],"desc":q["desc"],"claimed":False} for i,q in enumerate(quests)]}

    def progress(self, gid, uid, qtype, amount=1):
        d = self._get(gid, uid)
        self._refresh(d)
        for key in ("daily","weekly"):
            for q in d[key]["quests"]:
                if q["type"] == qtype and not q["claimed"]:
                    q["progress"] = min(q["goal"], q["progress"] + amount)
        QUESTS.mark_dirty(gid)

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot or not msg.guild: return
        if len(msg.content) < 5: return
        self.progress(msg.guild.id, msg.author.id, "messages", 1)

    @app_commands.command(name="quests", description="📋 Chouf quests dyalk")
    @app_commands.choices(type=[
        app_commands.Choice(name="Daily", value="daily"),
        app_commands.Choice(name="Weekly", value="weekly"),
    ])
    async def quests(self, it: discord.Interaction, type: app_commands.Choice[str] = None):
        t = (type.value if type else "daily")
        d = self._get(it.guild.id, it.user.id)
        self._refresh(d)
        data = d[t]
        embed = discord.Embed(title=f"📋 {t.title()} Quests", color=discord.Color.green())
        for q in data["quests"]:
            bar = "█" * int(q["progress"]/q["goal"]*15) + "░" * (15 - int(q["progress"]/q["goal"]*15))
            status = "✅" if q["claimed"] else ("🎁" if q["progress"] >= q["goal"] else "🔒")
            embed.add_field(
                name=f"{status} #{q['id']} — {q['desc']}",
                value=f"`{bar}` `{q['progress']}/{q['goal']}` → `{q['reward']:,}` 🪙",
                inline=False,
            )
        embed.set_footer(text=f"Use /questclaim {t} <id>")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="questclaim", description="🎁 Claim quest reward")
    @app_commands.choices(type=[
        app_commands.Choice(name="Daily", value="daily"),
        app_commands.Choice(name="Weekly", value="weekly"),
    ])
    async def questclaim(self, it: discord.Interaction, type: app_commands.Choice[str], quest_id: int):
        d = self._get(it.guild.id, it.user.id)
        self._refresh(d)
        t = type.value
        if quest_id < 0 or quest_id >= len(d[t]["quests"]):
            return await it.response.send_message("❌ ID ghalat!", ephemeral=True)
        q = d[t]["quests"][quest_id]
        if q["claimed"]:
            return await it.response.send_message("❌ Deja claimed!", ephemeral=True)
        if q["progress"] < q["goal"]:
            return await it.response.send_message(f"❌ Ba9i `{q['progress']}/{q['goal']}`!", ephemeral=True)

        q["claimed"] = True
        eco = ECONOMY.setdefault(it.guild.id, {}).setdefault(it.user.id, {"balance":0,"bank":0,"inventory":[]})
        eco["balance"] += q["reward"]
        save_economy()
        QUESTS.mark_dirty(it.guild.id)
        await it.response.send_message(f"🎁 **+{q['reward']:,}** 🪙! ({q['desc']})")

    @commands.command(name="quests")
    async def quests_prefix(self, ctx):
        """&quests — Chouf daily quests"""
        d = self._get(ctx.guild.id, ctx.author.id)
        self._refresh(d)
        lines = ["📋 **Daily Quests:**"]
        for q in d["daily"]["quests"]:
            st = "✅" if q["claimed"] else ("🎁" if q["progress"]>=q["goal"] else "🔒")
            lines.append(f"{st} `#{q['id']}` {q['desc']} — `{q['progress']}/{q['goal']}` → `{q['reward']:,}` 🪙")
        lines.append("\nUse `&questclaim <id>`")
        await ctx.send("\n".join(lines))

    @commands.command(name="questclaim")
    async def questclaim_prefix(self, ctx, quest_id: int, t: str = "daily"):
        """&questclaim <id> [daily|weekly]"""
        d = self._get(ctx.guild.id, ctx.author.id)
        self._refresh(d)
        t = t.lower()
        if t not in ("daily","weekly"):
            return await ctx.send("❌ `daily` wla `weekly`!")
        if quest_id < 0 or quest_id >= len(d[t]["quests"]):
            return await ctx.send("❌ ID ghalat!")
        q = d[t]["quests"][quest_id]
        if q["claimed"]: return await ctx.send("❌ Deja claimed!")
        if q["progress"] < q["goal"]:
            return await ctx.send(f"❌ Ba9i `{q['progress']}/{q['goal']}`!")
        q["claimed"] = True
        eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(ctx.author.id, {"balance":0,"bank":0,"inventory":[]})
        eco["balance"] += q["reward"]
        save_economy()
        QUESTS.mark_dirty(ctx.guild.id)
        await ctx.send(f"🎁 **+{q['reward']:,}** 🪙!")

    @commands.command(name="questweekly")
    async def questweekly_prefix(self, ctx):
        """&questweekly — Weekly quests"""
        d = self._get(ctx.guild.id, ctx.author.id)
        self._refresh(d)
        lines = ["📋 **Weekly Quests:**"]
        for q in d["weekly"]["quests"]:
            st = "✅" if q["claimed"] else ("🎁" if q["progress"]>=q["goal"] else "🔒")
            lines.append(f"{st} `#{q['id']}` {q['desc']} — `{q['progress']}/{q['goal']}` → `{q['reward']:,}` 🪙")
        lines.append("\nUse `&questclaim <id> weekly`")
        await ctx.send("\n".join(lines))

async def setup(bot): await bot.add_cog(Quests(bot))