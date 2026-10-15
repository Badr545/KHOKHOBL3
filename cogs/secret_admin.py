# cogs/secret_admin.py
# =====================================================================
# ─── SECRET ADMIN PANEL v3.5 — + SHOP + COMMAND MANAGER + AUTO REPLY
# =====================================================================
import os
import re
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

import botconfig
from data_manager import (
    ECONOMY, LEVELS, BIR, WARNINGS,
    save_economy, save_levels, save_bir, save_warnings,
)

# ═══════════════════════════════════════════════════════════════════
# ─── CONFIG SIRRI
# ═══════════════════════════════════════════════════════════════════
SECRET_TRIGGER = os.getenv("SECRET_TRIGGER", "khokho-panel")
MODPASS = os.getenv("MODPASS", "!XxKLoc0@^MP@z@%iUOX")

UNLOCKED: dict[int, float] = {}
SESSION_DURATION = 3600
AUDIT_LOG: list[dict] = []

IMAGE_URL_RE = re.compile(
    r"^https?://\S+\.(?:png|jpg|jpeg|gif|webp|bmp)(?:\?\S*)?$",
    re.IGNORECASE,
)

COG_MAP = {
    "basic": "cogs.basic", "admin": "cogs.admin", "announcements": "cogs.announcements",
    "roles": "cogs.roles", "economy": "cogs.economy", "gambling": "cogs.gambling",
    "games": "cogs.games", "bir": "cogs.bir", "levels": "cogs.levels",
    "rankcard": "cogs.rankcard", "leaderboard": "cogs.leaderboard",
    "shop": "cogs.shop", "info": "cogs.info", "utility": "cogs.utility",
    "help": "cogs.help", "logs": "cogs.logs", "welcome": "cogs.welcome",
    "stats": "cogs.stats", "tempvoice": "cogs.tempvoice", "voice": "cogs.voice",
    "roleconfig": "cogs.roleconfig",
    "automod": "cogs.automod", "tickets": "cogs.tickets", "tempban": "cogs.tempban",
    "giveaway": "cogs.giveaway", "embedbuilder": "cogs.embedbuilder",
    "reactionroles": "cogs.reactionroles", "channelmanager": "cogs.channelmanager",
    "backup_restore": "cogs.backup_restore", "customcommands": "cogs.customcommands",
    "cmd_overrides": "cogs.cmd_overrides",
    "auto_responses": "cogs.auto_responses",
    "insights": "cogs.insights",
    "selfroles": "cogs.selfroles",
}


def _is_unlocked(user_id: int) -> bool:
    ts = UNLOCKED.get(user_id)
    if ts is None:
        return False
    if datetime.now().timestamp() - ts > SESSION_DURATION:
        UNLOCKED.pop(user_id, None)
        return False
    return True


def _is_real_admin(member: discord.Member) -> bool:
    if member is None:
        return False
    if member.guild is None:
        return False
    if member.id == member.guild.owner_id:
        return True
    names = {r.name for r in member.roles}
    ids = {r.id for r in member.roles}
    for r in botconfig.ADMIN_ROLES:
        if r in names:
            return True
        rid = botconfig.ROLE_NAME_TO_ID.get(r)
        if rid and rid in ids:
            return True
    return False


def _audit(actor, action: str, details: str = ""):
    AUDIT_LOG.append({
        "actor": f"{actor} ({actor.id})",
        "action": action,
        "details": details,
        "time": datetime.now().isoformat(),
    })
    AUDIT_LOG[:] = AUDIT_LOG[-500:]


def _automod_api():
    try:
        from cogs.automod import get_config, _save as save_am, AUTOMOD
        return get_config, save_am, AUTOMOD
    except Exception as e:
        print(f"⚠️ automod import fail: {e}")
        return None, None, None


def _shop_api():
    try:
        from cogs.shop import get_shop_items, add_shop_item, remove_shop_item
        return get_shop_items, add_shop_item, remove_shop_item
    except Exception as e:
        print(f"⚠️ shop import fail: {e}")
        return None, None, None


try:
    from cogs.shop import SHOP_ITEMS
except Exception:
    SHOP_ITEMS = {}


