# cogs/server_setup.py
"""Auto-create categories, channels, roles + fix hierarchy/colors/perms + dedup."""
import discord
from discord.ext import commands
import asyncio
import re


# ═══════════════════════════════════════════════════════════════════
# ─── ROLE HIERARCHY (top → bottom)
# ═══════════════════════════════════════════════════════════════════
ROLE_HIERARCHY = [
    # ═══ 1. OWNERSHIP ═══
    {"name": "👑 𝓕𝓸𝓾𝓷𝓭𝓮𝓻", "color": 0xE91E63, "tier": "owner", "hoist": True, "mentionable": False},

    # ═══ 2. ADMIN TEAM ═══
    {"name": "Majesty", "color": 0xFFD700, "tier": "admin", "hoist": True},
    {"name": "⚜️ Community Manager", "color": 0x9B59B6, "tier": "admin", "hoist": True},
    {"name": "🛡️ Administrator", "color": 0xE74C3C, "tier": "admin", "hoist": True},

    # ═══ 3. MODERATION ═══
    {"name": "🔰 Superviseur", "color": 0xE67E22, "tier": "mod", "hoist": True},
    {"name": "🔨 Moderator", "color": 0xA0522D, "tier": "mod", "hoist": True},
    {"name": "🗡️ Helper", "color": 0x1ABC9C, "tier": "helper", "hoist": True},
    {"name": "⚔️ staff team", "color": 0x546E7A, "tier": "helper", "hoist": True},

    # ═══ 4. WARNINGS ═══
    {"name": "❗ First Warning", "color": 0xFFA500, "tier": "warn", "hoist": False, "mentionable": False},
    {"name": "❗ Second Warning", "color": 0xFF6600, "tier": "warn", "hoist": False, "mentionable": False},
    {"name": "❗ Last Warning", "color": 0xFF0000, "tier": "warn", "hoist": False, "mentionable": False},
    {"name": "9wad", "color": 0x2C2F33, "tier": "warn", "hoist": False, "mentionable": False},

    # ═══ 5. SPECIAL / PREMIUM ═══
    {"name": "👑 God", "color": 0xE91E63, "tier": "special", "hoist": True},
    {"name": "🏆 Legend", "color": 0xFF9800, "tier": "special", "hoist": True},
    {"name": "⭐ Premium", "color": 0xFFEB3B, "tier": "special", "hoist": True},
    {"name": "💎 VIP", "color": 0x00BCD4, "tier": "special", "hoist": True},
    {"name": "👑 The Boss", "color": 0xFFD700, "tier": "special", "hoist": True},
    {"name": "Casino Owner ♠️", "color": 0xE74C3C, "tier": "special", "hoist": True},
    {"name": "🎰 Casino Manager", "color": 0xFF5722, "tier": "special", "hoist": False},
    {"name": "🎰 Casino Player", "color": 0x9C27B0, "tier": "special", "hoist": False},

    # ═══ 6. VERIFICATION ═══
    {"name": "Verified ✓", "color": 0x43B581, "tier": "verify", "hoist": False},
    {"name": "💖 Verified Female", "color": 0xE91E63, "tier": "verify", "hoist": False},
    {"name": "Unverified", "color": 0x99AAB5, "tier": "verify", "hoist": False},

    # ═══ 7. PERSONAL / SELF-ASSIGNED ═══
    {"name": "+18", "color": 0x2C2F33, "tier": "self", "hoist": False},
    {"name": "-18", "color": 0x2C2F33, "tier": "self", "hoist": False},
    {"name": "💖 girl", "color": 0xE91E63, "tier": "self", "hoist": False},
    {"name": "Man 👔", "color": 0x3498DB, "tier": "self", "hoist": False},
    {"name": "🔒 en couple", "color": 0xE91E63, "tier": "self", "hoist": False},
    {"name": "🔓 single", "color": 0x9B59B6, "tier": "self", "hoist": False},

    # ═══ 8. GAMES ═══
    {"name": "VALORANT", "color": 0xFF4655, "tier": "game", "hoist": False},
    {"name": "FREE FIRE", "color": 0xFF5722, "tier": "game", "hoist": False},
    {"name": "PES", "color": 0x4CAF50, "tier": "game", "hoist": False},
    {"name": "AMONG US", "color": 0xFF0000, "tier": "game", "hoist": False},
    {"name": "ROBLOX", "color": 0xE74C3C, "tier": "game", "hoist": False},
    {"name": "CODENAMES", "color": 0xFFC107, "tier": "game", "hoist": False},

    # ═══ 9. REGIONS ═══
    {"name": "🇲🇦 Morocco", "color": 0xC8102E, "tier": "region", "hoist": False},
    {"name": "🌍 MENA", "color": 0xE67E22, "tier": "region", "hoist": False},
    {"name": "🇪🇺 Europe", "color": 0x003399, "tier": "region", "hoist": False},

    # ═══ 10. NOTIFICATIONS ═══
    {"name": "🔔 Ping: Events", "color": 0xFFD700, "tier": "notif", "hoist": False},
    {"name": "🔔 Ping: Giveaways", "color": 0xFFD700, "tier": "notif", "hoist": False},
    {"name": "🔔 Ping: Anime", "color": 0x9B59B6, "tier": "notif", "hoist": False},
    {"name": "🔔 Ping: Gaming", "color": 0x3498DB, "tier": "notif", "hoist": False},

    # ═══ 11. ACHIEVEMENTS ═══
    {"name": "💎 Millionaire", "color": 0xB9F2FF, "tier": "achievement", "hoist": False},
    {"name": "🔥 Grinder", "color": 0xFF5722, "tier": "achievement", "hoist": False},
    {"name": "🥷 Thief", "color": 0x424242, "tier": "achievement", "hoist": False},
    {"name": "🎰 Gambling Addict", "color": 0x8B0000, "tier": "achievement", "hoist": False},
    {"name": "✨ Best Member", "color": 0xFFEB3B, "tier": "achievement", "hoist": False},

    # ═══ 12. LANGUAGE ═══
    {"name": "🇲🇦 Darija", "color": 0xC8102E, "tier": "lang", "hoist": False},
    {"name": "🇬🇧 English", "color": 0x012169, "tier": "lang", "hoist": False},
    {"name": "🇫🇷 Français", "color": 0x0055A4, "tier": "lang", "hoist": False},

    # ═══ 13. MISC ═══
    {"name": "🎬 Content Creator", "color": 0x9B59B6, "tier": "misc", "hoist": False},
    {"name": "🚫 Access", "color": 0xE74C3C, "tier": "misc", "hoist": False, "mentionable": False},
]


