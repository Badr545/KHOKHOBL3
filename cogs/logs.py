# cogs/logs.py
# =====================================================================
# ─── LOGS — SPLIT CHANNELS + AUTO-CREATE + PERMISSION DENIED
# =====================================================================
import discord
from discord.ext import commands
import asyncio


# ═══════════════════════════════════════════════════════════════════
# ─── CHANNELS CONFIG
# ═══════════════════════════════════════════════════════════════════
LOG_CHANNELS = {
    "member":  "logs-member",      # 👥 Join/Leave/Kick/Ban/Nickname/Roles/Timeout
    "message": "logs-message",     # 💬 Delete/Edit
    "voice":   "logs-voice",       # 🔊 Voice join/leave/move
    "channel": "logs-channels",    # 📢 Channel + 🎭 Role create/delete/update
    "general": "logs",             # 🛡️ Permission denied + misc
}


INVITE_CACHE: dict[int, dict[str, int]] = {}


class Logs(commands.Cog):
    """Logs m9asmin + auto-create + permission denied"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════════════════════════
    # ─── CHANNEL RESOLVE + AUTO-CREATE
    # ═══════════════════════════════════════════════════════════
    def _channel(self, guild, key: str):
        name = LOG_CHANNELS.get(key, "logs")
        return discord.utils.get(guild.text_channels, name=name)

    async def _ensure_channels(self, guild: discord.Guild):
        """Sayeb channels ila makayninx."""
        created = []
        for key, name in LOG_CHANNELS.items():
            existing = discord.utils.get(guild.text_channels, name=name)
            if existing:
                continue
            try:
                ch = await guild.create_text_channel(
                    name=name,
                    reason="Logs channel auto-created",
                    topic=f"📋 Logs — {key}",
                )
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        view_channel=False,
                        send_messages=False,
                    ),
                    guild.me: discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        embed_links=True,
                        attach_files=True,
                        read_message_history=True,
                    ),
                }
                await ch.edit(overwrites=overwrites)
                created.append(name)
                print(f"✅ #{name} tsayeb f {guild.name}")
            except discord.Forbidden:
                print(f"❌ Ma qdertch nsayeb #{name} f {guild.name} (permission)")
            except Exception as e:
                print(f"❌ Create #{name} failed: {e}")
        return created

    async def _log(self, guild, key: str, message: str):
        """Sift message f channel dyal key."""
        ch = self._channel(guild, key)
        if ch is None:
            # Fallback: sayeb daba
            created = await self._ensure_channels(guild)
            if created:
                ch = self._channel(guild, key)
        if ch is None:
            return
        try:
            await ch.send(message)
        except discord.Forbidden:
            pass
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════
    # ─── PUBLIC: Permission Denied (kayt3ayet mn app.py)
    # ═══════════════════════════════════════════════════════════
    async def log_permission_denied(self, guild, user, command_name: str):
        """Log mli chi member y7awl yst3mel command bla permission."""
        if guild is None or user is None:
            return
        msg = (
            f"🚫 **{user}** (`{user.id}`) 7awl yst3mel "
            f"`{command_name}` walakin **ma 3endouch permission**"
        )
        await self._log(guild, "general", msg)

    # ═══════════════════════════════════════════════════════════
    # ─── AUDIT LOG HELPER
    # ═══════════════════════════════════════════════════════════
    async def _fetch_audit(self, guild, action, target_id=None, timeout=3.0):
        """Rje3 (user, reason) mn audit log."""
        await asyncio.sleep(1.0)
        try:
            async for entry in guild.audit_logs(limit=10, action=action):
                if target_id is not None:
                    tgt = getattr(entry.target, "id", None)
                    if tgt != target_id:
                        continue
                return entry.user, entry.reason
        except (discord.Forbidden, discord.HTTPException):
            return None, None
        return None, None

    def _mod_text(self, user, reason: str = None) -> str:
        """Format 'par @user' + 'Reason'."""
        parts = []
        if user:
            parts.append(f"par {user.mention}")
        else:
            parts.append("par *??*")
        if reason:
            parts.append(f"— `{reason}`")
        return " ".join(parts)

    # ═══════════════════════════════════════════════════════════
    # ─── INVITE CACHE
    # ═══════════════════════════════════════════════════════════
    async def _cache_invites(self, guild):
        try:
            invites = await guild.invites()
            INVITE_CACHE[guild.id] = {inv.code: inv.uses or 0 for inv in invites}
        except (discord.Forbidden, discord.HTTPException):
            INVITE_CACHE[guild.id] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            await self._ensure_channels(guild)
            await self._cache_invites(guild)
        print(f"✅ Logs ready: {len(self.bot.guilds)} guilds")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self._ensure_channels(guild)
        await self._cache_invites(guild)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        INVITE_CACHE.setdefault(invite.guild.id, {})[invite.code] = invite.uses or 0

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        if invite.guild and invite.guild.id in INVITE_CACHE:
            INVITE_CACHE[invite.guild.id].pop(invite.code, None)

    async def _find_inviter(self, guild):
        old = INVITE_CACHE.get(guild.id, {})
        try:
            new_invites = await guild.invites()
        except (discord.Forbidden, discord.HTTPException):
            return None, None
        inviter = None
        used_code = None
        for inv in new_invites:
            if old.get(inv.code, 0) < (inv.uses or 0):
                inviter = inv.inviter
                used_code = inv.code
                break
        INVITE_CACHE[guild.id] = {inv.code: inv.uses or 0 for inv in new_invites}
        return inviter, used_code

    # ═══════════════════════════════════════════════════════════
    # ─── MEMBER JOIN
    # ═══════════════════════════════════════════════════════════
    @commands.Cog.listener()
    async def on_member_join(self, member):
        inviter, code = await self._find_inviter(member.guild)
        inv = f"mn {inviter.mention} (`{code}`)" if inviter else "**bla invite**"
        await self._log(
            member.guild, "member",
            f"📥 **{member}** dkhel l server {inv} • 👥 `{member.guild.member_count}`",
        )

    # ═══════════════════════════════════════════════════════════
    # ─── MEMBER LEAVE / KICK
    # ═══════════════════════════════════════════════════════════
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Check kick f audit log
        kicker, reason = await self._fetch_audit(
            member.guild, discord.AuditLogAction.kick, target_id=member.id
        )
        # Ila kan ban → on_member_ban ylogi
        banner, _ = await self._fetch_audit(
            member.guild, discord.AuditLogAction.ban, target_id=member.id
        )
        if banner is not None:
            return

        if kicker:
            extra = self._mod_text(kicker, reason)
            await self._log(
                member.guild, "member",
                f"👢 **{member}** t-kicka {extra} • 👥 `{member.guild.member_count}`",
            )
        else:
            await self._log(
                member.guild, "member",
                f"📤 **{member}** khrej mn server • 👥 `{member.guild.member_count}`",
            )

    # ═══════════════════════════════════════════════════════════
    # ─── MEMBER BAN / UNBAN
    # ═══════════════════════════════════════════════════════════
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        banner, reason = await self._fetch_audit(
            guild, discord.AuditLogAction.ban, target_id=user.id
        )
        extra = self._mod_text(banner, reason)
        await self._log(guild, "member", f"🔨 **{user}** t-bana {extra}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        unbanner, reason = await self._fetch_audit(
            guild, discord.AuditLogAction.unban, target_id=user.id
        )
        extra = self._mod_text(unbanner, reason)
        await self._log(guild, "member", f"✅ **{user}** t-3ta unban {extra}")

    # ═══════════════════════════════════════════════════════════
    # ─── MESSAGE DELETE
    # ═══════════════════════════════════════════════════════════
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return

        deleter, reason = await self._fetch_audit(
            message.guild, discord.AuditLogAction.message_delete,
            target_id=message.author.id, timeout=2.0
        )

        content = (message.content or "*[attachment/embed]*")[:200]
        if len(message.content or "") > 200:
            content += "..."

        if deleter and deleter.id != message.author.id:
            extra = f"par {deleter.mention}"
        else:
            extra = "par *sahbo*"

        await self._log(
            message.guild, "message",
            f"🗑️ Message dyal **{message.author.name}** t-masa7 f {message.channel.mention} {extra}\n"
            f"> `{content}`",
        )

    # ═══════════════════════════════════════════════════════════
    # ─── MESSAGE EDIT
    # ═══════════════════════════════════════════════════════════
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild:
            return
        if before.content == after.content:
            return
        await self._log(
            before.guild, "message",
            f"📝 **{before.author.name}** beddel message f {before.channel.mention}\n"
            f"> 9bel: `{(before.content or '')[:100]}`\n"
            f"> Daba: `{(after.content or '')[:100]}`",
        )

    # ═══════════════════════════════════════════════════════════
    # ─── NICKNAME / ROLES / TIMEOUT
    # ═══════════════════════════════════════════════════════════
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # ─── Nickname
        if before.nick != after.nick:
            changer, reason = await self._fetch_audit(
                after.guild, discord.AuditLogAction.member_update,
                target_id=after.id, timeout=2.0
            )
            if changer and changer.id != after.id:
                extra = f"par {changer.mention}"
            else:
                extra = "par *sahbo*"
            await self._log(
                after.guild, "member",
                f"📛 Nickname dyal **{after.name}** tbeddel: "
                f"`{before.nick or before.name}` → `{after.nick or after.name}` {extra}",
            )

        # ─── Roles
        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]

            changer, reason = await self._fetch_audit(
                after.guild, discord.AuditLogAction.member_role_update,
                target_id=after.id, timeout=2.0
            )
            extra = f"par {changer.mention}" if changer else "par *??*"
            if reason:
                extra += f" — `{reason}`"

            for r in added:
                await self._log(
                    after.guild, "member",
                    f"🎭 Role **{r.name}** t-3ta l **{after.name}** {extra}",
                )
            for r in removed:
                await self._log(
                    after.guild, "member",
                    f"🎭 Role **{r.name}** t-hyed mn **{after.name}** {extra}",
                )

        # ─── Timeout
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until:
                actor, reason = await self._fetch_audit(
                    after.guild, discord.AuditLogAction.member_update,
                    target_id=after.id, timeout=2.0
                )
                extra = self._mod_text(actor, reason)
                await self._log(
                    after.guild, "member",
                    f"🔇 **{after.name}** t-timeout until "
                    f"<t:{int(after.timed_out_until.timestamp())}:R> {extra}",
                )

    # ═══════════════════════════════════════════════════════════
    # ─── VOICE
    # ═══════════════════════════════════════════════════════════
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        # Join
        if before.channel is None and after.channel is not None:
            await self._log(
                member.guild, "voice",
                f"🔊 **{member.name}** dkhel l 🔊 `{after.channel.name}`",
            )
            return

        # Leave
        if before.channel is not None and after.channel is None:
            mover, _ = await self._fetch_audit(
                member.guild, discord.AuditLogAction.member_disconnect,
                target_id=member.id, timeout=1.5
            )
            extra = f"par {mover.mention}" if mover else "b nafso"
            await self._log(
                member.guild, "voice",
                f"🔇 **{member.name}** khrj mn 🔊 `{before.channel.name}` ({extra})",
            )
            return

        # Move
        if before.channel != after.channel:
            mover, _ = await self._fetch_audit(
                member.guild, discord.AuditLogAction.member_move,
                target_id=member.id, timeout=1.5
            )
            extra = f"par {mover.mention}" if mover else "b nafso"
            await self._log(
                member.guild, "voice",
                f"🔀 **{member.name}** t7arek mn `{before.channel.name}` → `{after.channel.name}` ({extra})",
            )

    # ═══════════════════════════════════════════════════════════
    # ─── CHANNEL CREATE / DELETE / UPDATE
    # ═══════════════════════════════════════════════════════════
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        creator, reason = await self._fetch_audit(
            channel.guild, discord.AuditLogAction.channel_create,
            target_id=channel.id, timeout=2.0
        )
        extra = self._mod_text(creator, reason)
        await self._log(
            channel.guild, "channel",
            f"📢 Channel **{channel.name}** tsayeb {extra}",
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        deleter, reason = await self._fetch_audit(
            channel.guild, discord.AuditLogAction.channel_delete,
            target_id=channel.id, timeout=2.0
        )
        extra = self._mod_text(deleter, reason)
        await self._log(
            channel.guild, "channel",
            f"🗑️ Channel **{channel.name}** t-masa7 {extra}",
        )

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        changes = []
        if before.name != after.name:
            changes.append(f"smiya: `{before.name}` → `{after.name}`")
        if getattr(before, "topic", None) != getattr(after, "topic", None):
            changes.append("topic")
        if getattr(before, "slowmode_delay", None) != getattr(after, "slowmode_delay", None):
            changes.append(f"slowmode: `{before.slowmode_delay}s` → `{after.slowmode_delay}s`")
        if getattr(before, "nsfw", None) != getattr(after, "nsfw", None):
            changes.append(f"nsfw: `{before.nsfw}` → `{after.nsfw}`")
        if getattr(before, "user_limit", None) != getattr(after, "user_limit", None):
            changes.append(f"limit: `{before.user_limit}` → `{after.user_limit}`")

        if not changes:
            return

        updater, reason = await self._fetch_audit(
            after.guild, discord.AuditLogAction.channel_update,
            target_id=after.id, timeout=2.0
        )
        extra = self._mod_text(updater, reason)
        await self._log(
            after.guild, "channel",
            f"🔧 Channel **{after.name}** t-beddel ({', '.join(changes)}) {extra}",
        )

    # ═══════════════════════════════════════════════════════════
    # ─── ROLE CREATE / DELETE / UPDATE
    # ═══════════════════════════════════════════════════════════
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        creator, reason = await self._fetch_audit(
            role.guild, discord.AuditLogAction.role_create,
            target_id=role.id, timeout=2.0
        )
        extra = self._mod_text(creator, reason)
        await self._log(
            role.guild, "channel",
            f"🎭 Role **{role.name}** tsayeb {extra}",
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        deleter, reason = await self._fetch_audit(
            role.guild, discord.AuditLogAction.role_delete,
            target_id=role.id, timeout=2.0
        )
        extra = self._mod_text(deleter, reason)
        await self._log(
            role.guild, "channel",
            f"🗑️ Role **{role.name}** t-masa7 {extra}",
        )

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        changes = []
        if before.name != after.name:
            changes.append(f"smiya: `{before.name}` → `{after.name}`")
        if before.color != after.color:
            changes.append(f"color: `{before.color}` → `{after.color}`")
        if before.hoist != after.hoist:
            changes.append("hoist")
        if before.mentionable != after.mentionable:
            changes.append("mentionable")
        if before.permissions != after.permissions:
            changes.append("permissions")

        if not changes:
            return

        updater, reason = await self._fetch_audit(
            after.guild, discord.AuditLogAction.role_update,
            target_id=after.id, timeout=2.0
        )
        extra = self._mod_text(updater, reason)
        await self._log(
            after.guild, "channel",
            f"🎭 Role **{after.name}** t-beddel ({', '.join(changes)}) {extra}",
        )


async def setup(bot):
    await bot.add_cog(Logs(bot))