# ═══════════════════════════════════════════════════════════════════
# ─── PANEL MAIN
# ═══════════════════════════════════════════════════════════════════
class SecretPanel(discord.ui.View):
    def __init__(self, cog, user_id: int, guild_id: int):
        super().__init__(timeout=600)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id

    async def interaction_check(self, it: discord.Interaction) -> bool:
        if it.user.id != self.user_id:
            await it.response.send_message("❌ Machi dyalek!", ephemeral=True)
            return False
        if not _is_unlocked(it.user.id):
            await it.response.send_message("🔒 Session salat!", ephemeral=True)
            return False
        return True

    def _guild(self):
        return self.cog.bot.get_guild(self.guild_id)

    # ═══════════════════════════════════════════════════════════
    # ─── ROW 0
    # ═══════════════════════════════════════════════════════════
    @discord.ui.button(label="Roles", emoji="🎭", style=discord.ButtonStyle.primary, row=0)
    async def roles_btn(self, it, b):
        embed = discord.Embed(title="🎭 Roles", color=discord.Color.purple())
        embed.add_field(name="👑 ADMIN", value="\n".join(f"`{r}`" for r in botconfig.ADMIN_ROLES) or "—", inline=False)
        embed.add_field(name="🛡️ MOD", value="\n".join(f"`{r}`" for r in botconfig.MODERATOR_ROLES) or "—", inline=False)
        embed.add_field(name="💚 HELPER", value="\n".join(f"`{r}`" for r in botconfig.HELPER_ROLES) or "—", inline=False)
        await it.response.send_message(
            embed=embed,
            view=RolesPanel(self.cog, self.user_id, self.guild_id),
            ephemeral=True,
        )

    @discord.ui.button(label="Perms", emoji="🔑", style=discord.ButtonStyle.primary, row=0)
    async def perms_btn(self, it, b):
        embed = discord.Embed(title="🔑 Perms", color=discord.Color.gold())
        for cat, data in botconfig.COMMAND_PERMISSIONS.items():
            embed.add_field(
                name=f"{cat} ({len(data['commands'])})",
                value=f"Roles: {', '.join(f'`{r}`' for r in data['roles']) or 'public'}",
                inline=False,
            )
        await it.response.send_message(embed=embed, view=PermsPanel(self.cog, self.user_id), ephemeral=True)

    @discord.ui.button(label="Config", emoji="⚙️", style=discord.ButtonStyle.secondary, row=0)
    async def config_btn(self, it, b):
        await it.response.send_message(
            embed=self.cog._config_embed(),
            view=ConfigPanel(self.cog, self.user_id),
            ephemeral=True,
        )

    @discord.ui.button(label="Audit", emoji="📜", style=discord.ButtonStyle.secondary, row=0)
    async def audit_btn(self, it, b):
        if not AUDIT_LOG:
            return await it.response.send_message("📜 Khawi.", ephemeral=True)
        lines = [
            f"`{e['time'][11:19]}` **{e['actor'].split(' ')[0]}** → `{e['action']}` {e['details']}"
            for e in AUDIT_LOG[-15:]
        ]
        await it.response.send_message("📜 **Audit:**\n" + "\n".join(lines), ephemeral=True)

    @discord.ui.button(label="Commands", emoji="✏️", style=discord.ButtonStyle.primary, row=0)
    async def commands_btn(self, it, b):
        try:
            from cogs.cmd_overrides import CommandManagerPanel
        except Exception as e:
            return await it.response.send_message(
                f"❌ CmdOverrides machi loaded! `{e}`",
                ephemeral=True,
            )
        await it.response.send_message(
            "✏️ **Command Manager**\n"
            "Beddel smiyat dyal commands (aliases):\n\n"
            "• **Rename** — Zid alias jdid (ex: `kick` → `kherrej`)\n"
            "• **Remove** — Hyed alias\n"
            "• **List** — Chouf kol aliases\n"
            "• **Clear** — Hyed kolchi\n\n"
            "💡 Alias kaykhdem b nafs prefix dyal original",
            view=CommandManagerPanel(self.guild_id),
            ephemeral=True,
        )

    # ═══════════════════════════════════════════════════════════
    # ─── ROW 1
    # ═══════════════════════════════════════════════════════════
    @discord.ui.button(label="AutoMod", emoji="🛡️", style=discord.ButtonStyle.success, row=1)
    async def automod_btn(self, it, b):
        get_config, _, _ = _automod_api()
        if get_config is None:
            return await it.response.send_message("❌ AutoMod machi loaded!", ephemeral=True)
        await it.response.send_message(
            embed=self.cog._automod_embed(self.guild_id),
            view=AutoModPanel(self.cog, self.user_id, self.guild_id),
            ephemeral=True,
        )

    @discord.ui.button(label="Tickets", emoji="🎫", style=discord.ButtonStyle.success, row=1)
    async def tickets_btn(self, it, b):
        await it.response.send_message(
            embed=discord.Embed(
                title="🎫 Tickets",
                description="Setup wla manage tickets:",
                color=discord.Color.blurple(),
            ),
            view=TicketsPanel(self.cog, self.user_id, self.guild_id),
            ephemeral=True,
        )

    @discord.ui.button(label="TempBan", emoji="⏱️", style=discord.ButtonStyle.success, row=1)
    async def tempban_btn(self, it, b):
        await it.response.send_modal(TempBanModal(self.cog, self.guild_id))

    # ═══════════════════════════════════════════════════════════
    # ─── ROW 2
    # ═══════════════════════════════════════════════════════════
    @discord.ui.button(label="Giveaway", emoji="🎁", style=discord.ButtonStyle.success, row=2)
    async def giveaway_btn(self, it, b):
        await it.response.send_modal(GiveawayModal(self.cog, self.guild_id))

    @discord.ui.button(label="Embed", emoji="🎨", style=discord.ButtonStyle.success, row=2)
    async def embed_btn(self, it, b):
        guild = self._guild()
        if guild is None:
            return await it.response.send_message("❌ Guild ma kaynch!", ephemeral=True)
        await it.response.send_message(
            "🎨 Embed builder:",
            view=EmbedChannelPanel(self.cog, self.user_id, guild),
            ephemeral=True,
        )

    @discord.ui.button(label="React Roles", emoji="📌", style=discord.ButtonStyle.success, row=2)
    async def rr_btn(self, it, b):
        await it.response.send_modal(ReactRolesModal(self.cog, self.guild_id))

    @discord.ui.button(label="Announce", emoji="📢", style=discord.ButtonStyle.primary, row=2)
    async def announce_btn(self, it, b):
        await it.response.send_modal(AnnounceModal(self.cog, self.guild_id))

    # ═══════════════════════════════════════════════════════════
    # ─── ROW 3
    # ═══════════════════════════════════════════════════════════
    @discord.ui.button(label="Channels", emoji="🔧", style=discord.ButtonStyle.primary, row=3)
    async def channels_btn(self, it, b):
        guild = self._guild()
        if guild is None:
            return await it.response.send_message("❌ Guild ma kaynch!", ephemeral=True)
        await it.response.send_message(
            "🔧 Channel tools:",
            view=ChannelPanel(self.cog, self.user_id, guild),
            ephemeral=True,
        )

    @discord.ui.button(label="Self Roles", emoji="📋", style=discord.ButtonStyle.success, row=3)
    async def selfroles_btn(self, it, b):
        await it.response.send_modal(SelfRolesModal(self.cog, self.guild_id))

    @discord.ui.button(label="Custom Cmds", emoji="🎯", style=discord.ButtonStyle.primary, row=3)
    async def custom_btn(self, it, b):
        await it.response.send_message(
            "🎯 Custom commands (`&cmd`):",
            view=CustomCmdPanel(self.cog, self.user_id, self.guild_id),
            ephemeral=True,
        )

    @discord.ui.button(label="Auto Reply", emoji="💬", style=discord.ButtonStyle.success, row=3)
    async def autoreply_btn(self, it, b):
        await it.response.send_message(
            "💬 **Auto Responses** — kelma → reply\n"
            "Katb kelma f chat → bot yjaweb bo7do (bla `&`)",
            view=AutoReplyPanel(self.cog, self.user_id, self.guild_id),
            ephemeral=True,
        )

    @discord.ui.button(label="Backup", emoji="💾", style=discord.ButtonStyle.primary, row=3)
    async def backup_btn(self, it, b):
        await it.response.send_message(
            "💾 Backup tools:",
            view=BackupPanel(self.cog, self.user_id),
            ephemeral=True,
        )

    # ═══════════════════════════════════════════════════════════
    # ─── ROW 4
    # ═══════════════════════════════════════════════════════════
    @discord.ui.button(label="Shop", emoji="🛒", style=discord.ButtonStyle.success, row=4)
    async def shop_btn(self, it, b):
        await it.response.send_message(
            "🛒 Shop Manager:",
            view=ShopPanel(self.cog, self.user_id),
            ephemeral=True,
        )

    @discord.ui.button(label="Insights", emoji="📊", style=discord.ButtonStyle.secondary, row=4)
    async def insights_btn(self, it, b):
        cog = it.client.get_cog("Insights")
        if cog is None:
            return await it.response.send_message("❌ Insights machi loaded!", ephemeral=True)
        guild = self._guild()
        if guild is None:
            return await it.response.send_message("❌ Guild ma kaynch!", ephemeral=True)
        embed = await cog.build_report(guild)
        await it.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Reload", emoji="🔄", style=discord.ButtonStyle.secondary, row=4)
    async def reload_btn(self, it, b):
        await it.response.send_message("🔄 Reload:", view=ReloadPanel(self.cog, self.user_id), ephemeral=True)

    @discord.ui.button(label="Maint.", emoji="🚨", style=discord.ButtonStyle.danger, row=4)
    async def maint_btn(self, it, b):
        guild = self._guild()
        if guild is None:
            return await it.response.send_message("❌ Guild ma kaynch!", ephemeral=True)
        if it.user.id != guild.owner_id:
            return await it.response.send_message("❌ Ghir owner!", ephemeral=True)
        await it.response.send_message("🚨 Bot ghadi ytsded f 3s...", ephemeral=True)
        _audit(it.user, "maintenance")
        await asyncio.sleep(3)
        await self.cog.bot.close()

    @discord.ui.button(label="Lock", emoji="🔒", style=discord.ButtonStyle.danger, row=4)
    async def lock_btn(self, it, b):
        UNLOCKED.pop(it.user.id, None)
        _audit(it.user, "lock_panel")
        await it.response.send_message("🔒 Panel tsded!", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════
# ─── SHOP PANEL
# ═══════════════════════════════════════════════════════════════════
class ShopPanel(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id

    async def interaction_check(self, it):
        return it.user.id == self.user_id

    @discord.ui.button(label="Add Item", emoji="➕", style=discord.ButtonStyle.success)
    async def add_btn(self, it, b):
        await it.response.send_modal(ShopAddModal(self.cog))

    @discord.ui.button(label="Remove Item", emoji="➖", style=discord.ButtonStyle.danger)
    async def rm_btn(self, it, b):
        await it.response.send_modal(ShopRemoveModal(self.cog))

    @discord.ui.button(label="List Items", emoji="📋", style=discord.ButtonStyle.secondary)
    async def list_btn(self, it, b):
        get_items, _, _ = _shop_api()
        if get_items is None:
            return await it.response.send_message("❌ Shop machi loaded!", ephemeral=True)
        items = get_items()
        if not items:
            return await it.response.send_message("📋 Shop khawi.", ephemeral=True)
        lines = []
        for key, item in items.items():
            income = item.get("income", 0)
            lines.append(
                f"**`{key}`** — {item['name']} `{item['price']:,}` 🪙\n"
                f"  └ Role: `{item.get('role', '—')}` | Income: `{income:,}` / 30min"
            )
        embed = discord.Embed(
            title=f"🛒 Shop Items ({len(items)})",
            description="\n\n".join(lines[:15]) or "—",
            color=discord.Color.gold(),
        )
        await it.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary)
    async def refresh_btn(self, it, b):
        await it.response.send_message("🔄 Refreshed!", ephemeral=True)


class ShopAddModal(discord.ui.Modal, title="➕ Zid item l Shop"):
    key_ = discord.ui.TextInput(
        label="Key (unique, bla espaces)",
        placeholder="vip / premium / color_red",
        max_length=40,
    )
    name_ = discord.ui.TextInput(label="Name (b emoji)", placeholder="💎 VIP", max_length=100)
    price_ = discord.ui.TextInput(label="Price (coins)", placeholder="5000", max_length=12)
    role_ = discord.ui.TextInput(
        label="Role ID wla Smiya",
        placeholder="123456789012345678 wla 'VIP'",
        required=False,
    )
    desc_ = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=300,
    )
    income_ = discord.ui.TextInput(
        label="Income / 30min (0 = bla income)",
        placeholder="50",
        default="0",
        max_length=12,
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, it: discord.Interaction):
        get_items, add_item, _ = _shop_api()
        if add_item is None:
            return await it.response.send_message("❌ Shop machi loaded!", ephemeral=True)

        key = self.key_.value.strip().lower()
        if not key or " " in key:
            return await it.response.send_message("❌ Key khass bla espaces!", ephemeral=True)
        if key in get_items():
            return await it.response.send_message(f"⚠️ Key `{key}` deja kayn!", ephemeral=True)

        try:
            price = int(self.price_.value)
            income = int(self.income_.value or "0")
        except ValueError:
            return await it.response.send_message("❌ Price/Income khass ykoun ra9m!", ephemeral=True)

        if price <= 0 or income < 0:
            return await it.response.send_message("❌ Values ghalta!", ephemeral=True)

        role_name = None
        raw_role = self.role_.value.strip()
        if raw_role:
            guild = it.client.get_guild(it.guild.id) if it.guild else None
            if guild and raw_role.isdigit():
                role = guild.get_role(int(raw_role))
                role_name = role.name if role else raw_role
            else:
                role_name = raw_role

        data = {
            "name": self.name_.value.strip(),
            "price": price,
            "role": role_name,
            "desc": (self.desc_.value or "").strip(),
            "income": income,
        }

        add_item(key, data)
        _audit(it.user, "shop_add", f"{key} → {data['name']} ({price} 🪙, income={income})")

        await it.response.send_message(
            f"✅ Item tzad!\n"
            f"**Key:** `{key}`\n"
            f"**Name:** {data['name']}\n"
            f"**Price:** `{price:,}` 🪙\n"
            f"**Role:** `{role_name or '—'}`\n"
            f"**Income:** `{income:,}` 🪙 / 30min",
            ephemeral=True,
        )