# ═══════════════════════════════════════════════════════════════════
# ─── PERMISSIONS PER TIER
# ═══════════════════════════════════════════════════════════════════
ROLE_PERMISSIONS = {
    "owner": discord.Permissions.all(),
    "admin": discord.Permissions(administrator=True),
    "mod": discord.Permissions(
        kick_members=True, ban_members=True,
        manage_messages=True, moderate_members=True,
        mute_members=True, deafen_members=True, move_members=True,
        view_audit_log=True, manage_nicknames=True,
        view_channel=True, send_messages=True,
        read_message_history=True, add_reactions=True,
        embed_links=True, attach_files=True,
    ),
    "helper": discord.Permissions(
        manage_messages=True, moderate_members=True,
        mute_members=True, deafen_members=True, move_members=True,
        view_channel=True, send_messages=True,
        read_message_history=True, add_reactions=True,
    ),
    "warn": discord.Permissions(
        view_channel=True, read_message_history=True,
    ),
    "special": discord.Permissions(
        view_channel=True, send_messages=True,
        read_message_history=True, add_reactions=True,
        embed_links=True, attach_files=True,
        use_external_emojis=True,
    ),
    "verify": discord.Permissions(
        view_channel=True, send_messages=True,
        read_message_history=True, add_reactions=True,
        embed_links=True, attach_files=True,
    ),
    "self":        discord.Permissions.none(),
    "game":        discord.Permissions.none(),
    "region":      discord.Permissions.none(),
    "notif":       discord.Permissions.none(),
    "achievement": discord.Permissions.none(),
    "lang":        discord.Permissions.none(),
    "misc":        discord.Permissions.none(),
}


