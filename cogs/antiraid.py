# cogs/antiraid.py
# =====================================================================
# ─── ANTI-RAID + ANTI-NUKE — Auto-protection system
# =====================================================================
import discord
from discord.ext import commands, tasks
import json
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

DATA_FILE = "data/antiraid.json"


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


def _default():
    return {
        "enabled": True,
        "antiraid_enabled": True,
        "join_threshold": 10,       # joins
        "join_window": 30,          # seconds
        "min_account_age_days": 7,  # kick accounts younger
        "lockdown_active": False,
        "lockdown_until": None,
        "antinuke_enabled": True,
        "nuke_threshold": 3,        # actions
        "nuke_window": 10,          # seconds
        "trusted_users": [],
        "trusted_roles": [],
        "log_channel": None,
    }


ANTIRAID = _load()


def get_cfg(gid: int) -> dict:
    if gid not in ANTIRAID:
        ANTIRAID[gid] = _default()
        _save(ANTIRAID)
    return ANTIRAID[gid]


class AntiRaid(commands.Cog):
    """Anti-Raid + Anti-Nuke protection"""

    def __init__(self, bot):
        self.bot = bot
        self._joins = defaultdict(lambda: deque(maxlen=50))
        self._nuke_actions = defaultdict(lambda: deque(maxlen=50))
        self.lockdown_checker.start()

    def cog_unload(self):
        self.lockdown_checker.cancel()

    # ═══════════════════════════════════════════════════════════
    # ─── HELPERS
    # ═══════════════════════════════════════════════════════════
    def _is_trusted(self, member: discord.Member, cfg: dict) -> bool:
        if member.id == member.guild.owner_id:
            return True
        if member.id == self.bot.user.id:
            return True
        if member.id in cfg["trusted_users"]:
            return True
        member_roles = {r.id for r in member.roles}
        for rid in cfg["trusted_roles"]:
            if rid in member_roles:
                return True
        # Admin roles 9dim
        from botconfig import ADMIN_ROLES
        names = {r.name for r in member.roles}
        for ar in ADMIN_ROLES:
            if ar in names:
                return True
        return False

    async def _log(self, guild: discord.Guild, cfg: dict, embed: discord.Embed):
        ch_id = cfg.get("log_channel")
        if not ch_id:
            return
        ch = guild.get_channel(ch_id)
        if ch:
            try:
                await ch.send(embed=embed)
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════
    # ─── ANTI-RAID (join check)
    # ═══════════════════════════════════════════════════════════
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        cfg = get_cfg(member.guild.id)
        if not cfg["enabled"] or not cfg["antiraid_enabled"]:
            return

        # Account age check
        age_days = (datetime.now(datetime.UTC) - member.created_at).days \
            if hasattr(datetime, "UTC") else \
            (datetime.utcnow() - member.created_at.replace(tzinfo=None)).days

        if age_days < cfg["min_account_age_days"]:
            try:
                await member.send(
                    f"⚠️ Account dyalek jdid (`{age_days}d`) — ma tqderch tdkhol "
                    f"l **{member.guild.name}**.\n"
                    f"Khass `{cfg['min_account_age_days']}` days 9bel."
                )
            except Exception:
                pass
            try:
                await member.kick(reason=f"AntiRaid: account too young ({age_days}d)")
                embed = discord.Embed(
                    title="🛡️ AntiRaid — Kick",
                    description=f"**{member}** (`{member.id}`) t-kicka\n"
                                f"Reason: account age `{age_days}` days",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow(),
                )
                await self._log(member.guild, cfg, embed)
            except Exception:
                pass
            return

        # Join rate check
        now = time.time()
        dq = self._joins[member.guild.id]
        dq.append(now)
        recent = [t for t in dq if now - t <= cfg["join_window"]]

        if len(recent) >= cfg["join_threshold"] and not cfg["lockdown_active"]:
            await self._trigger_lockdown(member.guild, cfg, len(recent))

    async def _trigger_lockdown(self, guild, cfg, join_count):
        cfg["lockdown_active"] = True
        cfg["lockdown_until"] = (datetime.now() + timedelta(minutes=10)).isoformat()
        _save(ANTIRAID)

        # Enable server-wide verification level high
        try:
            await guild.edit(
                verification_level=discord.VerificationLevel.highest,
                reason="AntiRaid lockdown",
            )
        except Exception:
            pass

        embed = discord.Embed(
            title="🚨 ANTI-RAID LOCKDOWN",
            description=(
                f"**{join_count}** joins f **{cfg['join_window']}s**!\n"
                f"🔒 Server f **lockdown** l **10 min**.\n"
                f"Verification level: **HIGHEST**"
            ),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        await self._log(guild, cfg, embed)

        # Notify owner
        try:
            owner = guild.owner
            if owner:
                await owner.send(embed=embed)
        except Exception:
            pass

    @tasks.loop(seconds=30)
    async def lockdown_checker(self):
        now = datetime.now()
        for gid, cfg in list(ANTIRAID.items()):
            if not cfg.get("lockdown_active"):
                continue
            try:
                until = datetime.fromisoformat(cfg["lockdown_until"])
            except Exception:
                continue
            if now >= until:
                cfg["lockdown_active"] = False
                cfg["lockdown_until"] = None
                _save(ANTIRAID)
                guild = self.bot.get_guild(gid)
                if guild:
                    try:
                        await guild.edit(
                            verification_level=discord.VerificationLevel.medium,
                            reason="AntiRaid lockdown lifted",
                        )
                    except Exception:
                        pass
                    await self._log(guild, cfg, discord.Embed(
                        title="✅ Lockdown lifted",
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow(),
                    ))

    @lockdown_checker.before_loop
    async def before_lockdown(self):
        await self.bot.wait_until_ready()

    # ═══════════════════════════════════════════════════════════
    # ─── ANTI-NUKE (audit log monitor)
    # ═══════════════════════════════════════════════════════════
    def _record_nuke(self, guild_id: int, user_id: int) -> int:
        now = time.time()
        dq = self._nuke_actions[(guild_id, user_id)]
        dq.append(now)
        return len([t for t in dq if now - t <= 10])

    async def _handle_nuke(self, guild, actor: discord.Member, action: str, cfg: dict):
        if not cfg["enabled"] or not cfg["antinuke_enabled"]:
            return
        if not actor or actor.bot:
            return
        if self._is_trusted(actor, cfg):
            return

        count = self._record_nuke(guild.id, actor.id)
        if count < cfg["nuke_threshold"]:
            return

        # NUKE DETECTED → ban actor
        self._nuke_actions[(guild.id, actor.id)].clear()

        try:
            await guild.ban(actor, reason=f"AntiNuke: {count} {action} actions", delete_message_days=1)
            banned = True
        except Exception:
            banned = False
            # Fallback: strip all roles
            try:
                await actor.edit(roles=[], reason="AntiNuke: strip roles")
            except Exception:
                pass

        embed = discord.Embed(
            title="💥 ANTI-NUKE TRIGGERED",
            description=(
                f"**Actor:** {actor} (`{actor.id}`)\n"
                f"**Action:** `{action}`\n"
                f"**Count:** `{count}` f 10s\n"
                f"**Banned:** `{'✅' if banned else '❌'} `"
            ),
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow(),
        )
        await self._log(guild, cfg, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        cfg = get_cfg(channel.guild.id)
        if not cfg["enabled"]:
            return
        await self._fetch_and_handle(channel.guild, discord.AuditLogAction.channel_delete,
                                     channel.id, "channel_delete", cfg)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        cfg = get_cfg(role.guild.id)
        if not cfg["enabled"]:
            return
        await self._fetch_and_handle(role.guild, discord.AuditLogAction.role_delete,
                                     role.id, "role_delete", cfg)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        cfg = get_cfg(guild.id)
        if not cfg["enabled"]:
            return
        await self._fetch_and_handle(guild, discord.AuditLogAction.ban,
                                     user.id, "ban", cfg)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        cfg = get_cfg(member.guild.id)
        if not cfg["enabled"]:
            return
        await self._fetch_and_handle(member.guild, discord.AuditLogAction.kick,
                                     member.id, "kick", cfg)

    async def _fetch_and_handle(self, guild, action, target_id, action_name, cfg):
        try:
            async for entry in guild.audit_logs(limit=5, action=action):
                if entry.target and getattr(entry.target, "id", None) == target_id:
                    if entry.user and entry.user.id != self.bot.user.id:
                        await self._handle_nuke(guild, entry.user, action_name, cfg)
                    return
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════
    # ─── COMMANDS
    # ═══════════════════════════════════════════════════════════
    @commands.group(name="antiraid", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def antiraid_group(self, ctx: commands.Context):
        """`&antiraid` — Status"""
        cfg = get_cfg(ctx.guild.id)
        embed = discord.Embed(title="🛡️ AntiRaid Config", color=discord.Color.red())
        embed.add_field(name="Enabled", value=f"`{cfg['enabled']}`", inline=True)
        embed.add_field(name="AntiRaid", value=f"`{cfg['antiraid_enabled']}`", inline=True)
        embed.add_field(name="AntiNuke", value=f"`{cfg['antinuke_enabled']}`", inline=True)
        embed.add_field(name="Join Threshold", value=f"`{cfg['join_threshold']}` f `{cfg['join_window']}s`", inline=True)
        embed.add_field(name="Min Account Age", value=f"`{cfg['min_account_age_days']}d`", inline=True)
        embed.add_field(name="Nuke Threshold", value=f"`{cfg['nuke_threshold']}` f 10s", inline=True)
        embed.add_field(name="🔒 Lockdown", value=f"`{cfg['lockdown_active']}`", inline=True)
        embed.add_field(name="Trusted Users", value=f"`{len(cfg['trusted_users'])}`", inline=True)
        embed.add_field(name="Trusted Roles", value=f"`{len(cfg['trusted_roles'])}`", inline=True)
        await ctx.send(embed=embed)

    @antiraid_group.command(name="toggle")
    @commands.has_permissions(administrator=True)
    async def antiraid_toggle(self, ctx: commands.Context, feature: str):
        """`&antiraid toggle <enabled|antiraid|antinuke>`"""
        cfg = get_cfg(ctx.guild.id)
        f = feature.lower()
        if f not in ("enabled", "antiraid", "antinuke"):
            return await ctx.send("❌ Feature: `enabled` / `antiraid` / `antinuke`")
        if f == "enabled":
            cfg["enabled"] = not cfg["enabled"]
        elif f == "antiraid":
            cfg["antiraid_enabled"] = not cfg["antiraid_enabled"]
        else:
            cfg["antinuke_enabled"] = not cfg["antinuke_enabled"]
        _save(ANTIRAID)
        await ctx.send(f"✅ `{f}` = `{cfg[f if f != 'antiraid' else 'antiraid_enabled']}`")

    @antiraid_group.command(name="trust")
    @commands.has_permissions(administrator=True)
    async def antiraid_trust(self, ctx: commands.Context, target: discord.Member = None, role: discord.Role = None):
        """`&antiraid trust @user|@role`"""
        cfg = get_cfg(ctx.guild.id)
        if target:
            if target.id not in cfg["trusted_users"]:
                cfg["trusted_users"].append(target.id)
                _save(ANTIRAID)
            return await ctx.send(f"✅ {target.mention} trusted")
        if role:
            if role.id not in cfg["trusted_roles"]:
                cfg["trusted_roles"].append(role.id)
                _save(ANTIRAID)
            return await ctx.send(f"✅ {role.mention} trusted")
        await ctx.send("❌ 3ti @user wla @role")

    @antiraid_group.command(name="untrust")
    @commands.has_permissions(administrator=True)
    async def antiraid_untrust(self, ctx: commands.Context, target: discord.Member = None, role: discord.Role = None):
        cfg = get_cfg(ctx.guild.id)
        if target and target.id in cfg["trusted_users"]:
            cfg["trusted_users"].remove(target.id)
            _save(ANTIRAID)
            return await ctx.send(f"✅ {target.mention} untrusted")
        if role and role.id in cfg["trusted_roles"]:
            cfg["trusted_roles"].remove(role.id)
            _save(ANTIRAID)
            return await ctx.send(f"✅ {role.mention} untrusted")
        await ctx.send("❌ Ma kaynch!")

    @antiraid_group.command(name="setlog")
    @commands.has_permissions(administrator=True)
    async def antiraid_setlog(self, ctx: commands.Context, channel: discord.TextChannel):
        cfg = get_cfg(ctx.guild.id)
        cfg["log_channel"] = channel.id
        _save(ANTIRAID)
        await ctx.send(f"✅ Logs → {channel.mention}")

    @antiraid_group.command(name="unlockdown")
    @commands.has_permissions(administrator=True)
    async def antiraid_unlockdown(self, ctx: commands.Context):
        cfg = get_cfg(ctx.guild.id)
        cfg["lockdown_active"] = False
        cfg["lockdown_until"] = None
        _save(ANTIRAID)
        await ctx.send("✅ Lockdown disabled")

    @commands.command(name="lockdown")
    @commands.has_permissions(administrator=True)
    async def manual_lockdown(self, ctx: commands.Context):
        """`&lockdown` — Manual lockdown"""
        cfg = get_cfg(ctx.guild.id)
        if cfg["lockdown_active"]:
            return await ctx.send("⚠️ Deja f lockdown!")
        await self._trigger_lockdown(ctx.guild, cfg, 0)


async def setup(bot):
    await bot.add_cog(AntiRaid(bot))