class ShopRemoveModal(discord.ui.Modal, title="➖ Hyed item mn Shop"):
    key_ = discord.ui.TextInput(
        label="Key dyal item",
        placeholder="vip",
        max_length=40,
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, it: discord.Interaction):
        _, _, remove_item = _shop_api()
        if remove_item is None:
            return await it.response.send_message("❌ Shop machi loaded!", ephemeral=True)

        key = self.key_.value.strip().lower()
        ok = remove_item(key)
        _audit(it.user, "shop_remove", key)
        if ok:
            await it.response.send_message(f"✅ Item `{key}` thyed!", ephemeral=True)
        else:
            await it.response.send_message(f"⚠️ Key `{key}` ma kaynch!", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════
# ─── SUB-PANELS
# ═══════════════════════════════════════════════════════════════════
class RolesPanel(discord.ui.View):
    def __init__(self, cog, user_id, guild_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id

    async def interaction_check(self, it):
        return it.user.id == self.user_id

    @discord.ui.button(label="Add", emoji="➕", style=discord.ButtonStyle.success)
    async def add_btn(self, it, b):
        await it.response.send_modal(AddRoleModal(self.cog, self.guild_id))

    @discord.ui.button(label="Remove", emoji="➖", style=discord.ButtonStyle.danger)
    async def rm_btn(self, it, b):
        await it.response.send_modal(RemoveRoleModal(self.cog, self.guild_id))


class PermsPanel(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id

    async def interaction_check(self, it):
        return it.user.id == self.user_id

    @discord.ui.button(label="Grant", emoji="✅", style=discord.ButtonStyle.success)
    async def grant_btn(self, it, b):
        await it.response.send_modal(GrantPermModal(self.cog))

    @discord.ui.button(label="Revoke", emoji="❌", style=discord.ButtonStyle.danger)
    async def revoke_btn(self, it, b):
        await it.response.send_modal(RevokePermModal(self.cog))


class ConfigPanel(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=120)
        self.cog = cog
        self.user_id = user_id

    async def interaction_check(self, it):
        return it.user.id == self.user_id

    @discord.ui.button(label="Set Value", emoji="✏️", style=discord.ButtonStyle.primary)
    async def set_btn(self, it, b):
        await it.response.send_modal(SetConfigModal(self.cog))


class AutoModPanel(discord.ui.View):
    def __init__(self, cog, user_id, guild_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id

    async def interaction_check(self, it):
        return it.user.id == self.user_id

    def _cfg(self):
        get_config, _, _ = _automod_api()
        return get_config(self.guild_id) if get_config else {}

    def _embed(self):
        cfg = self._cfg()
        e = discord.Embed(title="🛡️ AutoMod Config", color=discord.Color.red())
        e.add_field(name="Enabled", value=f"`{cfg.get('enabled')}`", inline=True)
        e.add_field(name="Anti-Spam", value=f"`{cfg.get('anti_spam')}`", inline=True)
        e.add_field(name="Anti-Link", value=f"`{cfg.get('anti_link')}`", inline=True)
        e.add_field(name="Anti-Invite", value=f"`{cfg.get('anti_invite')}`", inline=True)
        e.add_field(name="Anti-CAPS", value=f"`{cfg.get('anti_caps')}`", inline=True)
        e.add_field(name="Bad Words", value=f"`{len(cfg.get('bad_words', []))}`", inline=True)
        e.add_field(name="Timeout", value=f"`{cfg.get('timeout_seconds')}s`", inline=True)
        log = f"<#{cfg.get('log_channel')}>" if cfg.get("log_channel") else "—"
        e.add_field(name="Log Channel", value=log, inline=True)
        return e

    @discord.ui.button(label="Toggle", emoji="🔘", style=discord.ButtonStyle.primary)
    async def toggle_btn(self, it, b):
        await it.response.send_modal(AutoModToggleModal(self.cog, self.guild_id))

    @discord.ui.button(label="Bad Words", emoji="📝", style=discord.ButtonStyle.secondary)
    async def words_btn(self, it, b):
        await it.response.send_modal(AutoModWordsModal(self.cog, self.guild_id))

    @discord.ui.button(label="Log Channel", emoji="📢", style=discord.ButtonStyle.secondary)
    async def log_btn(self, it, b):
        await it.response.send_modal(AutoModLogModal(self.cog, self.guild_id))

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary)
    async def refresh_btn(self, it, b):
        await it.response.edit_message(embed=self._embed(), view=self)


class TicketsPanel(discord.ui.View):
    def __init__(self, cog, user_id, guild_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id

    async def interaction_check(self, it):
        return it.user.id == self.user_id

    def _guild(self):
        return self.cog.bot.get_guild(self.guild_id)

    @discord.ui.button(label="Setup Panel", emoji="🎫", style=discord.ButtonStyle.success)
    async def setup_btn(self, it, b):
        await it.response.send_modal(TicketSetupModal(self.cog, self.guild_id))

    @discord.ui.button(label="List Open", emoji="📋", style=discord.ButtonStyle.secondary)
    async def list_btn(self, it, b):
        try:
            from cogs.tickets import TICKETS
        except Exception:
            return await it.response.send_message("❌ Tickets machi loaded!", ephemeral=True)
        guild = self._guild()
        if guild is None:
            return await it.response.send_message("❌ Guild ma kaynch!", ephemeral=True)
        open_t = TICKETS["open"].get(self.guild_id, {})
        if not open_t:
            return await it.response.send_message("📋 Ma kaynch tickets mfto7in.", ephemeral=True)
        lines = []
        for ch_id, data in open_t.items():
            ch = guild.get_channel(ch_id)
            if ch:
                lines.append(f"{ch.mention} — <@{data['user_id']}>")
        await it.response.send_message("📋 **Open:**\n" + "\n".join(lines), ephemeral=True)


class EmbedChannelPanel(discord.ui.View):
    def __init__(self, cog, user_id, guild):
        super().__init__(timeout=120)
        self.cog = cog
        self.user_id = user_id
        self.guild = guild

    async def interaction_check(self, it):
        return it.user.id == self.user_id

    @discord.ui.button(label="Pick Channel", emoji="📍", style=discord.ButtonStyle.success)
    async def pick_btn(self, it, b):
        await it.response.send_modal(EmbedPickChannelModal(self.cog, self.guild))


class ChannelPanel(discord.ui.View):
    def __init__(self, cog, user_id, guild):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.guild = guild

    async def interaction_check(self, it):
        return it.user.id == self.user_id

    @discord.ui.button(label="Bulk Lock", emoji="🔒", style=discord.ButtonStyle.danger)
    async def lock_btn(self, it, b):
        cog = it.client.get_cog("ChannelManager")
        if not cog:
            return await it.response.send_message("❌ CM machi loaded!", ephemeral=True)
        await it.response.defer(ephemeral=True)
        ok, fail = await cog.bulk_lock(self.guild, True)
        _audit(it.user, "bulk_lock", f"ok={ok} fail={fail}")
        await it.followup.send(f"🔒 Locked: `{ok}` | Failed: `{fail}`", ephemeral=True)

    @discord.ui.button(label="Bulk Unlock", emoji="🔓", style=discord.ButtonStyle.success)
    async def unlock_btn(self, it, b):
        cog = it.client.get_cog("ChannelManager")
        if not cog:
            return await it.response.send_message("❌ CM machi loaded!", ephemeral=True)
        await it.response.defer(ephemeral=True)
        ok, fail = await cog.bulk_lock(self.guild, False)
        _audit(it.user, "bulk_unlock", f"ok={ok} fail={fail}")
        await it.followup.send(f"🔓 Unlocked: `{ok}` | Failed: `{fail}`", ephemeral=True)

    @discord.ui.button(label="Slowmode All", emoji="🐌", style=discord.ButtonStyle.secondary)
    async def slow_btn(self, it, b):
        await it.response.send_modal(SlowmodeModal(self.cog, self.guild))


class CustomCmdPanel(discord.ui.View):
    def __init__(self, cog, user_id, guild_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id

    async def interaction_check(self, it):
        return it.user.id == self.user_id

    @discord.ui.button(label="Add", emoji="➕", style=discord.ButtonStyle.success)
    async def add_btn(self, it, b):
        await it.response.send_modal(CustomCmdAddModal(self.cog, self.guild_id))

    @discord.ui.button(label="Remove", emoji="➖", style=discord.ButtonStyle.danger)
    async def rm_btn(self, it, b):
        await it.response.send_modal(CustomCmdRemoveModal(self.cog, self.guild_id))

    @discord.ui.button(label="List", emoji="📋", style=discord.ButtonStyle.secondary)
    async def list_btn(self, it, b):
        cog = it.client.get_cog("CustomCommands")
        if not cog:
            return await it.response.send_message("❌ CC!", ephemeral=True)
        cmds = cog.list_commands(self.guild_id)
        if not cmds:
            return await it.response.send_message("📋 Khawi.", ephemeral=True)
        lines = [f"`&{name}`" for name in cmds]
        await it.response.send_message("📋 **Custom:**\n" + ", ".join(lines), ephemeral=True)


class BackupPanel(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id

    async def interaction_check(self, it):
        return it.user.id == self.user_id

    @discord.ui.button(label="Create", emoji="💾", style=discord.ButtonStyle.success)
    async def create_btn(self, it, b):
        cog = it.client.get_cog("BackupRestore")
        if not cog:
            return await it.response.send_message("❌ BR!", ephemeral=True)
        folder = cog.make_backup()
        _audit(it.user, "backup_create", folder or "empty")
        await it.response.send_message(f"✅ Backup: `{folder}`" if folder else "❌ Khawi!", ephemeral=True)

    @discord.ui.button(label="List", emoji="📋", style=discord.ButtonStyle.secondary)
    async def list_btn(self, it, b):
        cog = it.client.get_cog("BackupRestore")
        if not cog:
            return await it.response.send_message("❌ BR!", ephemeral=True)
        backups = cog.list_backups()
        if not backups:
            return await it.response.send_message("📋 Khawi.", ephemeral=True)
        await it.response.send_message("📋 **Backups:**\n" + "\n".join(f"`{b}`" for b in backups[:15]), ephemeral=True)

    @discord.ui.button(label="Restore", emoji="♻️", style=discord.ButtonStyle.danger)
    async def restore_btn(self, it, b):
        await it.response.send_modal(RestoreModal(self.cog))


class ReloadPanel(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=120)
        self.cog = cog
        self.user_id = user_id

    async def interaction_check(self, it):
        return it.user.id == self.user_id

    @discord.ui.button(label="Reload All", emoji="🔄", style=discord.ButtonStyle.danger)
    async def all_btn(self, it, b):
        await it.response.defer(ephemeral=True)
        loaded, failed = 0, 0
        for name, path in COG_MAP.items():
            try:
                await self.cog.bot.reload_extension(path)
                loaded += 1
            except Exception:
                failed += 1
        _audit(it.user, "reload_all", f"ok={loaded} fail={failed}")
        await it.followup.send(f"🔄 Reloaded: `{loaded}` | Failed: `{failed}`", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════
# ─── AUTO REPLY PANEL
# ═══════════════════════════════════════════════════════════════════
class AutoReplyPanel(discord.ui.View):
    def __init__(self, cog, user_id, guild_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id

    async def interaction_check(self, it):
        return it.user.id == self.user_id

    @discord.ui.button(label="Add", emoji="➕", style=discord.ButtonStyle.success)
    async def add_btn(self, it, b):
        await it.response.send_modal(AutoReplyAddModal(self.guild_id))

    @discord.ui.button(label="Remove", emoji="➖", style=discord.ButtonStyle.danger)
    async def rm_btn(self, it, b):
        await it.response.send_modal(AutoReplyRemoveModal(self.guild_id))

    @discord.ui.button(label="List", emoji="📋", style=discord.ButtonStyle.secondary)
    async def list_btn(self, it, b):
        cog = it.client.get_cog("AutoResponses")
        if not cog:
            return await it.response.send_message("❌ AutoResponses machi loaded!", ephemeral=True)
        rules = cog.list_all(self.guild_id)
        if not rules:
            return await it.response.send_message("📋 Khawi.", ephemeral=True)
        lines = []
        for trig, d in rules.items():
            kind = "🖼️" if d.get("image") else ("💬" if d.get("embed") else "📝")
            preview = d.get("title") or (d.get("content") or "")[:40]
            lines.append(f"{kind} **`{trig}`** — {preview}")
        embed = discord.Embed(
            title=f"💬 Auto Responses ({len(rules)})",
            description="\n".join(lines[:25]),
            color=discord.Color.blurple(),
        )
        await it.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Clear All", emoji="🗑️", style=discord.ButtonStyle.danger)
    async def clear_btn(self, it, b):
        cog = it.client.get_cog("AutoResponses")
        if not cog:
            return await it.response.send_message("❌ AutoResponses machi loaded!", ephemeral=True)
        n = cog.clear(self.guild_id)
        await it.response.send_message(f"🗑️ Tsaybo `{n}` responses!", ephemeral=True)


class AutoReplyAddModal(discord.ui.Modal, title="➕ Zid Auto Response"):
    trigger = discord.ui.TextInput(
        label="Trigger (kelma, bla espaces)",
        placeholder="badr / salam / exemple",
        max_length=50,
    )
    content = discord.ui.TextInput(
        label="Content / Text (optionnel)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1500,
    )
    title_ = discord.ui.TextInput(
        label="Embed title (optionnel)",
        required=False,
        max_length=200,
    )
    image = discord.ui.TextInput(
        label="Image URL (optionnel)",
        placeholder="https://i.pinimg.com/...jpg",
        required=False,
        max_length=500,
    )
    color = discord.ui.TextInput(
        label="Color hex (optionnel)",
        required=False,
        default="5865F2",
        max_length=7,
    )

    def __init__(self, guild_id):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, it: discord.Interaction):
        cog = it.client.get_cog("AutoResponses")
        if not cog:
            return await it.response.send_message("❌ AutoResponses machi loaded!", ephemeral=True)

        trigger = self.trigger.value.strip().lower()
        if not trigger or " " in trigger:
            return await it.response.send_message("❌ Trigger khass bla espaces!", ephemeral=True)

        content = (self.content.value or "").strip()
        image = (self.image.value or "").strip() or None

        if not image and content and IMAGE_URL_RE.match(content):
            image = content

        if not content and not image and not self.title_.value:
            return await it.response.send_message("❌ 3tini 3la l-a9al content wla image!", ephemeral=True)

        data = {
            "content": content,
            "image": image,
            "title": self.title_.value or None,
            "color": self.color.value or "5865F2",
            "embed": bool(self.title_.value or image),
            "exact": False,
        }
        cog.add(self.guild_id, trigger, data)
        await it.response.send_message(
            f"✅ Trigger **`{trigger}`** tzad!\n"
            f"💡 Jereb: kteb **{trigger}** f chat (bla `&`)",
            ephemeral=True,
        )


class AutoReplyRemoveModal(discord.ui.Modal, title="➖ Hyed Auto Response"):
    trigger = discord.ui.TextInput(label="Trigger", max_length=50)

    def __init__(self, guild_id):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, it: discord.Interaction):
        cog = it.client.get_cog("AutoResponses")
        if not cog:
            return await it.response.send_message("❌ AutoResponses machi loaded!", ephemeral=True)
        ok = cog.remove(self.guild_id, self.trigger.value)
        await it.response.send_message(
            "✅ Thyed!" if ok else "❌ Ma kaynch had trigger!",
            ephemeral=True,
        )


# ═══════════════════════════════════════════════════════════════════
# ─── MODALS
# ═══════════════════════════════════════════════════════════════════
class AddRoleModal(discord.ui.Modal, title="➕ Zid role"):
    role_input = discord.ui.TextInput(
        label="Role ID wla Smiya",
        placeholder="123456789012345678 wla 'Mod'",
        required=True,
    )
    category = discord.ui.TextInput(
        label="Category (admin/moderator/helper)",
        default="moderator",
        max_length=20,
    )

    def __init__(self, cog, guild_id: int):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, it: discord.Interaction):
        cat = self.category.value.lower().strip()
        target = {
            "admin": botconfig.ADMIN_ROLES,
            "moderator": botconfig.MODERATOR_ROLES,
            "helper": botconfig.HELPER_ROLES,
        }.get(cat)
        if target is None:
            return await it.response.send_message("❌ Category ghalta! (admin/moderator/helper)", ephemeral=True)

        guild = it.client.get_guild(self.guild_id)
        if guild is None:
            return await it.response.send_message("❌ Guild ma kaynch!", ephemeral=True)

        raw = self.role_input.value.strip()
        role_id = None
        role_name = None

        if raw.isdigit():
            role = guild.get_role(int(raw))
            if role is None:
                return await it.response.send_message(
                    f"❌ Role b ID `{raw}` ma kaynch f had server!",
                    ephemeral=True,
                )
            role_id = role.id
            role_name = role.name
        else:
            role = discord.utils.get(guild.roles, name=raw)
            if role is None:
                role_name = raw
            else:
                role_id = role.id
                role_name = role.name

        if role_name in target:
            return await it.response.send_message(
                f"⚠️ `{role_name}` deja kayn f **{cat}**!",
                ephemeral=True,
            )

        target.append(role_name)
        if role_id:
            botconfig.ROLE_NAME_TO_ID[role_name] = role_id

        _audit(it.user, "add_role", f"{role_name} ({role_id or 'name'}) → {cat}")

        emoji = {"admin": "👑", "moderator": "🛡️", "helper": "💚"}.get(cat, "🎭")
        await it.response.send_message(
            f"{emoji} **{role_name}** tzad f **{cat}**!\n"
            f"🆔 ID: `{role_id or '— (b smiya)'}`",
            ephemeral=True,
        )


class RemoveRoleModal(discord.ui.Modal, title="➖ Hyed role"):
    role_input = discord.ui.TextInput(
        label="Role ID wla Smiya",
        placeholder="123456789012345678 wla 'Mod'",
    )
    category = discord.ui.TextInput(
        label="Category (admin/moderator/helper)",
        default="moderator",
    )

    def __init__(self, cog, guild_id: int):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, it: discord.Interaction):
        cat = self.category.value.lower().strip()
        target = {
            "admin": botconfig.ADMIN_ROLES,
            "moderator": botconfig.MODERATOR_ROLES,
            "helper": botconfig.HELPER_ROLES,
        }.get(cat)
        if target is None:
            return await it.response.send_message("❌ Category ghalta!", ephemeral=True)

        guild = it.client.get_guild(self.guild_id)
        if guild is None:
            return await it.response.send_message("❌ Guild ma kaynch!", ephemeral=True)

        raw = self.role_input.value.strip()
        role_name = None

        if raw.isdigit():
            role = guild.get_role(int(raw))
            if role is None:
                for name, rid in botconfig.ROLE_NAME_TO_ID.items():
                    if rid == int(raw):
                        role_name = name
                        break
                if role_name is None:
                    return await it.response.send_message(f"❌ Role b ID `{raw}` ma kaynch!", ephemeral=True)
            else:
                role_name = role.name
        else:
            role_name = raw

        if role_name not in target:
            return await it.response.send_message(
                f"⚠️ `{role_name}` ma kaynch f **{cat}**!",
                ephemeral=True,
            )

        target.remove(role_name)
        botconfig.ROLE_NAME_TO_ID.pop(role_name, None)
        _audit(it.user, "remove_role", f"{role_name} ← {cat}")
        await it.response.send_message(
            f"✅ `{role_name}` thyed mn **{cat}**!",
            ephemeral=True,
        )


class GrantPermModal(discord.ui.Modal, title="✅ Grant command"):
    command = discord.ui.TextInput(label="Smiya dyal command")
    role = discord.ui.TextInput(label="Role li bghiti t3ti")

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, it):
        cmd = self.command.value.strip()
        for cat, data in botconfig.COMMAND_PERMISSIONS.items():
            if cmd in data["commands"]:
                if self.role.value not in data["roles"]:
                    data["roles"].append(self.role.value)
                _audit(it.user, "grant", f"{cmd} → {self.role.value}")
                return await it.response.send_message(
                    f"✅ `{cmd}` daba 3endou role `{self.role.value}`!",
                    ephemeral=True,
                )
        botconfig.COMMAND_PERMISSIONS["public"]["commands"].append(cmd)
        _audit(it.user, "grant_public", cmd)
        await it.response.send_message(f"✅ `{cmd}` tzad f public!", ephemeral=True)


class RevokePermModal(discord.ui.Modal, title="❌ Revoke command"):
    command = discord.ui.TextInput(label="Smiya dyal command")
    role = discord.ui.TextInput(label="Role li bghiti thyed")

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, it):
        cmd = self.command.value.strip()
        for cat, data in botconfig.COMMAND_PERMISSIONS.items():
            if cmd in data["commands"]:
                if self.role.value in data["roles"]:
                    data["roles"].remove(self.role.value)
                    _audit(it.user, "revoke", f"{cmd} ← {self.role.value}")
                    return await it.response.send_message("✅ Thyed!", ephemeral=True)
        await it.response.send_message("⚠️ Ma l9itch!", ephemeral=True)


class SetConfigModal(discord.ui.Modal, title="✏️ Beddel config"):
    key = discord.ui.TextInput(label="Config key (ex: WELCOME_CHANNEL_NAME)")
    value = discord.ui.TextInput(label="Value jdida")

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, it):
        key = self.key.value.strip().upper()
        if not hasattr(botconfig, key):
            return await it.response.send_message(f"❌ `{key}` ma kaynch!", ephemeral=True)
        old = getattr(botconfig, key)
        raw = self.value.value
        try:
            if isinstance(old, bool):
                new = raw.lower() in ("1", "true", "yes", "on")
            elif isinstance(old, int):
                new = int(raw)
            elif isinstance(old, list):
                new = [x.strip() for x in raw.split(",") if x.strip()]
            elif old is None:
                new = None if raw.lower() == "none" else raw
            else:
                new = raw
        except Exception:
            new = raw
        setattr(botconfig, key, new)
        _audit(it.user, "set_config", f"{key}: {old} → {new}")
        await it.response.send_message(f"✅ `{key}` = `{new}`", ephemeral=True)


class AutoModToggleModal(discord.ui.Modal, title="🛡️ Toggle AutoMod"):
    feature = discord.ui.TextInput(label="Feature (enabled/spam/link/invite/caps)")
    value = discord.ui.TextInput(label="Value (on/off)")

    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, it):
        get_config, save_am, AUTOMOD = _automod_api()
        if get_config is None:
            return await it.response.send_message("❌ AutoMod!", ephemeral=True)
        cfg = get_config(self.guild_id)
        key_map = {
            "enabled": "enabled", "spam": "anti_spam", "link": "anti_link",
            "invite": "anti_invite", "caps": "anti_caps",
        }
        k = key_map.get(self.feature.value.strip().lower())
        if not k:
            return await it.response.send_message("❌ Feature ghalta!", ephemeral=True)
        cfg[k] = self.value.value.strip().lower() in ("on", "true", "1", "yes")
        save_am(AUTOMOD)
        _audit(it.user, "automod_toggle", f"{k}={cfg[k]}")
        await it.response.send_message(f"✅ `{k}` = `{cfg[k]}`", ephemeral=True)


