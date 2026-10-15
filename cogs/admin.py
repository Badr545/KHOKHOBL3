# cogs/admin.py
# =====================================================================
# ─── ADMIN COMMANDS (Role-Based + Warn + Jail + Timeout)
#     Prefix: + (action) / - (remove)
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import utcnow
from datetime import timedelta
from utils.checks import require_role, require_role_prefix
from data_manager import WARNINGS, save_warnings as _save_warnings
import json
import os


# ═══════════════════════════════════════════════════════════════════
# ─── JAIL CONFIG
# ═══════════════════════════════════════════════════════════════════
JAIL_ROLE_ID = 1528517069220479006
JAIL_FILE = "data/jail.json"


def _load_jailed():
    if not os.path.exists(JAIL_FILE):
        return {}
    try:
        with open(JAIL_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {int(g): {int(u): v for u, v in d.items()} for g, d in raw.items()}
    except Exception as e:
        print(f"⚠️ Load jail failed: {e}")
        return {}


def _save_jailed():
    os.makedirs("data", exist_ok=True)
    try:
        with open(JAIL_FILE, "w", encoding="utf-8") as f:
            json.dump(JAILED, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Save jail failed: {e}")


JAILED: dict = _load_jailed()


def parse_duration(s: str) -> int:
    """'1h30m' → seconds. Rje3 -1 ila format ghalat."""
    if not s:
        return -1
    s = s.strip().lower()
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


# ═══════════════════════════════════════════════════════════════════
# ─── WARN ROLES CONFIG
#     Kol count → lista dyal smiyat (kayn b emoji w bla emoji)
# ═══════════════════════════════════════════════════════════════════
WARN_ROLES = {
    1: ["❗First Warning", "First Warning"],
    2: ["‼️Second Warning", "Second Warning"],
    3: ["⁉️Last Warning", "Last Warning"],
}
WARN_JAIL_AT = 4  # 4th warn → auto-jail


class Admin(commands.Cog):
    """Admin: kick, ban, warn, warnings, slowmode, lock, unlock, jail, rta7, timeout"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════════════════════════
    # ─── WARN SYSTEM HELPERS
    # ═══════════════════════════════════════════════════════════
    def _get_warnings(self, guild_id: int, user_id: int) -> list:
        return WARNINGS.get(guild_id, {}).get(user_id, [])

    def _find_warn_role(self, guild, threshold: int):
        """Qelleb 3la warn role b emoji wla bla emoji."""
        for name in WARN_ROLES.get(threshold, []):
            role = discord.utils.get(guild.roles, name=name)
            if role:
                return role
        return None

    async def _apply_warn_roles(self, member: discord.Member, count: int):
        """Kol warn y3ti role dyalo + y7ayed warn roles 9dam."""
        for threshold in sorted(WARN_ROLES.keys()):
            role = self._find_warn_role(member.guild, threshold)
            if role is None:
                continue
            try:
                if count == threshold and role not in member.roles:
                    await member.add_roles(role, reason=f"Warn #{count}")
                elif count < threshold and role in member.roles:
                    await member.remove_roles(role, reason=f"Warn cleared (count={count})")
            except discord.Forbidden:
                pass

    async def _jail_member(self, guild, member, reason: str):
        """Internal jail helper — kaykhdem men warn system (bla ctx)."""
        jail_role = guild.get_role(JAIL_ROLE_ID)
        if jail_role is None:
            return False, "Jail role ma kaynch!"
        if guild.me.top_role.position <= jail_role.position:
            return False, "Jail role fo9 role dyal bot!"
        if guild.id in JAILED and member.id in JAILED[guild.id]:
            return False, "Deja msjoun!"

        saved_roles = [
            r.id for r in member.roles
            if not r.is_default() and r.id != JAIL_ROLE_ID
        ]
        JAILED.setdefault(guild.id, {})[member.id] = {
            "roles": saved_roles,
            "reason": reason,
            "mod": self.bot.user.id,
            "time": discord.utils.utcnow().isoformat(),
        }
        _save_jailed()

        try:
            removable = [
                r for r in member.roles
                if not r.is_default() and r.id != JAIL_ROLE_ID
            ]
            if removable:
                await member.remove_roles(*removable, reason=f"Auto-jail: {reason}")
            await member.add_roles(jail_role, reason=f"Auto-jail: {reason}")
        except discord.Forbidden:
            return False, "Ma 3ndich permission!"
        except Exception as e:
            return False, str(e)

        # DM l-user
        try:
            await member.send(
                f"🔒 **T-sjenti f {guild.name}**\n"
                f"**Reason:** {reason}\n"
                f"Bash ttla9: `+rta7` (wla 3ayet l-staff)"
            )
        except discord.Forbidden:
            pass

        return True, "OK"

    async def _apply_warn_punishment(self, member: discord.Member, count: int):
        """Punishment logic: 4 warns → jail."""
        if count >= WARN_JAIL_AT:
            ok, msg = await self._jail_member(
                member.guild, member,
                reason=f"Auto-jail: {count} warnings",
            )
            if ok:
                return "jail"
            return f"jail_failed:{msg}"
        return None

    def _format_action(self, punishment: str) -> str | None:
        """Format dyal punishment string l embed."""
        if not punishment:
            return None
        if punishment == "jail":
            return "🔒 **JAILED** (auto at 4 warnings)"
        if punishment.startswith("jail_failed:"):
            err = punishment.split(":", 1)[1]
            return f"⚠️ **Jail failed:** `{err}`"
        if punishment == "ban":
            return "🔨 **BANNED**"
        if punishment == "kick":
            return "👢 **KICKED**"
        return f"⚡ **{punishment.upper()}**"

    # ═══════════════════════════════════════════════════════════
    # ─── /warn
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="warn", description="Warning l member")
    @app_commands.describe(member="L-member", reason="Sabab")
    @require_role("warn")
    async def warn(self, interaction: discord.Interaction, member: discord.Member,
                   reason: str = "Ma 3endich reason"):
        if member.bot:
            return await interaction.response.send_message("❌ Ma tqderch t-warni bot!", ephemeral=True)
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message("❌ Role fo9 dyalek!", ephemeral=True)

        guild_id = interaction.guild.id
        WARNINGS.setdefault(guild_id, {}).setdefault(member.id, []).append({
            "reason": reason,
            "mod": interaction.user.id,
            "time": discord.utils.utcnow().isoformat(),
        })
        _save_warnings()
        count = len(WARNINGS[guild_id][member.id])

        await self._apply_warn_roles(member, count)
        punishment = await self._apply_warn_punishment(member, count)

        embed = discord.Embed(
            title="⚠️ Warning",
            description=f"{member.mention} t-3ta warning!",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.add_field(name="👮 Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="📊 Total Warnings", value=f"`{count}`", inline=True)

        # Role gained info
        role_gained = None
        for threshold in sorted(WARN_ROLES.keys()):
            if count == threshold:
                role_gained = self._find_warn_role(interaction.guild, threshold)
                break
        if role_gained:
            embed.add_field(name="🎭 Role Added", value=role_gained.mention, inline=True)

        action_text = self._format_action(punishment)
        if action_text:
            embed.add_field(name="⚡ Action", value=action_text, inline=False)

        await interaction.response.send_message(embed=embed)

        # DM l-user
        try:
            dm = discord.Embed(
                title=f"⚠️ T-3titi warning f {interaction.guild.name}",
                description=f"**Reason:** {reason}\n**Total:** `{count}`",
                color=discord.Color.orange(),
            )
            if role_gained:
                dm.add_field(name="🎭 Role", value=role_gained.mention, inline=False)
            if action_text:
                dm.add_field(name="⚡ Action", value=action_text, inline=False)
            await member.send(embed=dm)
        except discord.Forbidden:
            pass

    @commands.command(name="warn")
    @require_role_prefix("warn")
    async def warn_prefix(self, ctx: commands.Context, member: discord.Member,
                          *, reason: str = "Ma 3endich reason"):
        """+warn @user [reason]"""
        if member.bot:
            return await ctx.send("❌ Ma tqderch t-warni bot!")
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("❌ Role fo9 dyalek!")

        guild_id = ctx.guild.id
        WARNINGS.setdefault(guild_id, {}).setdefault(member.id, []).append({
            "reason": reason,
            "mod": ctx.author.id,
            "time": discord.utils.utcnow().isoformat(),
        })
        _save_warnings()
        count = len(WARNINGS[guild_id][member.id])

        await self._apply_warn_roles(member, count)
        punishment = await self._apply_warn_punishment(member, count)

        embed = discord.Embed(
            title="⚠️ Warning",
            description=f"{member.mention} t-3ta warning!",
            color=discord.Color.orange(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.add_field(name="👮 Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="📊 Total", value=f"`{count}`", inline=True)

        role_gained = None
        for threshold in sorted(WARN_ROLES.keys()):
            if count == threshold:
                role_gained = self._find_warn_role(ctx.guild, threshold)
                break
        if role_gained:
            embed.add_field(name="🎭 Role Added", value=role_gained.mention, inline=True)

        action_text = self._format_action(punishment)
        if action_text:
            embed.add_field(name="⚡ Action", value=action_text, inline=False)

        await ctx.send(embed=embed)

        try:
            dm = discord.Embed(
                title=f"⚠️ T-3titi warning f {ctx.guild.name}",
                description=f"**Reason:** {reason}\n**Total:** `{count}`",
                color=discord.Color.orange(),
            )
            if action_text:
                dm.add_field(name="⚡ Action", value=action_text, inline=False)
            await member.send(embed=dm)
        except discord.Forbidden:
            pass

    # ═══════════════════════════════════════════════════════════
    # ─── /warnings
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="warnings", description="Chouf warnings dyal member")
    @require_role("warnings")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        warns = self._get_warnings(interaction.guild.id, member.id)
        if not warns:
            return await interaction.response.send_message(
                f"✅ {member.mention} ma 3endouch warnings!", ephemeral=True
            )
        embed = discord.Embed(
            title=f"⚠️ Warnings dyal {member.name}",
            description=f"**Total:** `{len(warns)}`",
            color=discord.Color.orange(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        for i, w in enumerate(warns[:10], 1):
            mod = interaction.guild.get_member(w.get("mod"))
            mod_name = mod.mention if mod else "?"
            embed.add_field(
                name=f"#{i}",
                value=f"**Reason:** {w['reason']}\n**By:** {mod_name}",
                inline=False,
            )
        if len(warns) > 10:
            embed.set_footer(text=f"... w {len(warns) - 10} khrin")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name="warnings")
    @require_role_prefix("warnings")
    async def warnings_prefix(self, ctx: commands.Context, member: discord.Member):
        """+warnings @user"""
        warns = self._get_warnings(ctx.guild.id, member.id)
        if not warns:
            return await ctx.send("✅ Ma 3endouch warnings!")
        embed = discord.Embed(
            title=f"⚠️ Warnings dyal {member.name}",
            description=f"**Total:** `{len(warns)}`",
            color=discord.Color.orange(),
        )
        for i, w in enumerate(warns[:10], 1):
            embed.add_field(name=f"#{i}", value=w["reason"], inline=False)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /clearwarns
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="clearwarns", description="Msa7 warnings dyal member")
    @require_role("clearwarns")
    async def clearwarns(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = interaction.guild.id
        if guild_id in WARNINGS and member.id in WARNINGS[guild_id]:
            del WARNINGS[guild_id][member.id]
            _save_warnings()
        await self._apply_warn_roles(member, 0)
        await interaction.response.send_message(f"✅ Warnings dyal {member.mention} t-mas7ou!")

    @commands.command(name="clearwarns")
    @require_role_prefix("clearwarns")
    async def clearwarns_prefix(self, ctx: commands.Context, member: discord.Member):
        """+clearwarns @user"""
        guild_id = ctx.guild.id
        if guild_id in WARNINGS and member.id in WARNINGS[guild_id]:
            del WARNINGS[guild_id][member.id]
            _save_warnings()
        await self._apply_warn_roles(member, 0)
        await ctx.send(f"✅ Warnings dyal {member.mention} t-mas7ou!")

    # ═══════════════════════════════════════════════════════════
    # ─── /kick
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="kick", description="Kherrej user")
    @require_role("kick")
    async def kick(self, interaction: discord.Interaction, member: discord.Member,
                   reason: str = "Ma 3endich reason"):
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message("❌ Role fo9 dyalek!", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        try:
            await member.send(f"⛔ T-kickiti mn **{interaction.guild.name}**. Reason: {reason}")
        except discord.Forbidden:
            pass
        await member.kick(reason=reason)
        await interaction.followup.send(f"✅ {member.mention} t-kicka! `{reason}`", ephemeral=True)

    @commands.command(name="kick")
    @require_role_prefix("kick")
    @commands.bot_has_permissions(kick_members=True)
    async def kick_prefix(self, ctx: commands.Context, member: discord.Member,
                          *, reason: str = "Ma 3endich reason"):
        """+kick @user [reason]"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("❌ Role fo9 dyalek!")
        try:
            await member.send(f"⛔ T-kickiti mn **{ctx.guild.name}**. Reason: {reason}")
        except discord.Forbidden:
            pass
        await member.kick(reason=reason)
        await ctx.send(f"✅ {member.mention} t-kicka! `{reason}`")

    # ═══════════════════════════════════════════════════════════
    # ─── /ban
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="ban", description="Ban user")
    @require_role("ban")
    async def ban(self, interaction: discord.Interaction, member: discord.Member,
                  reason: str = "Ma 3endich reason",
                  delete_days: app_commands.Range[int, 0, 7] = 0):
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message("❌ Role fo9 dyalek!", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        await member.ban(reason=reason, delete_message_days=delete_days)
        await interaction.followup.send(f"🔨 {member.mention} t-bana! `{reason}`", ephemeral=True)

    @commands.command(name="ban")
    @require_role_prefix("ban")
    @commands.bot_has_permissions(ban_members=True)
    async def ban_prefix(self, ctx: commands.Context, member: discord.Member,
                         delete_days: int = 0, *, reason: str = "Ma 3endich reason"):
        """+ban @user [delete_days] [reason]"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("❌ Role fo9 dyalek!")
        if delete_days < 0 or delete_days > 7:
            return await ctx.send("❌ `delete_days`: 0-7!")
        await member.ban(reason=reason, delete_message_days=delete_days)
        await ctx.send(f"🔨 {member.mention} t-bana! `{reason}`")

    # ═══════════════════════════════════════════════════════════
    # ─── /slowmode
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="slowmode", description="Slow mode")
    @require_role("slowmode")
    async def slowmode(self, interaction: discord.Interaction,
                       seconds: app_commands.Range[int, 0, 21600]):
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f"✅ Slow mode: `{seconds}s`")

    @commands.command(name="slowmode")
    @require_role_prefix("slowmode")
    async def slowmode_prefix(self, ctx: commands.Context, seconds: int = 0):
        """+slowmode [seconds]"""
        if seconds < 0 or seconds > 21600:
            return await ctx.send("❌ 0-21600!")
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"✅ Slow mode: `{seconds}s`")

    # ═══════════════════════════════════════════════════════════
    # ─── /lock / /unlock
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="lock", description="Qfel channel")
    @require_role("lock")
    async def lock(self, interaction: discord.Interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔒 T-qfel!")

    @commands.command(name="lock")
    @require_role_prefix("lock")
    async def lock_prefix(self, ctx: commands.Context):
        """+lock"""
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send("🔒 T-qfel!")

    @app_commands.command(name="unlock", description="Ftah channel")
    @require_role("unlock")
    async def unlock(self, interaction: discord.Interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔓 T-fta7!")

    @commands.command(name="unlock")
    @require_role_prefix("unlock")
    async def unlock_prefix(self, ctx: commands.Context):
        """+unlock"""
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send("🔓 T-fta7!")

    # ═══════════════════════════════════════════════════════════
    # ─── JAIL HELPERS (internal)
    # ═══════════════════════════════════════════════════════════
    async def _do_jail(self, ctx: commands.Context, member: discord.Member, reason: str):
        """Logic dyal jail — kaykhedm b +jail"""
        if member.bot:
            return await ctx.send("❌ Ma tqderch tsjen bot!")
        if member.id == ctx.guild.owner_id:
            return await ctx.send("❌ Ma tqderch tsjen l-owner!")
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("❌ Role fo9 dyalek!")

        jail_role = ctx.guild.get_role(JAIL_ROLE_ID)
        if jail_role is None:
            return await ctx.send(f"❌ Jail role (`{JAIL_ROLE_ID}`) ma kaynch!")
        if ctx.guild.me.top_role.position <= jail_role.position:
            return await ctx.send("❌ Jail role fo9 role dyal bot! 7arrek role dyal bot fo9.")

        guild_id = ctx.guild.id
        if guild_id in JAILED and member.id in JAILED[guild_id]:
            return await ctx.send(f"⚠️ {member.mention} deja msjoun! St3mel `-jail` bash ttla9o.")

        saved_roles = [r.id for r in member.roles if not r.is_default() and r.id != JAIL_ROLE_ID]
        JAILED.setdefault(guild_id, {})[member.id] = {
            "roles": saved_roles,
            "reason": reason,
            "mod": ctx.author.id,
            "time": discord.utils.utcnow().isoformat(),
        }
        _save_jailed()

        try:
            removable = [r for r in member.roles if not r.is_default() and r.id != JAIL_ROLE_ID]
            if removable:
                await member.remove_roles(*removable, reason=f"Jail: {reason}")
            await member.add_roles(jail_role, reason=f"Jail: {reason}")
        except discord.Forbidden:
            return await ctx.send("❌ Ma 3ndich permission!")
        except Exception as e:
            return await ctx.send(f"❌ `{e}`")

        embed = discord.Embed(
            title="🔒 Jail",
            description=f"{member.mention} t-sjen!",
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.add_field(name="👮 Mod", value=ctx.author.mention, inline=True)
        embed.add_field(name="🎭 Roles Saved", value=f"`{len(saved_roles)}`", inline=True)
        embed.set_footer(text="Bash tla9o: -jail @user")
        await ctx.send(embed=embed)

        try:
            await member.send(
                f"🔒 **T-sjenti f {ctx.guild.name}**\n"
                f"**Reason:** {reason}\n"
                f"Bash ttla9: **-jail** (wla 3ayet l-staff)"
            )
        except discord.Forbidden:
            pass

    async def _do_unjail(self, ctx: commands.Context, member: discord.Member):
        """Logic dyal unjail — kaykhedm b -jail"""
        jail_role = ctx.guild.get_role(JAIL_ROLE_ID)
        guild_id = ctx.guild.id
        data = JAILED.get(guild_id, {}).get(member.id)

        if not data and (jail_role is None or jail_role not in member.roles):
            return await ctx.send(f"❌ {member.mention} machi msjoun!")

        restored = 0
        try:
            if jail_role and jail_role in member.roles:
                await member.remove_roles(jail_role, reason=f"Unjail par {ctx.author}")

            if data:
                saved_ids = data.get("roles", [])
                to_restore = []
                for rid in saved_ids:
                    r = ctx.guild.get_role(rid)
                    if r is None or r in member.roles:
                        continue
                    if r >= ctx.guild.me.top_role:
                        continue
                    to_restore.append(r)
                if to_restore:
                    await member.add_roles(*to_restore, reason="Unjail restore")
                    restored = len(to_restore)
        except discord.Forbidden:
            return await ctx.send("❌ Ma 3ndich permission!")
        except Exception as e:
            return await ctx.send(f"❌ `{e}`")

        if guild_id in JAILED and member.id in JAILED[guild_id]:
            del JAILED[guild_id][member.id]
            _save_jailed()

        embed = discord.Embed(
            title="🔓 Unjail",
            description=f"{member.mention} t-fta7!",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="🎭 Roles Restored", value=f"`{restored}`", inline=True)
        embed.add_field(name="👮 Mod", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)

        try:
            await member.send(f"🔓 **T-fta7ti mn jail f {ctx.guild.name}**")
        except discord.Forbidden:
            pass

    # ═══════════════════════════════════════════════════════════
    # ─── +jail / -jail (PREFIX)
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="jail", aliases=["unjail", "rta7"])
    @require_role_prefix("jail")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def jail_prefix(self, ctx: commands.Context, member: discord.Member,
                          *, reason: str = "Ma 3endich reason"):
        """
        +jail @user [reason]  → Sjen member (hyed kolchi roles)
        -jail @user           → 7ayed jail w rejje3 roles
        &jail / &unjail / &rta7 → nafs l-7aja
        """
        if ctx.prefix == "-" or ctx.invoked_with in ("unjail", "rta7"):
            return await self._do_unjail(ctx, member)
        return await self._do_jail(ctx, member, reason)

    # ═══════════════════════════════════════════════════════════
    # ─── /jail / /rta7 (SLASH)
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="jail", description="[STAFF] Sjen member (hyed kolchi roles)")
    @app_commands.describe(member="L-member", reason="Sabab")
    @app_commands.checks.has_permissions(manage_roles=True)
    @require_role("jail")
    async def jail_slash(self, interaction: discord.Interaction, member: discord.Member,
                         reason: str = "Ma 3endich reason"):
        if member.bot:
            return await interaction.response.send_message("❌ Ma tqderch tsjen bot!", ephemeral=True)
        if member.id == interaction.guild.owner_id:
            return await interaction.response.send_message("❌ Ma tqderch tsjen l-owner!", ephemeral=True)
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message("❌ Role fo9 dyalek!", ephemeral=True)

        jail_role = interaction.guild.get_role(JAIL_ROLE_ID)
        if jail_role is None:
            return await interaction.response.send_message(
                f"❌ Jail role (`{JAIL_ROLE_ID}`) ma kaynch!", ephemeral=True)
        if interaction.guild.me.top_role.position <= jail_role.position:
            return await interaction.response.send_message("❌ Jail role fo9 role dyal bot!", ephemeral=True)

        guild_id = interaction.guild.id
        if guild_id in JAILED and member.id in JAILED[guild_id]:
            return await interaction.response.send_message(
                f"⚠️ {member.mention} deja msjoun!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        saved_roles = [r.id for r in member.roles if not r.is_default() and r.id != JAIL_ROLE_ID]
        JAILED.setdefault(guild_id, {})[member.id] = {
            "roles": saved_roles, "reason": reason,
            "mod": interaction.user.id,
            "time": discord.utils.utcnow().isoformat(),
        }
        _save_jailed()

        try:
            removable = [r for r in member.roles if not r.is_default() and r.id != JAIL_ROLE_ID]
            if removable:
                await member.remove_roles(*removable, reason=f"Jail: {reason}")
            await member.add_roles(jail_role, reason=f"Jail: {reason}")
        except discord.Forbidden:
            return await interaction.followup.send("❌ Ma 3ndich permission!", ephemeral=True)
        except Exception as e:
            return await interaction.followup.send(f"❌ `{e}`", ephemeral=True)

        embed = discord.Embed(
            title="🔒 Jail",
            description=f"{member.mention} t-sjen!",
            color=discord.Color.dark_red(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.add_field(name="👮 Mod", value=interaction.user.mention, inline=True)
        embed.add_field(name="🎭 Roles Saved", value=f"`{len(saved_roles)}`", inline=True)
        embed.set_footer(text="St3mel /rta7 bash ttla9o")
        await interaction.followup.send(embed=embed)

        try:
            await member.send(f"🔒 **T-sjenti f {interaction.guild.name}**\n**Reason:** {reason}")
        except discord.Forbidden:
            pass

    @app_commands.command(name="rta7", description="[STAFF] 7ayed jail mn member")
    @app_commands.describe(member="L-member")
    @app_commands.checks.has_permissions(manage_roles=True)
    @require_role("rta7")
    async def rta7_slash(self, interaction: discord.Interaction, member: discord.Member):
        jail_role = interaction.guild.get_role(JAIL_ROLE_ID)
        guild_id = interaction.guild.id
        data = JAILED.get(guild_id, {}).get(member.id)

        if not data and (jail_role is None or jail_role not in member.roles):
            return await interaction.response.send_message(
                f"❌ {member.mention} machi msjoun!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        restored = 0
        try:
            if jail_role and jail_role in member.roles:
                await member.remove_roles(jail_role, reason="Unjail")
            if data:
                saved_ids = data.get("roles", [])
                to_restore = [interaction.guild.get_role(rid) for rid in saved_ids]
                to_restore = [r for r in to_restore if r and r not in member.roles and r < interaction.guild.me.top_role]
                if to_restore:
                    await member.add_roles(*to_restore, reason="Unjail restore")
                    restored = len(to_restore)
        except discord.Forbidden:
            return await interaction.followup.send("❌ Ma 3ndich permission!", ephemeral=True)
        except Exception as e:
            return await interaction.followup.send(f"❌ `{e}`", ephemeral=True)

        if guild_id in JAILED and member.id in JAILED[guild_id]:
            del JAILED[guild_id][member.id]
            _save_jailed()

        embed = discord.Embed(title="🔓 Unjail", description=f"{member.mention} t-fta7!", color=discord.Color.green())
        embed.add_field(name="🎭 Roles Restored", value=f"`{restored}`", inline=True)
        embed.add_field(name="👮 Mod", value=interaction.user.mention, inline=True)
        await interaction.followup.send(embed=embed)

        try:
            await member.send(f"🔓 **T-fta7ti mn jail f {interaction.guild.name}**")
        except discord.Forbidden:
            pass

    # ═══════════════════════════════════════════════════════════
    # ─── +timeout / -timeout (PREFIX)
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="timeout", aliases=["mute"])
    @require_role_prefix("timeout")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout_prefix(self, ctx: commands.Context, member: discord.Member,
                             *, args: str = ""):
        """
        +timeout @user <duration> [reason]  → Timeout (ex: +timeout @user 1h spamming)
        -timeout @user                      → 7ayed timeout
        """
        # ─── REMOVE TIMEOUT (-timeout)
        if ctx.prefix == "-":
            try:
                await member.timeout(None, reason=f"Timeout removed par {ctx.author}")
            except discord.Forbidden:
                return await ctx.send("❌ Ma 3ndich permission!")
            except Exception as e:
                return await ctx.send(f"❌ `{e}`")

            embed = discord.Embed(
                title="✅ Timeout Removed",
                description=f"{member.mention} wella free!",
                color=discord.Color.green(),
            )
            embed.add_field(name="👮 Mod", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)

            try:
                await member.send(f"✅ **T-7ayed lik timeout f {ctx.guild.name}**")
            except discord.Forbidden:
                pass
            return

        # ─── APPLY TIMEOUT (+timeout)
        if not args:
            return await ctx.send(
                "❌ Usage: `+timeout @user <duration> [reason]`\n"
                "Ex: `+timeout @user 1h spamming`\n"
                "Bash thayd: `-timeout @user`"
            )

        parts = args.split(maxsplit=1)
        duration = parts[0]
        reason = parts[1] if len(parts) > 1 else "Ma 3endich reason"

        if member.bot:
            return await ctx.send("❌ Ma tqderch timeout l bot!")
        if member.id == ctx.guild.owner_id:
            return await ctx.send("❌ Ma tqderch timeout l-owner!")
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("❌ Role fo9 dyalek!")

        secs = parse_duration(duration)
        if secs <= 0:
            return await ctx.send("❌ Duration ghalta! Ex: `1h`, `30m`, `1d`, `7d`")
        if secs > 28 * 86400:
            return await ctx.send("❌ Max 28d!")

        until = discord.utils.utcnow() + timedelta(seconds=secs)
        try:
            await member.timeout(until, reason=f"{ctx.author}: {reason}")
        except discord.Forbidden:
            return await ctx.send("❌ Ma 3ndich permission!")
        except Exception as e:
            return await ctx.send(f"❌ `{e}`")

        embed = discord.Embed(
            title="⏱️ Timeout",
            description=f"{member.mention} t-timeout!",
            color=discord.Color.orange(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="⏰ Until", value=f"<t:{int(until.timestamp())}:R>", inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.add_field(name="👮 Mod", value=ctx.author.mention, inline=True)
        embed.set_footer(text="Bash thayd: -timeout @user")
        await ctx.send(embed=embed)

        try:
            await member.send(
                f"⏱️ **T-timeout f {ctx.guild.name}**\n"
                f"**Until:** <t:{int(until.timestamp())}:R>\n"
                f"**Reason:** {reason}"
            )
        except discord.Forbidden:
            pass

    @app_commands.command(name="timeout", description="[STAFF] Timeout member")
    @app_commands.describe(
        member="L-member",
        duration="Duration (ex: 1h, 30m, 1d, 7d) — max 28d",
        reason="Sabab",
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    @require_role("timeout")
    async def timeout_slash(self, interaction: discord.Interaction, member: discord.Member,
                            duration: str, reason: str = "Ma 3endich reason"):
        if member.bot:
            return await interaction.response.send_message("❌ Ma tqderch timeout l bot!", ephemeral=True)
        if member.id == interaction.guild.owner_id:
            return await interaction.response.send_message("❌ Ma tqderch timeout l-owner!", ephemeral=True)
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message("❌ Role fo9 dyalek!", ephemeral=True)

        secs = parse_duration(duration)
        if secs <= 0:
            return await interaction.response.send_message("❌ Duration ghalta!", ephemeral=True)
        if secs > 28 * 86400:
            return await interaction.response.send_message("❌ Max 28d!", ephemeral=True)

        until = discord.utils.utcnow() + timedelta(seconds=secs)
        try:
            await member.timeout(until, reason=f"{interaction.user}: {reason}")
        except discord.Forbidden:
            return await interaction.response.send_message("❌ Ma 3ndich permission!", ephemeral=True)
        except Exception as e:
            return await interaction.response.send_message(f"❌ `{e}`", ephemeral=True)

        embed = discord.Embed(title="⏱️ Timeout", description=f"{member.mention} t-timeout!", color=discord.Color.orange())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="⏰ Until", value=f"<t:{int(until.timestamp())}:R>", inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.add_field(name="👮 Mod", value=interaction.user.mention, inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="untimeout", description="[STAFF] 7ayed timeout")
    @app_commands.describe(member="L-member")
    @app_commands.checks.has_permissions(moderate_members=True)
    @require_role("timeout")
    async def untimeout_slash(self, interaction: discord.Interaction, member: discord.Member):
        try:
            await member.timeout(None, reason=f"Untimeout par {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message("❌ Ma 3ndich permission!", ephemeral=True)
        except Exception as e:
            return await interaction.response.send_message(f"❌ `{e}`", ephemeral=True)

        embed = discord.Embed(title="✅ Untimeout", description=f"{member.mention} wella free!", color=discord.Color.green())
        embed.add_field(name="👮 Mod", value=interaction.user.mention, inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Admin(bot))