# ═══════════════════════════════════════════════════════════════════
# ─── CATEGORIES + CHANNELS
#     Structure: {category_name: [channel_name, ...]}
#     • channel starts with "🔒" → admin only (view denied @everyone)
#     • channel starts with "📖" → read-only (@everyone can't send)
#     • channel starts with "🎮" → normal text channel
# ═══════════════════════════════════════════════════════════════════
NEW_CATEGORIES = {
    # ═══ EXISTING ═══
    "📋 INFORMATION": ["📖bot-guide", "📖faq", "📖about"],
    "💰 ECONOMY HUB": ["🎮shop", "🎮daily", "📖rich-list", "🎮market-watch"],
    "🎁 EVENTS": ["🎮giveaways", "🎮tournaments", "📖event-winners", "🎮event-chat"],
    "🎯 MATCHMAKING": ["🎮looking-for-group", "🎮scrim-finder", "📖match-results"],
    "🎓 TUTORIALS": ["📖bot-tutorial", "📖commands-guide"],
    "💼 JOBS": ["🎮looking-for-team", "🎮offering-services"],
    "🎬 CONTENT": ["🎮youtube", "🎮tiktok"],
    "🌍 LANGUAGES": ["🎮english-practice", "🎮french-practice", "🎮darija-only"],
    "📸 SUGGESTIONS": ["🎮suggestions", "🎮bug-reports", "🎮feedback"],
    "🏆 TOURNAMENTS": ["📖brackets", "📖results"],

    # ═══ NEW (l cogs jdad) ═══
    "🔢 COUNTING": ["🎮counting"],
    "🎭 ROLEPLAY": ["🎮roleplay"],
    "📊 ACTIVITY": ["🎮activity-top", "📖activity-weekly"],
    "🕵️ CONFESSIONS": ["🎮confessions"],
    "⭐ STARBOARD": ["📖starboard"],
    "📋 MODERATION": ["🔒mod-cases"],
    "🎂 BIRTHDAYS": ["🎮birthdays"],
}