class AutoModWordsModal(discord.ui.Modal, title="📝 Bad Words"):
    action = discord.ui.TextInput(label="Action (add/remove/set)", default="add")
    words = discord.ui.TextInput(label="Words (comma-separated)", required=False)

    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, it):
        get_config, save_am, AUTOMOD = _automod_api()
        if get_config is None:
            return await it.response.send_message("❌ AutoMod!", ephemeral=True)
        cfg = get_config(self.guild_id)
        action = self.action.value.strip().lower()
        words = [w.strip() for w in self.words.value.split(",") if w.strip()]
        if action == "add":
            for w in words:
                if w not in cfg["bad_words"]:
                    cfg["bad_words"].append(w)
        elif action == "remove":
            cfg["bad_words"] = [w for w in cfg["bad_words"] if w not in words]
        elif action == "set":
            cfg["bad_words"] = words
        save_am(AUTOMOD)
        _audit(it.user, "automod_words", f"{action}: {len(cfg['bad_words'])} words")
        await it.response.send_message(f"✅ `{action}` → {len(cfg['bad_words'])} words", ephemeral=True)


class AutoModLogModal(discord.ui.Modal, title="📢 Log Channel"):
    channel_id = discord.ui.TextInput(label="Channel ID (khawi = disable)", required=False)

    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, it):
        get_config, save_am, AUTOMOD = _automod_api()
        if get_config is None:
            return await it.response.send_message("❌ AutoMod!", ephemeral=True)
        cfg = get_config(self.guild_id)
        v = self.channel_id.value.strip()
        cfg["log_channel"] = int(v) if v else None
        save_am(AUTOMOD)
        await it.response.send_message(f"✅ Log = `{cfg['log_channel']}`", ephemeral=True)


