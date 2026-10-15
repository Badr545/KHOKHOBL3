# cogs/tickets.py
# =====================================================================
# ─── TICKET SYSTEM — Panel + Create/Close/Claim
# =====================================================================
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

DATA_FILE = "data/tickets.json"


def _load():
    if not os.path.exists(DATA_FILE):
        return {"guilds": {}, "open": {}, "counter": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        raw["guilds"] = {int(g): v for g, v in raw.get("guilds", {}).items()}
        raw["open"] = {int(g): v for g, v in raw.get("open", {}).items()}
        raw["counter"] = {int(g): v for g, v in raw.get("counter", {}).items()}
        return raw
    except Exception:
        return {"guilds": {}, "open": {}, "counter": {}}


TICKETS = _load()


def _save():
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(TICKETS, f, indent=2, ensure_ascii=False)


class TicketView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Create Ticket", emoji="🎫", style=discord.ButtonStyle.success, custom_id="ticket:create")
    async def create_btn(self, it: discord.Interaction, b: discord.ui.Button):
        await self.cog._create_ticket(it)


class TicketControl(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Close", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="ticket:close")
    async def close_btn(self, it: discord.Interaction, b: discord.ui.Button):
        await self.cog._close_ticket(it)

    @discord.ui.button(label="Claim", emoji="✋", style=discord.ButtonStyle.primary, custom_id="ticket:claim")
    async def claim_btn(self, it: discord.Interaction, b: discord.ui.Button):
        await self.cog._claim_ticket(it)


class Tickets(commands.Cog):
    """Ticket system"""

    def __init__(self, bot):
        self.bot = bot

    def _gcfg(self, guild_id: int) -> dict:
        return TICKETS["guilds"].setdefault(guild_id, {
            "category_id": None,
            "support_role_id": None,
            "log_channel_id": None,
            "panel_channel_id": None,
            "panel_message_id": None,
        })

    async def setup_panel(self, guild: discord.Guild, channel: discord.TextChannel) -> bool:
        cfg = self._gcfg(guild.id)
        embed = discord.Embed(
            title="🎫 Support Tickets",
            description="Click 3la **Create Ticket** bash tfta7 ticket m3a l-staff.",
            color=discord.Color.blurple(),
        )
        try:
            msg = await channel.send(embed=embed, view=TicketView(self))
        except Exception:
            return False
        cfg["panel_channel_id"] = channel.id
        cfg["panel_message_id"] = msg.id
        _save()
        return True

    async def _create_ticket(self, it: discord.Interaction):
        cfg = self._gcfg(it.guild.id)

        # Check deja 3endou ticket
        for ch_id, data in TICKETS["open"].get(it.guild.id, {}).items():
            if data["user_id"] == it.user.id:
                ch = it.guild.get_channel(ch_id)
                if ch:
                    return await it.response.send_message(f"⚠️ Deja 3endek ticket: {ch.mention}", ephemeral=True)

        if not cfg["category_id"]:
            return await it.response.send_message("❌ Ticket system machi configuré!", ephemeral=True)

        category = it.guild.get_channel(cfg["category_id"])
        if category is None:
            return await it.response.send_message("❌ Category ma kaynch!", ephemeral=True)

        counter = TICKETS["counter"].get(it.guild.id, 0) + 1
        TICKETS["counter"][it.guild.id] = counter

        overwrites = {
            it.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            it.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            it.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        if cfg["support_role_id"]:
            role = it.guild.get_role(cfg["support_role_id"])
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        try:
            ch = await it.guild.create_text_channel(
                name=f"ticket-{counter:04d}",
                category=category,
                overwrites=overwrites,
                reason=f"Ticket par {it.user}",
            )
        except Exception as e:
            return await it.response.send_message(f"❌ `{e}`", ephemeral=True)

        TICKETS["open"].setdefault(it.guild.id, {})[ch.id] = {
            "user_id": it.user.id,
            "created_at": datetime.now().isoformat(),
            "claimed_by": None,
            "number": counter,
        }
        _save()

        embed = discord.Embed(
            title=f"🎫 Ticket #{counter:04d}",
            description=f"Marhba {it.user.mention}!\nStaff ghadi yjawebek 9rib.",
            color=discord.Color.green(),
        )
        embed.set_footer(text="St3mel les boutons bash tqfel wla tclaimi")
        try:
            await ch.send(content=f"{it.user.mention}", embed=embed, view=TicketControl(self))
        except Exception:
            pass

        await it.response.send_message(f"✅ Ticket tsayeb: {ch.mention}", ephemeral=True)

    async def _close_ticket(self, it: discord.Interaction):
        data = TICKETS["open"].get(it.guild.id, {}).get(it.channel.id)
        if not data:
            return await it.response.send_message("❌ Machi ticket channel!", ephemeral=True)

        # Log
        log_id = self._gcfg(it.guild.id).get("log_channel_id")
        if log_id:
            log = it.guild.get_channel(log_id)
            if log:
                embed = discord.Embed(
                    title="🎫 Ticket Closed",
                    description=f"Channel: `{it.channel.name}`\nClosed by: {it.user.mention}",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow(),
                )
                try:
                    await log.send(embed=embed)
                except Exception:
                    pass

        TICKETS["open"][it.guild.id].pop(it.channel.id, None)
        _save()

        await it.response.send_message("🔒 Ticket ghadi ytsded f 5s...", ephemeral=True)
        import asyncio
        await asyncio.sleep(5)
        try:
            await it.channel.delete(reason="Ticket closed")
        except Exception:
            pass

    async def _claim_ticket(self, it: discord.Interaction):
        data = TICKETS["open"].get(it.guild.id, {}).get(it.channel.id)
        if not data:
            return await it.response.send_message("❌ Machi ticket!", ephemeral=True)
        if data["claimed_by"]:
            return await it.response.send_message(f"⚠️ Deja claimed by <@{data['claimed_by']}>!", ephemeral=True)
        data["claimed_by"] = it.user.id
        _save()
        await it.response.send_message(f"✋ {it.user.mention} claima had ticket!")

    # ─── Slash commands
    @app_commands.command(name="ticket_setup", description="Setup ticket panel")
    @app_commands.describe(
        category="Category li fiha ghadi ytsayeb tickets",
        support_role="Role dyal support",
        log_channel="Channel dyal logs",
        panel_channel="Channel li fih panel",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_setup(self, it: discord.Interaction, category: discord.CategoryChannel,
                           support_role: discord.Role, log_channel: discord.TextChannel,
                           panel_channel: discord.TextChannel):
        cfg = self._gcfg(it.guild.id)
        cfg["category_id"] = category.id
        cfg["support_role_id"] = support_role.id
        cfg["log_channel_id"] = log_channel.id
        _save()
        ok = await self.setup_panel(it.guild, panel_channel)
        if ok:
            await it.response.send_message(f"✅ Panel setup f {panel_channel.mention}", ephemeral=True)
        else:
            await it.response.send_message("❌ Erreur panel!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Tickets(bot))