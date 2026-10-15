# cogs/scheduled.py
# =====================================================================
# ─── SCHEDULED MESSAGES — Send messages ba3d wa9t / recurring
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import uuid
from datetime import datetime, timedelta

DATA_FILE = "data/scheduled.json"


def _load():
    if not os.path.exists(DATA_FILE):
        return {"one_time": [], "recurring": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"one_time": [], "recurring": []}


def _save(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


SCHEDULED = _load()


def parse_duration(s: str) -> int:
    s = s.strip().lower()
    if not s:
        return -1
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    total = 0
    num = ""
    for c in s:
        if c.isdigit():
            num += c
        elif c in units:
            if not num:
                return -1
            total += int(num) * units[c]
            num = ""
        else:
            return -1
    if num:
        total += int(num)
    return total if total > 0 else -1


class Scheduled(commands.Cog):
    """Scheduled messages + recurring"""

    def __init__(self, bot):
        self.bot = bot
        self.checker.start()

    def cog_unload(self):
        self.checker.cancel()

    @tasks.loop(seconds=30)
    async def checker(self):
        now = datetime.now()
        changed = False

        for item in list(SCHEDULED["one_time"]):
            try:
                when = datetime.fromisoformat(item["when"])
            except Exception:
                continue
            if now >= when:
                await self._send(item)
                SCHEDULED["one_time"].remove(item)
                changed = True

        for item in SCHEDULED["recurring"]:
            try:
                next_at = datetime.fromisoformat(item["next_at"])
            except Exception:
                continue
            if now >= next_at:
                await self._send(item)
                interval = item["interval"]
                item["next_at"] = (now + timedelta(seconds=interval)).isoformat()
                changed = True

        if changed:
            _save(SCHEDULED)

    @checker.before_loop
    async def before(self):
        await self.bot.wait_until_ready()

    async def _send(self, item: dict):
        guild = self.bot.get_guild(item["guild_id"])
        if not guild:
            return
        ch = guild.get_channel(item["channel_id"])
        if not ch:
            return
        try:
            await ch.send(item["content"])
        except Exception as e:
            print(f"❌ Schedule send: {e}")

    @app_commands.command(name="schedule", description="📅 Sift message ba3d wa9t")
    @app_commands.describe(
        when="Duration (ex: 1h30m, 2d, 30m)",
        content="Message li bghiti tsift",
        channel="Channel (khawi = current)",
        repeat="Recurring duration (ex: 24h, 7d)",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def schedule_cmd(
        self,
        it: discord.Interaction,
        when: str,
        content: str,
        channel: discord.TextChannel = None,
        repeat: str = None,
    ):
        ch = channel or it.channel
        secs = parse_duration(when)
        if secs <= 0:
            return await it.response.send_message("❌ Duration ghalta!", ephemeral=True)

        sid = uuid.uuid4().hex[:8].upper()
        when_dt = datetime.now() + timedelta(seconds=secs)

        if repeat:
            r_secs = parse_duration(repeat)
            if r_secs <= 0:
                return await it.response.send_message("❌ Repeat ghalta!", ephemeral=True)
            SCHEDULED["recurring"].append({
                "id": sid, "guild_id": it.guild.id, "channel_id": ch.id,
                "content": content, "interval": r_secs,
                "next_at": when_dt.isoformat(), "author_id": it.user.id,
            })
            _save(SCHEDULED)
            await it.response.send_message(
                f"✅ **Recurring!**\n🆔 `{sid}` — {ch.mention}\n"
                f"⏰ First: <t:{int(when_dt.timestamp())}:R>\n🔁 Every: `{repeat}`"
            )
        else:
            SCHEDULED["one_time"].append({
                "id": sid, "guild_id": it.guild.id, "channel_id": ch.id,
                "content": content, "when": when_dt.isoformat(),
                "author_id": it.user.id,
            })
            _save(SCHEDULED)
            await it.response.send_message(
                f"✅ **Scheduled!**\n🆔 `{sid}` — {ch.mention}\n"
                f"⏰ <t:{int(when_dt.timestamp())}:R>"
            )

    @app_commands.command(name="unschedule", description="🗑️ Cancel scheduled message")
    @app_commands.describe(sid="ID")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def unschedule(self, it: discord.Interaction, sid: str):
        sid = sid.upper()
        removed = False
        for lst in [SCHEDULED["one_time"], SCHEDULED["recurring"]]:
            for item in list(lst):
                if item["id"] == sid:
                    lst.remove(item)
                    removed = True
        if removed:
            _save(SCHEDULED)
            await it.response.send_message(f"✅ Removed `{sid}`!")
        else:
            await it.response.send_message("❌ Ma l9itch!", ephemeral=True)

    @app_commands.command(name="schedules", description="📋 List scheduled messages")
    async def schedules_list(self, it: discord.Interaction):
        embed = discord.Embed(title="📅 Scheduled Messages", color=discord.Color.blurple())
        one = [x for x in SCHEDULED["one_time"] if x["guild_id"] == it.guild.id]
        rec = [x for x in SCHEDULED["recurring"] if x["guild_id"] == it.guild.id]
        if one:
            lines = []
            for x in one[:10]:
                ts = int(datetime.fromisoformat(x["when"]).timestamp())
                lines.append(f"`{x['id']}` — <#{x['channel_id']}> — <t:{ts}:R>")
            embed.add_field(name=f"⏰ One-time ({len(one)})", value="\n".join(lines), inline=False)
        if rec:
            lines = []
            for x in rec[:10]:
                ts = int(datetime.fromisoformat(x["next_at"]).timestamp())
                lines.append(f"`{x['id']}` — <#{x['channel_id']}> — next <t:{ts}:R>")
            embed.add_field(name=f"🔁 Recurring ({len(rec)})", value="\n".join(lines), inline=False)
        if not one and not rec:
            embed.description = "❌ Ma kaynch!"
        await it.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Scheduled(bot))