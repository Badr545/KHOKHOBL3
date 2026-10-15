# cogs/insights.py
# =====================================================================
# ─── INSIGHTS — Messages/day, active hours, top channels
# =====================================================================
import discord
from discord.ext import commands
import json
import os
import io
from datetime import datetime, timedelta
from collections import defaultdict

DATA_FILE = "data/insights.json"


def _load():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


INSIGHTS = _load()


class Insights(commands.Cog):
    """Server analytics"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        gid = str(message.guild.id)
        uid = str(message.author.id)
        cid = str(message.channel.id)
        today = datetime.now().strftime("%Y-%m-%d")
        hour = datetime.now().hour

        g = INSIGHTS.setdefault(gid, {
            "users": {}, "channels": {}, "hours": {str(i): 0 for i in range(24)},
            "daily": {}, "total": 0,
        })
        g["users"][uid] = g["users"].get(uid, 0) + 1
        g["channels"][cid] = g["channels"].get(cid, 0) + 1
        g["hours"][str(hour)] = g["hours"].get(str(hour), 0) + 1
        g["daily"][today] = g["daily"].get(today, 0) + 1
        g["total"] += 1

        # Save kola 20 messages
        if g["total"] % 20 == 0:
            _save(INSIGHTS)

    async def build_report(self, guild: discord.Guild) -> discord.Embed:
        gid = str(guild.id)
        g = INSIGHTS.get(gid)
        embed = discord.Embed(
            title=f"📊 Insights — {guild.name}",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        if not g:
            embed.description = "❌ Ma kaynch data."
            return embed

        embed.add_field(name="📨 Total messages", value=f"`{g['total']:,}`", inline=True)

        # Top users
        top_users = sorted(g["users"].items(), key=lambda x: x[1], reverse=True)[:5]
        lines = []
        for uid, cnt in top_users:
            m = guild.get_member(int(uid))
            name = m.name if m else f"User {uid}"
            lines.append(f"`{cnt:,}` — {name}")
        embed.add_field(name="👥 Top Users", value="\n".join(lines) or "—", inline=False)

        # Top channels
        top_channels = sorted(g["channels"].items(), key=lambda x: x[1], reverse=True)[:5]
        lines = []
        for cid, cnt in top_channels:
            ch = guild.get_channel(int(cid))
            name = ch.mention if ch else f"#{cid}"
            lines.append(f"`{cnt:,}` — {name}")
        embed.add_field(name="📢 Top Channels", value="\n".join(lines) or "—", inline=False)

        # Active hours
        top_hours = sorted(g["hours"].items(), key=lambda x: x[1], reverse=True)[:3]
        lines = [f"`{h}:00` — `{c:,}` msgs" for h, c in top_hours]
        embed.add_field(name="⏰ Active Hours", value="\n".join(lines) or "—", inline=False)

        # Daily
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = g["daily"].get(today, 0)
        embed.add_field(name="📅 Today", value=f"`{today_count:,}`", inline=True)
        embed.add_field(name="📈 All-time", value=f"`{g['total']:,}`", inline=True)

        return embed


async def setup(bot):
    await bot.add_cog(Insights(bot))