class TicketSetupModal(discord.ui.Modal, title="🎫 Ticket Setup"):
    category_id = discord.ui.TextInput(label="Category ID")
    support_role_id = discord.ui.TextInput(label="Support Role ID")
    log_channel_id = discord.ui.TextInput(label="Log Channel ID")
    panel_channel_id = discord.ui.TextInput(label="Panel Channel ID")

    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, it):
        cog = it.client.get_cog("Tickets")
        if not cog:
            return await it.response.send_message("❌ Tickets machi loaded!", ephemeral=True)
        guild = it.client.get_guild(self.guild_id)
        if guild is None:
            return await it.response.send_message("❌ Guild ma kaynch!", ephemeral=True)
        cfg = cog._gcfg(self.guild_id)
        try:
            cfg["category_id"] = int(self.category_id.value)
            cfg["support_role_id"] = int(self.support_role_id.value)
            cfg["log_channel_id"] = int(self.log_channel_id.value)
        except ValueError:
            return await it.response.send_message("❌ ID ghalat!", ephemeral=True)
        from cogs.tickets import _save
        _save()
        ch = guild.get_channel(int(self.panel_channel_id.value))
        if not ch:
            return await it.response.send_message("❌ Panel channel ma kaynch!", ephemeral=True)
        ok = await cog.setup_panel(guild, ch)
        await it.response.send_message("✅ Setup!" if ok else "❌ Erreur!", ephemeral=True)


