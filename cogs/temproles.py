# cogs/temproles.py
# =====================================================================
# ─── TEMP ROLES — Auto-remove ba3d wa9t
# =====================================================================
import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
from datetime import datetime, timedelta

DATA_FILE = "data/temproles.json"


def _load():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {int(g): v for g, v in raw.items()}
    except Exception:
        return {}


def _save(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


TEMPROLES = _load()


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


class TempRoles(commands.Cog):
    """Temp roles b auto-remove"""

    def __init__(self, bot):
        self.bot = bot
        self.checker.start()

    def cog_unload(self):
        self.checker.cancel()

    @tasks.loop(minutes=1)
    async def checker(self):
        now = datetime.now()
        changed = False
        for gid, data in list(TEMPROLES.items()):
            guild = self.bot.get_guild(gid)
            if not guild:
                continue
            for key in list(data.keys()):
                entry = data[key]
                try:
                    until = datetime.fromisoformat(entry["until"])
                except Exception:
                    continue
                if now >= until:
                    try:
                        member = guild.get_member(entry["user_id"])
                        role = guild.get_role(entry["role_id"])
                        if member and role and role in member.roles:
                            await member.remove_roles(role, reason="TempRole expired")
                    except Exception:
                        pass
                    data.pop(key, None)
                    changed = True
        if changed:
            _save(TEMPROLES)

    @checker.before_loop
    async def before(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="temprole", description="🎭 3ti role l wa9t mou3ayan")
    @app_commands.describe(member="L-member", role="Role", duration="Ex: 1h, 7d, 30m")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def temprole(self, it: discord.Interaction, member: discord.Member, role: discord.Role, duration: str):
        secs = parse_duration(duration)
        if secs <= 0:
            return await it.response.send_message("❌ Duration ghalta!", ephemeral=True)

        if role >= it.guild.me.top_role:
            return await it.response.send_message("❌ Role fo9 dyaly!", ephemeral=True)

        try:
            await member.add_roles(role, reason=f"TempRole {duration}")
        except discord.Forbidden:
            return await it.response.send_message("❌ Ma 3ndich permission!", ephemeral=True)

        until = datetime.now() + timedelta(seconds=secs)
        key = f"{member.id}:{role.id}"
        TEMPROLES.setdefault(it.guild.id, {})[key] = {
            "user_id": member.id,
            "role_id": role.id,
            "until": until.isoformat(),
            "mod_id": it.user.id,
        }
        _save(TEMPROLES)

        await it.response.send_message(
            f"✅ {member.mention} — {role.mention}\n"
            f"⏰ Until: <t:{int(until.timestamp())}:R>"
        )

    @app_commands.command(name="temproles", description="📋 List temp roles")
    async def temproles_list(self, it: discord.Interaction):
        data = TEMPROLES.get(it.guild.id, {})
        if not data:
            return await it.response.send_message("❌ Ma kaynch!", ephemeral=True)
        embed = discord.Embed(title="🎭 Temp Roles", color=discord.Color.blurple())
        for key, e in list(data.items())[:20]:
            ts = int(datetime.fromisoformat(e["until"]).timestamp())
            embed.add_field(
                name=f"<@{e['user_id']}> — <@&{e['role_id']}>",
                value=f"Expires <t:{ts}:R>",
                inline=False,
            )
        await it.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(TempRoles(bot))