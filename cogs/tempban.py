# cogs/tempban.py
# =====================================================================
# ─── TEMP BAN — Ban b wa9t + auto-unban
# =====================================================================
import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta

DATA_FILE = "data/tempbans.json"


def _load():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {int(g): {int(u): v for u, v in d.items()} for g, d in raw.items()}
    except Exception:
        return {}


def _save(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


TEMPBANS = _load()


def parse_duration(s: str) -> int:
    """'1h30m' → seconds. -1 ila ghalat."""
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


class TempBan(commands.Cog):
    """Temp ban b auto-unban"""

    def __init__(self, bot):
        self.bot = bot
        self.checker.start()

    def cog_unload(self):
        self.checker.cancel()

    @tasks.loop(seconds=30)
    async def checker(self):
        now = datetime.now()
        changed = False
        for gid in list(TEMPBANS.keys()):
            guild = self.bot.get_guild(gid)
            if not guild:
                continue
            for uid in list(TEMPBANS[gid].keys()):
                entry = TEMPBANS[gid][uid]
                try:
                    until = datetime.fromisoformat(entry["until"])
                except Exception:
                    continue
                if until <= now:
                    try:
                        user = discord.Object(id=uid)
                        await guild.unban(user, reason="Temp ban expired")
                    except Exception:
                        pass
                    TEMPBANS[gid].pop(uid, None)
                    changed = True
        if changed:
            _save()

    @checker.before_loop
    async def before(self):
        await self.bot.wait_until_ready()

    async def tempban(self, guild, user, duration_s: int, reason: str, mod):
        until = datetime.now() + timedelta(seconds=duration_s)
        try:
            await guild.ban(user, reason=f"TempBan ({duration_s}s) by {mod}: {reason}")
        except Exception as e:
            return None, str(e)
        TEMPBANS.setdefault(guild.id, {})[user.id] = {
            "until": until.isoformat(),
            "reason": reason,
            "mod": mod.id,
        }
        _save()
        return until, None

    async def tempunban(self, guild, user_id: int):
        if guild.id in TEMPBANS and user_id in TEMPBANS[guild.id]:
            try:
                await guild.unban(discord.Object(id=user_id), reason="TempUnban manual")
            except Exception:
                pass
            TEMPBANS[guild.id].pop(user_id, None)
            _save()
            return True
        return False


async def setup(bot):
    await bot.add_cog(TempBan(bot))