class TempBanModal(discord.ui.Modal, title="⏱️ Temp Ban"):
    user_id = discord.ui.TextInput(label="User ID")
    duration = discord.ui.TextInput(label="Duration (ex: 1h30m, 2d, 1w)")
    reason = discord.ui.TextInput(label="Reason", required=False, default="Panel")

    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, it):
        from cogs.tempban import parse_duration
        cog = it.client.get_cog("TempBan")
        if not cog:
            return await it.response.send_message("❌ TempBan machi loaded!", ephemeral=True)
        guild = it.client.get_guild(self.guild_id)
        if guild is None:
            return await it.response.send_message("❌ Guild ma kaynch!", ephemeral=True)
        try:
            uid = int(self.user_id.value)
        except ValueError:
            return await it.response.send_message("❌ ID ghalat!", ephemeral=True)
        secs = parse_duration(self.duration.value)
        if secs <= 0:
            return await it.response.send_message("❌ Duration ghalta! (1h30m, 2d, 1w)", ephemeral=True)
        try:
            user = await it.client.fetch_user(uid)
        except Exception:
            return await it.response.send_message("❌ User ma kaynch!", ephemeral=True)
        until, err = await cog.tempban(guild, user, secs, self.reason.value, it.user)
        if err:
            return await it.response.send_message(f"❌ `{err}`", ephemeral=True)
        _audit(it.user, "tempban", f"{user} {secs}s")
        await it.response.send_message(
            f"✅ TempBan <@{uid}> l {secs}s (until <t:{int(until.timestamp())}:R>)",
            ephemeral=True,
        )


class GiveawayModal(discord.ui.Modal, title="🎁 Giveaway"):
    channel_id = discord.ui.TextInput(label="Channel ID")
    prize = discord.ui.TextInput(label="Prize")
    duration = discord.ui.TextInput(label="Duration (ex: 1h, 30m, 1d)", default="1h")
    winners = discord.ui.TextInput(label="Winners count", default="1")

    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, it):
        from cogs.tempban import parse_duration
        cog = it.client.get_cog("Giveaway")
        if not cog:
            return await it.response.send_message("❌ Giveaway machi loaded!", ephemeral=True)
        guild = it.client.get_guild(self.guild_id)
        if guild is None:
            return await it.response.send_message("❌ Guild ma kaynch!", ephemeral=True)
        try:
            ch = guild.get_channel(int(self.channel_id.value))
            secs = parse_duration(self.duration.value)
            wins = int(self.winners.value)
        except Exception:
            return await it.response.send_message("❌ Input ghalat!", ephemeral=True)
        if not ch or secs <= 0 or wins < 1:
            return await it.response.send_message("❌ Values ghalta!", ephemeral=True)
        await cog.start_giveaway(ch, self.prize.value, secs, wins, it.user)
        _audit(it.user, "giveaway", f"{self.prize.value} f {ch.name}")
        await it.response.send_message(f"✅ Giveaway bda f {ch.mention}", ephemeral=True)


class ReactRolesModal(discord.ui.Modal, title="📌 Reaction Roles"):
    channel_id = discord.ui.TextInput(label="Channel ID")
    panel_title = discord.ui.TextInput(
        label="Title",
        default="Choisis tes rôles",
        max_length=200,
    )
    panel_description = discord.ui.TextInput(
        label="Description",
        default="Click 3la button bash takhod role",
        max_length=1000,
    )
    mappings = discord.ui.TextInput(
        label="Mappings",
        placeholder="role_id:label:emoji (kol line)",
        style=discord.TextStyle.paragraph,
        default="1550538976635527288:Casino Player:🎰",
    )

    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, it):
        await it.response.defer(ephemeral=True, thinking=True)

        cog = it.client.get_cog("ReactionRoles")
        if not cog:
            return await it.followup.send("❌ RR machi loaded!", ephemeral=True)
        guild = it.client.get_guild(self.guild_id)
        if guild is None:
            return await it.followup.send("❌ Guild ma kaynch!", ephemeral=True)
        try:
            ch = guild.get_channel(int(self.channel_id.value))
        except ValueError:
            return await it.followup.send("❌ Channel ID ghalat!", ephemeral=True)
        if not ch:
            return await it.followup.send("❌ Channel ma kaynch!", ephemeral=True)

        mappings = []
        for line in self.mappings.value.splitlines():
            parts = line.split(":")
            if len(parts) < 2:
                continue
            try:
                rid = int(parts[0])
                label = parts[1]
                emoji = parts[2] if len(parts) > 2 else None
                mappings.append({"role_id": rid, "label": label, "emoji": emoji})
            except ValueError:
                continue
        if not mappings:
            return await it.followup.send("❌ Mappings ghalta!", ephemeral=True)

        ok = await cog.create_panel(
            ch,
            self.panel_title.value,
            self.panel_description.value,
            mappings,
            it.user,
        )
        _audit(it.user, "reaction_roles", f"{len(mappings)} mappings")
        await it.followup.send("✅ Panel tsayeb!" if ok else "❌ Erreur!", ephemeral=True)