# ═══════════════════════════════════════════════════════════════════
# ─── CHANNEL OVERWRITES (per prefix)
# ═══════════════════════════════════════════════════════════════════
def _channel_overwrites(guild, prefix: str):
    """Rje3 dict dyal overwrites 7sab prefix."""
    default = guild.default_role
    if prefix == "🔒":
        # Admin only
        return {
            default: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
    if prefix == "📖":
        # Read-only
        return {
            default: discord.PermissionOverwrite(
                view_channel=True, send_messages=False,
                add_reactions=True, read_message_history=True,
            ),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
    # 🎮 normal
    return None


class ServerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════════════════════════
    # ─── HELPER: normalize name
    # ═══════════════════════════════════════════════════════════
    @staticmethod
    def _norm(name: str) -> str:
        name = re.sub(r'[^\w\s\u0600-\u06FF]', '', name, flags=re.UNICODE)
        name = ' '.join(name.split())
        return name.lower().strip()

    @staticmethod
    def _clean_channel_name(name: str) -> str:
        """Hyed prefix 🔒 / 📖 / 🎮 mn smiya dyal channel."""
        for p in ("🔒", "📖", "🎮"):
            if name.startswith(p):
                return name[len(p):], p
        return name, "🎮"

    def _find_roles_by_norm(self, guild, target_name: str):
        key = self._norm(target_name)
        result = []
        for role in guild.roles:
            if role.is_default() or role.managed:
                continue
            if self._norm(role.name) == key:
                result.append(role)
        return result

    # ═══════════════════════════════════════════════════════════
    # ─── +setserver — Categories + Channels + Roles
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="setserver")
    @commands.has_permissions(administrator=True)
    async def setserver(self, ctx, confirm: str = None):
        """+setserver confirm — Sayeb categories/channels/roles"""
        if confirm != "confirm":
            return await ctx.send(
                "⚠️ `+setserver confirm` bash tbda!\n"
                "Ghadi yzid **~40 channels** w roles jdad.\n"
                "Mor ma ysali, st3mel `+fixroles confirm` bash yrtbhom."
            )

        status = await ctx.send("⏳ Kaytcrea...")
        created_ch = created_cat = created_r = 0
        skipped_r = 0

        # ─── Roles
        for role_data in ROLE_HIERARCHY:
            name = role_data["name"]
            existing = self._find_roles_by_norm(ctx.guild, name)
            if existing:
                skipped_r += 1
                continue
            try:
                await ctx.guild.create_role(
                    name=name,
                    color=discord.Color(role_data["color"]),
                    hoist=role_data.get("hoist", False),
                    mentionable=role_data.get("mentionable", False),
                    reason="+setserver",
                )
                created_r += 1
                await asyncio.sleep(0.3)
            except Exception:
                pass

        # ─── Categories + Channels
        existing_cats = {c.name for c in ctx.guild.categories}
        for cat_name, channels in NEW_CATEGORIES.items():
            if cat_name in existing_cats:
                cat = discord.utils.get(ctx.guild.categories, name=cat_name)
            else:
                try:
                    cat = await ctx.guild.create_category(cat_name, reason="+setserver")
                    created_cat += 1
                except Exception:
                    continue

            existing_ch = {c.name for c in cat.channels}
            for raw_name in channels:
                clean_name, prefix = self._clean_channel_name(raw_name)
                if clean_name in existing_ch:
                    continue
                try:
                    overwrites = _channel_overwrites(ctx.guild, prefix)
                    if overwrites:
                        await ctx.guild.create_text_channel(
                            clean_name, category=cat, overwrites=overwrites,
                            reason="+setserver",
                        )
                    else:
                        await ctx.guild.create_text_channel(
                            clean_name, category=cat,
                            reason="+setserver",
                        )
                    created_ch += 1
                    await asyncio.sleep(0.4)
                except Exception:
                    pass

        await status.edit(content=(
            f"✅ **Done!**\n"
            f"📁 Categories: `{created_cat}`\n"
            f"💬 Channels: `{created_ch}`\n"
            f"🎭 Roles jdad: `{created_r}`\n"
            f"⏭️ Skipped (already exist): `{skipped_r}`\n\n"
            f"💡 **Next:**\n"
            f"1. `+duproles` — Chouf duplicates\n"
            f"2. `+cleandroles confirm` — Msa7 duplicates\n"
            f"3. `+fixroles confirm` — Colors + Perms + Tartib\n"
            f"4. `+counting setup #counting` — Bda counting game"
        ))

    # ═══════════════════════════════════════════════════════════
    # ─── +duproles — Detect duplicates
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="duproles", aliases=["finddups", "rolesdup"])
    @commands.has_permissions(administrator=True)
    async def duproles(self, ctx):
        """+duproles — Chouf roles mكررين (bla ma ymsa7)"""
        guild = ctx.guild
        me = guild.get_member(self.bot.user.id)
        bot_top = me.top_role.position if me else 0

        groups: dict[str, list[discord.Role]] = {}
        for role in guild.roles:
            if role.is_default() or role.managed:
                continue
            if role.position >= bot_top:
                continue
            key = self._norm(role.name)
            groups.setdefault(key, []).append(role)

        dups = {k: v for k, v in groups.items() if len(v) > 1}

        if not dups:
            return await ctx.send("✅ **Ma kaynch duplicates!** Kolchi nadi.")

        embed = discord.Embed(
            title="🔍 Duplicates Found",
            description=f"`{len(dups)}` groups mكررين — **`+cleandroles confirm`** bash tmsa7hom",
            color=discord.Color.orange(),
        )

        total_extra = 0
        for key, roles in sorted(dups.items(), key=lambda x: -len(x[1])):
            roles.sort(key=lambda r: (-len(r.members), r.position), reverse=True)
            keep = roles[0]
            extras = roles[1:]
            total_extra += len(extras)

            lines = [f"✅ KEEP: **{keep.name}** — `{len(keep.members)}` members (pos {keep.position})"]
            for r in extras:
                lines.append(f"❌ DUP: **{r.name}** — `{len(r.members)}` members (pos {r.position})")

            embed.add_field(
                name=f"📛 `{keep.name}` ({len(roles)}×)",
                value="\n".join(lines[:8]),
                inline=False,
            )

        embed.set_footer(text=f"Total li ghadi ytmsa7: {total_extra} roles")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── +cleandroles — Delete duplicates
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="cleandroles", aliases=["removedups", "dupdell"])
    @commands.has_permissions(administrator=True)
    async def cleandroles(self, ctx, confirm: str = None):
        """+cleandroles confirm — Msa7 roles mكررين"""
        if confirm != "confirm":
            return await ctx.send(
                "⚠️ **`+cleandroles confirm`** bash tbda!\n"
                "Ghadi ymsa7 **roles mكرrين** (kayb9a wa7ed f kol group).\n"
                "💡 Chouf 9bel: `+duproles`"
            )

        status = await ctx.send("⏳ Kan-mse7 duplicates...")

        guild = ctx.guild
        me = guild.get_member(self.bot.user.id)
        bot_top = me.top_role.position if me else 0

        groups: dict[str, list[discord.Role]] = {}
        for role in guild.roles:
            if role.is_default() or role.managed:
                continue
            if role.position >= bot_top:
                continue
            key = self._norm(role.name)
            groups.setdefault(key, []).append(role)

        dups = {k: v for k, v in groups.items() if len(v) > 1}

        if not dups:
            return await status.edit(content="✅ **Ma kaynch duplicates!**")

        deleted = 0
        failed = 0

        for key, roles in dups.items():
            roles.sort(key=lambda r: (-len(r.members), -r.position))
            extras = roles[1:]

            for role in extras:
                try:
                    await role.delete(reason=f"Duplicate cleanup by {ctx.author}")
                    deleted += 1
                    await asyncio.sleep(0.6)
                except discord.Forbidden:
                    failed += 1
                except Exception:
                    failed += 1

        embed = discord.Embed(
            title="✅ Duplicates Cleared",
            color=discord.Color.green(),
        )
        embed.add_field(name="🗑️ Deleted", value=f"`{deleted}` roles", inline=True)
        embed.add_field(name="❌ Failed", value=f"`{failed}`", inline=True)
        embed.add_field(name="📊 Groups", value=f"`{len(dups)}`", inline=True)
        embed.set_footer(text="St3mel +fixroles confirm bash t-rtb l-ba9i")
        await status.edit(content=None, embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── +fixroles — Colors + Perms + Hierarchy
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="fixroles", aliases=["reorderroles", "rolefix"])
    @commands.has_permissions(administrator=True)
    async def fixroles(self, ctx, confirm: str = None):
        """+fixroles confirm — Appliqui colors + perms + tartib"""
        if confirm != "confirm":
            embed = discord.Embed(
                title="⚠️ +fixroles — Confirmation",
                description=(
                    "Had command ghadi ydir **3 7wayj**:\n\n"
                    "🎨 **Colors** — kol role yjib color dyalo\n"
                    "🔐 **Permissions** — kol tier ykhod perms dyalo\n"
                    "📊 **Tartib** — hierarchy mn l-fo9 l-te7t\n\n"
                    f"**Total roles:** `{len(ROLE_HIERARCHY)}`\n"
                    f"**Sa3a:** ~1 minute\n\n"
                    "**`+fixroles confirm`** bash tbda"
                ),
                color=discord.Color.orange(),
            )
            return await ctx.send(embed=embed)

        status = await ctx.send("⏳ Kan-fixi roles... (`~1min`)")

        guild = ctx.guild
        me = guild.get_member(self.bot.user.id)
        if me is None:
            return await status.edit(content="❌ Bot member ma kaynch!")
        bot_top = me.top_role.position

        matched = []
        missing = []
        for rd in ROLE_HIERARCHY:
            candidates = self._find_roles_by_norm(guild, rd["name"])
            candidates = [
                r for r in candidates
                if not r.managed and r.position < bot_top
            ]
            if not candidates:
                missing.append(rd["name"])
                continue
            role = max(candidates, key=lambda r: r.position)
            matched.append((role, rd))

        if not matched:
            return await status.edit(content="❌ Ma l9itch roles li n9der n-editihom!")

        ok_edit = 0
        for role, rd in matched:
            perms = ROLE_PERMISSIONS.get(rd["tier"], discord.Permissions.none())
            try:
                await role.edit(
                    color=discord.Color(rd["color"]),
                    permissions=perms,
                    hoist=rd.get("hoist", False),
                    mentionable=rd.get("mentionable", False),
                    reason="+fixroles",
                )
                ok_edit += 1
            except discord.Forbidden:
                pass
            except Exception:
                pass
            await asyncio.sleep(0.5)

        start_pos = bot_top - 1
        reordered = 0
        for i, (role, rd) in enumerate(matched):
            target = start_pos - i
            if target < 1:
                break
            try:
                await role.edit(position=target, reason="+fixroles reorder")
                reordered += 1
            except Exception:
                pass
            await asyncio.sleep(0.7)

        embed = discord.Embed(
            title="✅ +fixroles — Done!",
            color=discord.Color.green(),
            description="Roles daba **mrattbin** + **colors** + **perms** ✅",
        )
        embed.add_field(name="🎨 Edited", value=f"`{ok_edit}` roles", inline=True)
        embed.add_field(name="📊 Reordered", value=f"`{reordered}` roles", inline=True)
        embed.add_field(name="⚠️ Missing", value=f"`{len(missing)}` roles", inline=True)

        if missing:
            m_str = ", ".join(f"`{m}`" for m in missing[:15])
            if len(missing) > 15:
                m_str += f" +{len(missing) - 15} khrin"
            embed.add_field(name="❌ Roles ma kaynin", value=m_str, inline=False)

        embed.set_footer(text=f"Bot top position: {bot_top}")
        await status.edit(content=None, embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── +setcolors
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="setcolors", aliases=["rolecolors"])
    @commands.has_permissions(administrator=True)
    async def setcolors(self, ctx):
        """+setcolors — Colors only"""
        status = await ctx.send("🎨 Kan-appliqui colors...")
        ok = skipped = 0
        for rd in ROLE_HIERARCHY:
            candidates = self._find_roles_by_norm(ctx.guild, rd["name"])
            candidates = [r for r in candidates if not r.managed]
            if not candidates:
                skipped += 1
                continue
            role = max(candidates, key=lambda r: r.position)
            try:
                await role.edit(color=discord.Color(rd["color"]), reason="+setcolors")
                ok += 1
            except Exception:
                skipped += 1
            await asyncio.sleep(0.3)
        await status.edit(content=f"🎨 Colors: `{ok}` applied • `{skipped}` skipped")

    # ═══════════════════════════════════════════════════════════
    # ─── +setperms
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="setperms", aliases=["roleperms"])
    @commands.has_permissions(administrator=True)
    async def setperms(self, ctx):
        """+setperms — Permissions only"""
        status = await ctx.send("🔐 Kan-appliqui permissions...")
        ok = skipped = 0
        for rd in ROLE_HIERARCHY:
            candidates = self._find_roles_by_norm(ctx.guild, rd["name"])
            candidates = [r for r in candidates if not r.managed]
            if not candidates:
                skipped += 1
                continue
            role = max(candidates, key=lambda r: r.position)
            perms = ROLE_PERMISSIONS.get(rd["tier"], discord.Permissions.none())
            try:
                await role.edit(permissions=perms, reason="+setperms")
                ok += 1
            except Exception:
                skipped += 1
            await asyncio.sleep(0.4)
        await status.edit(content=f"🔐 Permissions: `{ok}` applied • `{skipped}` skipped")

    # ═══════════════════════════════════════════════════════════
    # ─── +rolesinfo
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="rolesinfo", aliases=["rhier"])
    @commands.has_permissions(administrator=True)
    async def rolesinfo(self, ctx):
        """+rolesinfo — Preview dyal hierarchy"""
        embed = discord.Embed(
            title="📊 Role Hierarchy Preview",
            description="Had l-lista hiya **l-tartib** li ghadi ykoun (top → bottom)",
            color=discord.Color.blurple(),
        )
        lines = []
        for i, rd in enumerate(ROLE_HIERARCHY, 1):
            candidates = self._find_roles_by_norm(ctx.guild, rd["name"])
            count = len(candidates)
            if count == 0:
                mark = "❌"
            elif count == 1:
                mark = "✅"
            else:
                mark = f"⚠️ x{count}"
            lines.append(f"`{i:2}.` {mark} {rd['name']} — `{rd['tier']}`")

        half = (len(lines) + 1) // 2
        embed.add_field(name="\u200b", value="\n".join(lines[:half]), inline=True)
        embed.add_field(name="\u200b", value="\n".join(lines[half:]), inline=True)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ServerSetup(bot))