class SlowmodeModal(discord.ui.Modal, title="🐌 Slowmode All"):
    seconds = discord.ui.TextInput(label="Seconds (0-21600)")

    def __init__(self, cog, guild):
        super().__init__()
        self.cog = cog
        self.guild = guild

    async def on_submit(self, it):
        cog = it.client.get_cog("ChannelManager")
        if not cog:
            return await it.response.send_message("❌ CM!", ephemeral=True)
        try:
            s = int(self.seconds.value)
        except ValueError:
            return await it.response.send_message("❌ Ra9m ghalat!", ephemeral=True)
        await it.response.defer(ephemeral=True)
        ok, fail = await cog.bulk_slowmode(self.guild, s)
        _audit(it.user, "bulk_slowmode", f"{s}s ok={ok}")
        await it.followup.send(f"🐌 Applied to `{ok}` | Failed: `{fail}`", ephemeral=True)


class EmbedPickChannelModal(discord.ui.Modal, title="🎨 Embed Builder"):
    channel_id = discord.ui.TextInput(label="Channel ID")

    def __init__(self, cog, guild):
        super().__init__()
        self.cog = cog
        self.guild = guild

    async def on_submit(self, it):
        cog = it.client.get_cog("EmbedBuilder")
        if not cog:
            return await it.response.send_message("❌ EmbedBuilder machi loaded!", ephemeral=True)
        try:
            ch = self.guild.get_channel(int(self.channel_id.value))
        except ValueError:
            return await it.response.send_message("❌ Channel ID ghalat!", ephemeral=True)
        if not ch:
            return await it.response.send_message("❌ Channel ma kaynch!", ephemeral=True)
        await it.response.defer(ephemeral=True)
        ok = await cog.open_builder(ch, it.user)
        if ok:
            await it.followup.send("✅ Check DM!", ephemeral=True)
        else:
            await it.followup.send("❌ Ma qdertch nsift DM!", ephemeral=True)


class CustomCmdAddModal(discord.ui.Modal, title="➕ Custom Command"):
    name = discord.ui.TextInput(label="Command name (bla &)")
    content = discord.ui.TextInput(
        label="Content / Text",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=2000,
    )
    title_ = discord.ui.TextInput(label="Embed title (optionnel)", required=False)
    color = discord.ui.TextInput(label="Color hex (optionnel)", required=False, default="5865F2")
    image = discord.ui.TextInput(
        label="Image URL (optionnel)",
        placeholder="https://i.pinimg.com/...jpg",
        required=False,
        max_length=500,
    )

    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, it):
        cog = it.client.get_cog("CustomCommands")
        if not cog:
            return await it.response.send_message("❌ CC!", ephemeral=True)

        content = (self.content.value or "").strip()
        image_url = (self.image.value or "").strip() or None

        if not image_url and content and IMAGE_URL_RE.match(content):
            image_url = content

        data = {
            "content": content,
            "title": self.title_.value or None,
            "color": self.color.value or "5865F2",
            "embed": bool(self.title_.value or image_url),
            "image": image_url,
        }
        cog.add_command(self.guild_id, self.name.value.strip().lower(), data)
        _audit(it.user, "custom_cmd_add", f"{self.name.value} (img={'yes' if image_url else 'no'})")
        await it.response.send_message(
            f"✅ `&{self.name.value}` tzad!"
            + (f"\n🖼️ Image: `{image_url[:50]}...`" if image_url else ""),
            ephemeral=True,
        )


class CustomCmdRemoveModal(discord.ui.Modal, title="➖ Remove Custom"):
    name = discord.ui.TextInput(label="Command name")

    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, it):
        cog = it.client.get_cog("CustomCommands")
        if not cog:
            return await it.response.send_message("❌ CC!", ephemeral=True)
        ok = cog.remove_command(self.guild_id, self.name.value.strip().lower())
        await it.response.send_message("✅ Thyed!" if ok else "❌ Ma kaynch!", ephemeral=True)


class RestoreModal(discord.ui.Modal, title="♻️ Restore"):
    name = discord.ui.TextInput(label="Backup name (YYYYMMDD-HHMMSS)")

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, it):
        cog = it.client.get_cog("BackupRestore")
        if not cog:
            return await it.response.send_message("❌ BR!", ephemeral=True)
        ok, fail = cog.restore(self.name.value.strip())
        _audit(it.user, "restore", f"{self.name.value} ok={ok}")
        await it.response.send_message(
            f"♻️ Restored: `{ok}` | Failed: `{fail}`\n⚠️ Restart bot bash tloadi data.",
            ephemeral=True,
        )


class SelfRolesModal(discord.ui.Modal, title="📋 Self Roles Panel"):
    channel_id = discord.ui.TextInput(
        label="Channel ID",
        placeholder="123456789012345678",
    )
    panel_title = discord.ui.TextInput(
        label="Title",
        default="🎭 Choose Your Roles",
        max_length=200,
    )
    panel_description = discord.ui.TextInput(
        label="Description",
        default="Click a category to select your roles",
        style=discord.TextStyle.paragraph,
        max_length=500,
    )
    banner_url = discord.ui.TextInput(
        label="Banner URL (khawi = bla image)",
        required=False,
        max_length=500,
    )
    categories = discord.ui.TextInput(
        label="Categories",
        placeholder="Games roles | 123:Valorant:🎮, 456:Minecraft:⛏️",
        style=discord.TextStyle.paragraph,
        max_length=2000,
    )

    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, it: discord.Interaction):
        await it.response.defer(ephemeral=True, thinking=True)

        cog = it.client.get_cog("SelfRoles")
        if not cog:
            return await it.followup.send("❌ SelfRoles cog machi loaded!", ephemeral=True)
        guild = it.client.get_guild(self.guild_id)
        if guild is None:
            return await it.followup.send("❌ Guild ma kaynch!", ephemeral=True)

        try:
            ch = guild.get_channel(int(self.channel_id.value.strip()))
        except ValueError:
            return await it.followup.send("❌ Channel ID ghalat!", ephemeral=True)
        if not ch:
            return await it.followup.send("❌ Channel ma kaynch!", ephemeral=True)

        parsed_cats = []
        for line in self.categories.value.splitlines():
            line = line.strip()
            if not line or "|" not in line:
                continue
            parts = line.split("|", 1)
            cat_name = parts[0].strip()
            options = []
            for opt in parts[1].split(","):
                opt = opt.strip()
                if not opt:
                    continue
                sub = opt.split(":")
                if len(sub) < 2:
                    continue
                try:
                    rid = int(sub[0])
                    label = sub[1]
                    emoji = sub[2] if len(sub) > 2 else None
                    options.append({"role_id": rid, "label": label, "emoji": emoji})
                except ValueError:
                    continue
            if options:
                parsed_cats.append({"name": cat_name, "options": options})

        if not parsed_cats:
            return await it.followup.send(
                "❌ Format ghalat!\n"
                "**Exemple:**\n"
                "`Games roles | 123:Valorant:🎮, 456:Minecraft:⛏️`",
                ephemeral=True,
            )

        ok = await cog.create_panel(
            ch,
            self.panel_title.value,
            self.panel_description.value,
            self.banner_url.value or None,
            parsed_cats,
            it.user,
        )
        _audit(it.user, "selfroles", f"{len(parsed_cats)} cats → #{ch.name}")
        await it.followup.send(
            f"✅ **{len(parsed_cats)}** categories tsaybo!" if ok else "❌ Erreur!",
            ephemeral=True,
        )


class AnnounceModal(discord.ui.Modal, title="📢 Sift Announcement"):
    type_ = discord.ui.TextInput(
        label="Type (event/meeting/news)",
        placeholder="event, meeting, wla news",
        default="event",
        max_length=10,
    )
    title_ = discord.ui.TextInput(
        label="Title",
        placeholder="Ex: GUESS THE ENDING",
        max_length=200,
    )
    message = discord.ui.TextInput(
        label="Message / Concept / Agenda",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1500,
    )
    time_or_date = discord.ui.TextInput(
        label="Time/Date",
        placeholder="TODAY, 22:00  wla  2025-01-15 21:00",
        required=False,
        max_length=100,
    )
    extra1 = discord.ui.TextInput(
        label="Prize / Location / Category",
        required=False,
        max_length=200,
    )

    def __init__(self, cog, guild_id: int):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, it: discord.Interaction):
        await it.response.defer(ephemeral=True, thinking=True)

        try:
            from cogs.announcements import (
                build_event_embed,
                build_meeting_embed,
                build_news_embed,
                resolve_ping,
            )
        except Exception as e:
            return await it.followup.send(
                f"❌ Announcements cog machi loaded! `{e}`",
                ephemeral=True,
            )

        guild = it.client.get_guild(self.guild_id)
        if guild is None:
            return await it.followup.send("❌ Guild ma kaynch!", ephemeral=True)

        channel = it.channel

        t = self.type_.value.strip().lower()
        title = self.title_.value
        msg = self.message.value or None
        td = self.time_or_date.value or None
        e1 = self.extra1.value or None
        ping_type = "none"

        if t == "event":
            embed = build_event_embed(
                title,
                event_time=td,
                event_prize=e1,
                concept=msg,
                host=None,
                author=it.user,
                ping_type=ping_type,
            )
        elif t == "meeting":
            m_date, m_time = None, None
            if td:
                parts = td.split(" ", 1)
                m_date = parts[0]
                if len(parts) > 1:
                    m_time = parts[1]
            embed = build_meeting_embed(
                title,
                meeting_date=m_date,
                meeting_time=m_time,
                location=e1,
                agenda=msg,
                host=None,
                author=it.user,
                ping_type=ping_type,
            )
        elif t == "news":
            embed = build_news_embed(
                title,
                message=msg or "...",
                category=e1,
                link=None,
                author=it.user,
                ping_type=ping_type,
            )
        else:
            return await it.followup.send(
                "❌ Type khass ykoun: `event`, `meeting`, wla `news`",
                ephemeral=True,
            )

        content = resolve_ping(ping_type, guild) if ping_type else ""

        try:
            await channel.send(content=content or None, embed=embed)
        except discord.Forbidden:
            return await it.followup.send(
                "❌ Ma 3ndich permission f had channel!",
                ephemeral=True,
            )

        _audit(it.user, f"announce_{t}", f"{title} → #{channel.name} (ping={ping_type})")
        await it.followup.send(
            f"✅ Sift f {channel.mention}! (ping: `{ping_type or 'none'}`)",
            ephemeral=True,
        )


# ═══════════════════════════════════════════════════════════════════
# ─── COG MAIN
# ═══════════════════════════════════════════════════════════════════
class SecretAdmin(commands.Cog):
    """Secret Admin Panel v3.5 — + Shop + Command Manager + Auto Reply"""

    def __init__(self, bot):
        self.bot = bot

    def _config_embed(self) -> discord.Embed:
        embed = discord.Embed(title="⚙️ Bot Config", color=discord.Color.blue())
        for attr in sorted(dir(botconfig)):
            if attr.isupper() and not attr.startswith("_"):
                try:
                    val = getattr(botconfig, attr)
                    if isinstance(val, (str, int, bool, list)) or val is None:
                        sval = str(val)
                        if len(sval) > 80:
                            sval = sval[:77] + "..."
                        embed.add_field(name=attr, value=f"`{sval}`", inline=True)
                except Exception:
                    pass
        return embed

    def _automod_embed(self, guild_id: int) -> discord.Embed:
        get_config, _, _ = _automod_api()
        if get_config is None:
            return discord.Embed(title="🛡️ AutoMod", description="❌ Machi loaded!", color=discord.Color.red())
        cfg = get_config(guild_id)
        e = discord.Embed(title="🛡️ AutoMod Config", color=discord.Color.red())
        e.add_field(name="Enabled", value=f"`{cfg.get('enabled')}`", inline=True)
        e.add_field(name="Anti-Spam", value=f"`{cfg.get('anti_spam')}`", inline=True)
        e.add_field(name="Anti-Link", value=f"`{cfg.get('anti_link')}`", inline=True)
        e.add_field(name="Anti-Invite", value=f"`{cfg.get('anti_invite')}`", inline=True)
        e.add_field(name="Anti-CAPS", value=f"`{cfg.get('anti_caps')}`", inline=True)
        e.add_field(name="Bad Words", value=f"`{len(cfg.get('bad_words', []))}`", inline=True)
        e.add_field(name="Timeout", value=f"`{cfg.get('timeout_seconds')}s`", inline=True)
        log = f"<#{cfg.get('log_channel')}>" if cfg.get("log_channel") else "—"
        e.add_field(name="Log Channel", value=log, inline=True)
        return e

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.content.strip() != SECRET_TRIGGER:
            return

        if message.guild is not None:
            try:
                await message.delete()
            except discord.Forbidden:
                pass

            if not _is_real_admin(message.author):
                try:
                    await message.author.send("❌ Ma 3ndkch permission l had l-panel.")
                except discord.Forbidden:
                    pass
                return
        else:
            found_admin = False
            for guild in self.bot.guilds:
                member = guild.get_member(message.author.id)
                if member and _is_real_admin(member):
                    found_admin = True
                    break

            if not found_admin:
                try:
                    await message.author.send("❌ Ma 3ndkch permission f ay server!")
                except discord.Forbidden:
                    pass
                return

        if _is_unlocked(message.author.id):
            if message.guild:
                guild_id = message.guild.id
            else:
                guild_id = None
                for guild in self.bot.guilds:
                    member = guild.get_member(message.author.id)
                    if member and _is_real_admin(member):
                        guild_id = guild.id
                        break

            if guild_id is None:
                return await message.author.send("❌ Ma l9itch guild!")

            embed = self._panel_embed(message.author)
            view = SecretPanel(self, message.author.id, guild_id)
            try:
                await message.author.send(embed=embed, view=view)
            except discord.Forbidden:
                pass
            return

        try:
            await message.author.send(
                "🔒 **Panel Admin v3.5**\n"
                "Sift liya l-**modpass** f had DM. 3ndek **60s**."
            )
        except discord.Forbidden:
            return

        def check(m):
            return m.author.id == message.author.id and isinstance(m.channel, discord.DMChannel)

        try:
            reply = await self.bot.wait_for("message", timeout=60.0, check=check)
        except Exception:
            try:
                await message.author.send("⏰ Wqef l-wa9t. 3awed kteb l-kelma f server wla DM.")
            except Exception:
                pass
            return

        if reply.content.strip() != MODPASS:
            _audit(message.author, "failed_modpass")
            try:
                await message.author.send("❌ Modpass ghalat!")
            except Exception:
                pass
            return

        UNLOCKED[message.author.id] = datetime.now().timestamp()
        _audit(message.author, "unlock_panel")

        try:
            await reply.delete()
        except Exception:
            pass

        if message.guild:
            guild_id = message.guild.id
        else:
            guild_id = None
            for guild in self.bot.guilds:
                member = guild.get_member(message.author.id)
                if member and _is_real_admin(member):
                    guild_id = guild.id
                    break

        if guild_id is None:
            return await message.author.send("❌ Ma l9itch guild!")

        embed = self._panel_embed(message.author)
        view = SecretPanel(self, message.author.id, guild_id)
        try:
            await message.author.send(embed=embed, view=view)
        except Exception:
            pass

    def _panel_embed(self, user: discord.Member) -> discord.Embed:
        embed = discord.Embed(
            title="🎛️ Secret Admin Panel v3.5",
            description=(
                f"### Marhba {user.mention}\n"
                "Kolchi **makaybanch** f `&help`.\n\n"
                "🎭 **Roles** — Add b ID wla Smiya\n"
                "🔑 **Perms** — Commands → Roles\n"
                "⚙️ **Config** — Beddel config\n"
                "📜 **Audit** — Kolchi mssjel\n"
                "🛡️ **AutoMod** — Anti-spam/link\n"
                "🎫 **Tickets** — Support system\n"
                "⏱️ **TempBan** — Ban b wa9t\n"
                "🎁 **Giveaway** — Giveaways\n"
                "🎨 **Embed** — Embed builder\n"
                "📌 **React Roles** — RR panel\n"
                "📢 **Announce** — Event / Meeting / News\n"
                "📋 **Self Roles** — Dropdowns multi-cat\n"
                "🔧 **Channels** — Bulk tools\n"
                "🎯 **Custom Cmds** — Custom cmds (`&cmd`)\n"
                "💬 **Auto Reply** — Kelma → reply (bla `&`) [NEW]\n"
                "💾 **Backup** — Save/Restore\n"
                "🛒 **Shop** — Add/Remove items\n"
                "✏️ **Commands** — Rename / Alias commands\n"
                "📊 **Insights** — Stats\n"
                "🔄 **Reload** — Reload cogs\n"
                "🚨 **Maint.** — Tfe3 bot\n"
                "🔒 **Lock** — Sded panel"
            ),
            color=discord.Color.dark_red(),
            timestamp=datetime.now(),
        )
        embed.set_footer(text="Session: 1h • DM only • v3.5")
        return embed


async def setup(bot):
    await bot.add_cog(SecretAdmin(bot))