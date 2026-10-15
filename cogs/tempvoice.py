# cogs/tempvoice.py
# =====================================================================
# ─── TEMP VOICE SYSTEM — Panel + Commands (&vc <action>)
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import asyncio
import json
import os

# 💾 Persistence — bach VC ma ythalfouch mli restarta l-bot
TV_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "tempvoice.json")

def _load_tv():
    global TEMP_VOICE
    TEMP_VOICE = {}
    try:
        with open(TV_DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return
    for k, v in raw.items():
        try:
            TEMP_VOICE[int(k)] = {
                "owner_id": v["owner_id"],
                "guild_id": v["guild_id"],
                "panel_message_id": v.get("panel_message_id"),
                "blacklist": set(v.get("blacklist", [])),
                "permitted": set(v.get("permitted", [])),
                "locked": v.get("locked", False),
                "hidden": v.get("hidden", False),
            }
        except Exception:
            continue

def _save_tv():
    try:
        os.makedirs(os.path.dirname(TV_DATA_FILE), exist_ok=True)
        raw = {str(k): {"owner_id": v["owner_id"], "guild_id": v["guild_id"],
                "panel_message_id": v.get("panel_message_id"),
                "blacklist": list(v.get("blacklist", [])),
                "permitted": list(v.get("permitted", [])),
                "locked": v.get("locked", False), "hidden": v.get("hidden", False)}
               for k, v in TEMP_VOICE.items()}
        with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=1)
    except Exception as e:
        print(f"[TempVoice] save error: {e}")

# ⚙️ CONFIG
ONETAP_CHANNEL_NAME = "➕ OneTap"
CATEGORY_NAME = "🎙️ Temp Voice"
DEFAULT_NAME_TEMPLATE = "{user}'s channel"


# ═══════════════════════════════════════════════════════════════════
# ─── STORAGE
# ═══════════════════════════════════════════════════════════════════
TEMP_VOICE: dict[int, dict] = {}
# {channel_id: {"owner_id": int, "guild_id": int, "panel_message_id": int,
#               "blacklist": set, "permitted": set,
#               "locked": bool, "hidden": bool}}


class TempVoice(commands.Cog):
    """Temp Voice: OneTap + Panel + `&vc <action>` commands"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════════════════════════
    # ─── HELPERS
    # ═══════════════════════════════════════════════════════════
    def _find_vc_by_owner(self, guild, user_id):
        """Qelleb 3la VC li owner dyalha huwa user"""
        for vc_id, data in TEMP_VOICE.items():
            if data["owner_id"] == user_id and data["guild_id"] == guild.id:
                vc = guild.get_channel(vc_id)
                if vc:
                    return vc, data
        return None, None

    def _get_user_vc(self, member: discord.Member):
        """Rje3 VC dyal member ila howa owner"""
        return self._find_vc_by_owner(member.guild, member.id)

    async def _create_temp_vc(self, member: discord.Member):
        """Creeyi temp VC w mouv user + sift PANEL"""
        guild = member.guild
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if category is None:
            try:
                category = await guild.create_category(CATEGORY_NAME)
            except discord.Forbidden:
                print(f"❌ Ma qdertch nsayeb category f {guild.name}")
                return None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=True),
            member: discord.PermissionOverwrite(
                view_channel=True, connect=True, manage_channels=True,
                move_members=True, mute_members=True, deafen_members=True,
            ),
        }

        name = DEFAULT_NAME_TEMPLATE.format(user=member.display_name)[:100]

        try:
            new_vc = await guild.create_voice_channel(
                name=name,
                category=category,
                overwrites=overwrites,
                reason=f"TempVoice par {member.name}",
            )
        except discord.Forbidden:
            print(f"❌ Ma qdertch nsayeb VC f {guild.name}")
            return None

        TEMP_VOICE[new_vc.id] = {
            "owner_id": member.id,
            "guild_id": guild.id,
            "panel_message_id": None,
            "blacklist": set(),
            "permitted": set(),
            "locked": False,
            "hidden": False,
        }

        try:
            if member.voice and member.voice.channel:
                await member.move_to(new_vc)
        except discord.Forbidden:
            pass

        await self._send_panel(new_vc, member)

        return new_vc

    async def _send_panel(self, vc: discord.VoiceChannel, owner: discord.Member):
        """Sift panel b buttons f chat dyal VC"""
        embed = self._build_panel_embed(owner)
        view = ControlPanel(self, vc.id, owner.id)
        try:
            msg = await vc.send(embed=embed, view=view)
            TEMP_VOICE[vc.id]["panel_message_id"] = msg.id
        except discord.Forbidden:
            print(f"❌ Ma qdertch nsift panel f {vc.name}")

    def _build_panel_embed(self, owner: discord.Member) -> discord.Embed:
        embed = discord.Embed(
            title="🌙 Good Night",
            description=(
                f"### Good night {owner.display_name} Interface\n"
                f"Click on the buttons below to control your voice channel.\n\n"
                f"**Awla st3mel `&vc <action>`** — Chouf `&vc help`"
            ),
            color=discord.Color.from_rgb(88, 101, 242),
            timestamp=datetime.now(),
        )
        embed.set_footer(text="Temp Voice System • Buttons + &vc commands")
        return embed

    async def _delete_temp_vc(self, vc: discord.VoiceChannel):
        TEMP_VOICE.pop(vc.id, None)
        try:
            await vc.delete(reason="TempVoice empty")
        except (discord.Forbidden, discord.NotFound):
            pass

    # ═══════════════════════════════════════════════════════════
    # ─── LISTENER
    # ═══════════════════════════════════════════════════════════
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        guild = member.guild

        # 1. OneTap
        if after.channel is not None and after.channel.name == ONETAP_CHANNEL_NAME:
            vc, _ = self._find_vc_by_owner(guild, member.id)
            if vc:
                try:
                    await member.move_to(vc)
                except discord.Forbidden:
                    pass
                return
            await self._create_temp_vc(member)
            return

        # 2. Delete ila khawi
        if before.channel is not None and before.channel.id in TEMP_VOICE:
            await asyncio.sleep(1.5)
            try:
                vc = guild.get_channel(before.channel.id)
                if vc is None:
                    TEMP_VOICE.pop(before.channel.id, None)
                    return
                if len(vc.members) == 0:
                    await self._delete_temp_vc(vc)
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════
    # ─── COMMAND: &ot
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="ot")
    async def ot_prefix(self, ctx: commands.Context):
        """&ot — Creeyi temp VC dyalk"""
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            return await ctx.send("❌ Khass tkoun f voice channel 9bel!")

        vc, _ = self._find_vc_by_owner(ctx.guild, ctx.author.id)
        if vc:
            try:
                await ctx.author.move_to(vc)
                return await ctx.send(f"✅ Deja 3endek: {vc.mention}")
            except discord.Forbidden:
                pass

        new_vc = await self._create_temp_vc(ctx.author)
        if new_vc:
            await ctx.send(f"✅ Temp VC tsayeb: {new_vc.mention}", delete_after=5)

    @app_commands.command(name="ot", description="Creeyi temp voice channel dyalk")
    async def ot_slash(self, interaction: discord.Interaction):
        if interaction.user.voice is None or interaction.user.voice.channel is None:
            return await interaction.response.send_message("❌ Khass tkoun f voice channel 9bel!", ephemeral=True)

        vc, _ = self._find_vc_by_owner(interaction.guild, interaction.user.id)
        if vc:
            try:
                await interaction.user.move_to(vc)
                return await interaction.response.send_message(f"✅ Deja 3endek: {vc.mention}", ephemeral=True)
            except discord.Forbidden:
                pass

        new_vc = await self._create_temp_vc(interaction.user)
        if new_vc:
            await interaction.response.send_message(f"✅ Temp VC tsayeb: {new_vc.mention}", ephemeral=True)

    # ═══════════════════════════════════════════════════════════
    # ─── COMMAND GROUP: &vc <action>
    # ═══════════════════════════════════════════════════════════
    @commands.group(name="vc", invoke_without_command=True)
    async def vc_group(self, ctx: commands.Context):
        """`&vc <action>` — Control VC dyalk"""
        await self._show_help(ctx)

    async def _show_help(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🎙️ TempVoice Commands",
            description="Control VC dyalk b had commands:",
            color=discord.Color.from_rgb(88, 101, 242),
        )
        embed.add_field(name="`&vc name <smiya>`", value="Beddel smiya dyal VC", inline=False)
        embed.add_field(name="`&vc limit <ra9m>`", value="7ded limit (0 = bla limit)", inline=False)
        embed.add_field(name="`&vc lock` / `&vc unlock`", value="Qfel wla Ftah VC", inline=False)
        embed.add_field(name="`&vc permit @user`", value="Sme7 l user ydkhol", inline=False)
        embed.add_field(name="`&vc reject @user`", value="Mn3 user ydkhol", inline=False)
        embed.add_field(name="`&vc hide` / `&vc show`", value="Khebbi wla Bayen VC", inline=False)
        embed.add_field(name="`&vc claim`", value="Khod ownership ila owner khrej", inline=False)
        embed.add_field(name="`&vc transfer @user`", value="3ti ownership l chi wa7ed", inline=False)
        embed.add_field(name="`&vc owner`", value="Chouf owner dyal VC", inline=False)
        embed.add_field(name="`&vc reset`", value="Rje3 kolchi default", inline=False)
        embed.add_field(name="`&vc close`", value="Msa7 VC dyalk", inline=False)
        embed.set_footer(text="Khass tkoun owner dyal VC bash t-controli")
        await ctx.send(embed=embed)

    async def _check_owner(self, ctx: commands.Context):
        vc, data = self._get_user_vc(ctx.author)
        if not vc:
            await ctx.send("❌ Ma 3endekch temp VC! St3mel `&ot` wla dkhol l `➕ OneTap`.")
            return None, None
        return vc, data

    # ─── &vc help
    @vc_group.command(name="help")
    async def vc_help(self, ctx: commands.Context):
        """`&vc help` — Kolchi"""
        await self._show_help(ctx)

    # ─── &vc name <smiya>
    @vc_group.command(name="name")
    async def vc_name(self, ctx: commands.Context, *, name: str):
        """`&vc name <smiya>` — Beddel smiya"""
        vc, data = await self._check_owner(ctx)
        if not vc:
            return
        try:
            await vc.edit(name=name[:100])
            await ctx.send(f"✅ Smiya tbeddlat l: **{name}**")
        except discord.Forbidden:
            await ctx.send("❌ Ma 3ndich permission!")

    # ─── &vc limit <ra9m>
    @vc_group.command(name="limit")
    async def vc_limit(self, ctx: commands.Context, limit: int):
        """`&vc limit <ra9m>` — 7ded limit"""
        if limit < 0 or limit > 99:
            return await ctx.send("❌ Ra9m bin `0` w `99`!")
        vc, data = await self._check_owner(ctx)
        if not vc:
            return
        try:
            await vc.edit(user_limit=limit)
            await ctx.send(f"✅ Limit wella: `{limit}`")
        except discord.Forbidden:
            await ctx.send("❌ Ma 3ndich permission!")

    # ─── &vc lock
    @vc_group.command(name="lock")
    async def vc_lock(self, ctx: commands.Context):
        """`&vc lock` — Qfel VC"""
        vc, data = await self._check_owner(ctx)
        if not vc:
            return
        overwrite = vc.overwrites_for(ctx.guild.default_role)
        overwrite.connect = False
        await vc.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        data["locked"] = True
        await ctx.send("🔒 VC t-qfel!")

    # ─── &vc unlock
    @vc_group.command(name="unlock")
    async def vc_unlock(self, ctx: commands.Context):
        """`&vc unlock` — Ftah VC"""
        vc, data = await self._check_owner(ctx)
        if not vc:
            return
        overwrite = vc.overwrites_for(ctx.guild.default_role)
        overwrite.connect = True
        await vc.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        data["locked"] = False
        await ctx.send("🔓 VC t-fta7!")

    # ─── &vc permit @user
    @vc_group.command(name="permit")
    async def vc_permit(self, ctx: commands.Context, member: discord.Member):
        """`&vc permit @user` — Sme7 l user"""
        vc, data = await self._check_owner(ctx)
        if not vc:
            return
        if member.id == ctx.author.id:
            return await ctx.send("❌ Deja 3endek access!")
        data["permitted"].add(member.id)
        data["blacklist"].discard(member.id)
        overwrite = vc.overwrites_for(member)
        overwrite.connect = True
        overwrite.view_channel = True
        await vc.set_permissions(member, overwrite=overwrite)
        await ctx.send(f"✅ {member.mention} t-permit!")

    # ─── &vc reject @user
    @vc_group.command(name="reject")
    async def vc_reject(self, ctx: commands.Context, member: discord.Member):
        """`&vc reject @user` — Mn3 user"""
        vc, data = await self._check_owner(ctx)
        if not vc:
            return
        if member.id == ctx.author.id:
            return await ctx.send("❌ Ma tqderch t-rejecti rasek!")
        data["blacklist"].add(member.id)
        data["permitted"].discard(member.id)
        overwrite = vc.overwrites_for(member)
        overwrite.connect = False
        overwrite.view_channel = False
        await vc.set_permissions(member, overwrite=overwrite)
        if member.voice and member.voice.channel and member.voice.channel.id == vc.id:
            try:
                await member.move_to(None)
            except discord.Forbidden:
                pass
        await ctx.send(f"❌ {member.mention} t-reject!")

    # ─── &vc hide
    @vc_group.command(name="hide")
    async def vc_hide(self, ctx: commands.Context):
        """`&vc hide` — Khebbi VC"""
        vc, data = await self._check_owner(ctx)
        if not vc:
            return
        overwrite = vc.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = False
        await vc.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        data["hidden"] = True
        await ctx.send("🙈 VC mkhbi!")

    # ─── &vc show
    @vc_group.command(name="show")
    async def vc_show(self, ctx: commands.Context):
        """`&vc show` — Bayen VC"""
        vc, data = await self._check_owner(ctx)
        if not vc:
            return
        overwrite = vc.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = True
        await vc.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        data["hidden"] = False
        await ctx.send("👁️ VC wella bayn!")

    # ─── &vc claim
    @vc_group.command(name="claim")
    async def vc_claim(self, ctx: commands.Context):
        """`&vc claim` — Khod ownership ila owner khrej"""
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            return await ctx.send("❌ Khass tkoun f VC!")
        vc = ctx.author.voice.channel
        data = TEMP_VOICE.get(vc.id)
        if not data:
            return await ctx.send("❌ Hadi machi temp VC!")

        owner = ctx.guild.get_member(data["owner_id"])
        if owner and owner.voice and owner.voice.channel and owner.voice.channel.id == vc.id:
            return await ctx.send("❌ Owner mazal f VC!")

        data["owner_id"] = ctx.author.id
        overwrites = vc.overwrites_for(ctx.author)
        overwrites.manage_channels = True
        overwrites.move_members = True
        overwrites.mute_members = True
        overwrites.deafen_members = True
        await vc.set_permissions(ctx.author, overwrite=overwrites)
        await ctx.send(f"👑 {ctx.author.mention} wella **owner** dyal VC!")

    # ─── &vc transfer @user
    @vc_group.command(name="transfer")
    async def vc_transfer(self, ctx: commands.Context, member: discord.Member):
        """`&vc transfer @user` — 3ti ownership"""
        vc, data = await self._check_owner(ctx)
        if not vc:
            return
        old_owner = ctx.guild.get_member(data["owner_id"])
        if old_owner:
            ow = vc.overwrites_for(old_owner)
            ow.manage_channels = None
            ow.move_members = None
            ow.mute_members = None
            ow.deafen_members = None
            await vc.set_permissions(old_owner, overwrite=ow)

        data["owner_id"] = member.id
        overwrite = vc.overwrites_for(member)
        overwrite.manage_channels = True
        overwrite.move_members = True
        overwrite.mute_members = True
        overwrite.deafen_members = True
        await vc.set_permissions(member, overwrite=overwrite)
        await ctx.send(f"🔀 Ownership t-3ta l {member.mention}!")

    # ─── &vc owner
    @vc_group.command(name="owner")
    async def vc_owner(self, ctx: commands.Context):
        """`&vc owner` — Chouf owner dyal VC"""
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            return await ctx.send("❌ Khass tkoun f VC!")
        vc = ctx.author.voice.channel
        data = TEMP_VOICE.get(vc.id)
        if not data:
            return await ctx.send("❌ Hadi machi temp VC!")
        owner = ctx.guild.get_member(data["owner_id"])
        owner_name = owner.mention if owner else f"`{data['owner_id']}`"
        await ctx.send(f"👤 Owner: {owner_name}")

    # ─── &vc reset
    @vc_group.command(name="reset")
    async def vc_reset(self, ctx: commands.Context):
        """`&vc reset` — Rje3 default"""
        vc, data = await self._check_owner(ctx)
        if not vc:
            return
        overwrite = vc.overwrites_for(ctx.guild.default_role)
        overwrite.connect = True
        overwrite.view_channel = True
        await vc.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        data["locked"] = False
        data["hidden"] = False
        data["blacklist"].clear()
        data["permitted"].clear()
        try:
            await vc.edit(user_limit=0)
        except discord.Forbidden:
            pass
        await ctx.send("🔄 VC t-reseta!")

    # ─── &vc close
    @vc_group.command(name="close")
    async def vc_close(self, ctx: commands.Context):
        """`&vc close` — Msa7 VC dyalk"""
        vc, data = await self._check_owner(ctx)
        if not vc:
            return
        await self._delete_temp_vc(vc)
        await ctx.send("🗑️ VC t-masa7!")


# =====================================================================
# ─── CONTROL PANEL VIEW (Buttons)
# =====================================================================
class ControlPanel(discord.ui.View):
    def __init__(self, cog: TempVoice, vc_id: int, owner_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.vc_id = vc_id
        self.owner_id = owner_id

    async def _check_owner(self, interaction: discord.Interaction) -> bool:
        data = TEMP_VOICE.get(self.vc_id)
        if not data:
            await interaction.response.send_message("❌ Had channel ma b9ach!", ephemeral=True)
            return False
        if interaction.user.id != data["owner_id"]:
            await interaction.response.send_message("❌ Ghir **owner** li kay9der ydir had chi!", ephemeral=True)
            return False
        return True

    # ═══════════════════════════════════════════════════════════
    # ─── ROW 1
    # ═══════════════════════════════════════════════════════════
    @discord.ui.button(label="Name", emoji="✏️", style=discord.ButtonStyle.secondary, row=0)
    async def name_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        await interaction.response.send_modal(NameModal(self.cog, self.vc_id))

    @discord.ui.button(label="Limit", emoji="👥", style=discord.ButtonStyle.secondary, row=0)
    async def limit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        await interaction.response.send_modal(LimitModal(self.cog, self.vc_id))

    @discord.ui.button(label="Lock", emoji="🔒", style=discord.ButtonStyle.secondary, row=0)
    async def lock_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        vc = interaction.guild.get_channel(self.vc_id)
        data = TEMP_VOICE.get(self.vc_id)
        if not vc or not data:
            return
        overwrite = vc.overwrites_for(interaction.guild.default_role)
        overwrite.connect = False
        await vc.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        data["locked"] = True
        await interaction.response.send_message("🔒 VC t-qfel!", ephemeral=True)

    @discord.ui.button(label="Unlock", emoji="🔓", style=discord.ButtonStyle.secondary, row=0)
    async def unlock_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        vc = interaction.guild.get_channel(self.vc_id)
        data = TEMP_VOICE.get(self.vc_id)
        if not vc or not data:
            return
        overwrite = vc.overwrites_for(interaction.guild.default_role)
        overwrite.connect = True
        await vc.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        data["locked"] = False
        await interaction.response.send_message("🔓 VC t-fta7!", ephemeral=True)

    @discord.ui.button(label="Claim", emoji="👑", style=discord.ButtonStyle.secondary, row=0)
    async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = TEMP_VOICE.get(self.vc_id)
        if not data:
            return await interaction.response.send_message("❌ Channel ma b9ach!", ephemeral=True)
        vc = interaction.guild.get_channel(self.vc_id)
        if not vc:
            return await interaction.response.send_message("❌ Channel ma b9ach!", ephemeral=True)

        owner = interaction.guild.get_member(data["owner_id"])
        if owner and owner.voice and owner.voice.channel and owner.voice.channel.id == vc.id:
            return await interaction.response.send_message("❌ Owner mazal f VC!", ephemeral=True)

        data["owner_id"] = interaction.user.id
        overwrites = vc.overwrites_for(interaction.user)
        overwrites.manage_channels = True
        overwrites.move_members = True
        overwrites.mute_members = True
        overwrites.deafen_members = True
        await vc.set_permissions(interaction.user, overwrite=overwrites)
        self.owner_id = interaction.user.id
        await interaction.response.send_message(f"👑 {interaction.user.mention} wella **owner** dyal VC!", ephemeral=True)

    # ═══════════════════════════════════════════════════════════
    # ─── ROW 2
    # ═══════════════════════════════════════════════════════════
    @discord.ui.button(label="Permit", emoji="✅", style=discord.ButtonStyle.success, row=1)
    async def permit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        await interaction.response.send_modal(PermitModal(self.cog, self.vc_id))

    @discord.ui.button(label="Reject", emoji="❌", style=discord.ButtonStyle.danger, row=1)
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        await interaction.response.send_modal(RejectModal(self.cog, self.vc_id))

    @discord.ui.button(label="Hide", emoji="🙈", style=discord.ButtonStyle.secondary, row=1)
    async def hide_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        vc = interaction.guild.get_channel(self.vc_id)
        data = TEMP_VOICE.get(self.vc_id)
        if not vc or not data:
            return
        overwrite = vc.overwrites_for(interaction.guild.default_role)
        overwrite.view_channel = False
        await vc.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        data["hidden"] = True
        await interaction.response.send_message("🙈 VC mkhbi!", ephemeral=True)

    @discord.ui.button(label="Show", emoji="👁️", style=discord.ButtonStyle.secondary, row=1)
    async def show_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        vc = interaction.guild.get_channel(self.vc_id)
        data = TEMP_VOICE.get(self.vc_id)
        if not vc or not data:
            return
        overwrite = vc.overwrites_for(interaction.guild.default_role)
        overwrite.view_channel = True
        await vc.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        data["hidden"] = False
        await interaction.response.send_message("👁️ VC wella bayn!", ephemeral=True)

    @discord.ui.button(label="Transfer", emoji="🔀", style=discord.ButtonStyle.secondary, row=1)
    async def transfer_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        await interaction.response.send_modal(TransferModal(self.cog, self.vc_id))

    # ═══════════════════════════════════════════════════════════
    # ─── ROW 3
    # ═══════════════════════════════════════════════════════════
    @discord.ui.button(label="Owner", emoji="👤", style=discord.ButtonStyle.secondary, row=2)
    async def owner_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = TEMP_VOICE.get(self.vc_id)
        if not data:
            return await interaction.response.send_message("❌ Ma b9ach!", ephemeral=True)
        owner = interaction.guild.get_member(data["owner_id"])
        owner_name = owner.mention if owner else f"`{data['owner_id']}`"
        await interaction.response.send_message(f"👤 Owner: {owner_name}", ephemeral=True)

    @discord.ui.button(label="Blacklist", emoji="🚫", style=discord.ButtonStyle.danger, row=2)
    async def blacklist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        data = TEMP_VOICE.get(self.vc_id)
        bl = data["blacklist"] if data else set()
        if bl:
            mentions = "\n".join(f"<@{uid}>" for uid in bl)
            await interaction.response.send_message(f"🚫 **Blacklist:**\n{mentions}", ephemeral=True)
        else:
            await interaction.response.send_message("🚫 Blacklist khawi!", ephemeral=True)

    @discord.ui.button(label="Info", emoji="ℹ️", style=discord.ButtonStyle.secondary, row=2)
    async def info_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = TEMP_VOICE.get(self.vc_id)
        if not data:
            return await interaction.response.send_message("❌ Ma b9ach!", ephemeral=True)
        vc = interaction.guild.get_channel(self.vc_id)
        owner = interaction.guild.get_member(data["owner_id"])
        embed = discord.Embed(title="ℹ️ Channel Info", color=discord.Color.blue())
        embed.add_field(name="👑 Owner", value=owner.mention if owner else f"`{data['owner_id']}`", inline=True)
        embed.add_field(name="🔒 Locked", value=f"`{data['locked']}`", inline=True)
        embed.add_field(name="🙈 Hidden", value=f"`{data['hidden']}`", inline=True)
        embed.add_field(name="👥 Limit", value=f"`{vc.user_limit if vc else 0}`", inline=True)
        embed.add_field(name="✅ Permitted", value=f"`{len(data['permitted'])}`", inline=True)
        embed.add_field(name="🚫 Blacklist", value=f"`{len(data['blacklist'])}`", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Help", emoji="❓", style=discord.ButtonStyle.secondary, row=2)
    async def help_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❓ Help — Temp Voice",
            description=(
                "**Buttons** — Click 3la ay button\n"
                "**Commands** — `&vc <action>` (chouf `&vc help`)\n\n"
                "**Actions:**\n"
                "✏️ Name — Beddel smiya\n"
                "👥 Limit — 7ded members\n"
                "🔒 Lock / 🔓 Unlock\n"
                "👑 Claim — Khod ownership\n"
                "✅ Permit / ❌ Reject\n"
                "🙈 Hide / 👁️ Show\n"
                "🔀 Transfer — 3ti ownership"
            ),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ═══════════════════════════════════════════════════════════
    # ─── ROW 4
    # ═══════════════════════════════════════════════════════════
    @discord.ui.button(label="Reset", emoji="🔄", style=discord.ButtonStyle.secondary, row=3)
    async def reset_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        vc = interaction.guild.get_channel(self.vc_id)
        data = TEMP_VOICE.get(self.vc_id)
        if not vc or not data:
            return
        overwrite = vc.overwrites_for(interaction.guild.default_role)
        overwrite.connect = True
        overwrite.view_channel = True
        await vc.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        data["locked"] = False
        data["hidden"] = False
        data["blacklist"].clear()
        data["permitted"].clear()
        try:
            await vc.edit(user_limit=0)
        except discord.Forbidden:
            pass
        await interaction.response.send_message("🔄 VC t-reseta!", ephemeral=True)


# =====================================================================
# ─── MODALS
# =====================================================================
class NameModal(discord.ui.Modal, title="✏️ Beddel smiya"):
    name = discord.ui.TextInput(label="Smiya jdida", max_length=100)

    def __init__(self, cog: TempVoice, vc_id: int):
        super().__init__()
        self.cog = cog
        self.vc_id = vc_id

    async def on_submit(self, interaction: discord.Interaction):
        vc = interaction.guild.get_channel(self.vc_id)
        if not vc:
            return await interaction.response.send_message("❌ Ma b9ach!", ephemeral=True)
        try:
            await vc.edit(name=self.name.value)
            await interaction.response.send_message(f"✅ Smiya tbeddlat l: **{self.name.value}**", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Ma 3ndich permission!", ephemeral=True)


class LimitModal(discord.ui.Modal, title="👥 Beddel limit"):
    limit = discord.ui.TextInput(label="Limit (0 = bla limit)", max_length=2)

    def __init__(self, cog: TempVoice, vc_id: int):
        super().__init__()
        self.cog = cog
        self.vc_id = vc_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit = int(self.limit.value)
            if limit < 0 or limit > 99:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message("❌ Ra9m bin 0 w 99!", ephemeral=True)
        vc = interaction.guild.get_channel(self.vc_id)
        if not vc:
            return await interaction.response.send_message("❌ Ma b9ach!", ephemeral=True)
        try:
            await vc.edit(user_limit=limit)
            await interaction.response.send_message(f"✅ Limit wella: `{limit}`", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Ma 3ndich permission!", ephemeral=True)


class PermitModal(discord.ui.Modal, title="✅ Permit user"):
    user_id = discord.ui.TextInput(label="User ID", max_length=20)

    def __init__(self, cog: TempVoice, vc_id: int):
        super().__init__()
        self.cog = cog
        self.vc_id = vc_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = int(self.user_id.value)
        except ValueError:
            return await interaction.response.send_message("❌ ID ghalat!", ephemeral=True)
        data = TEMP_VOICE.get(self.vc_id)
        vc = interaction.guild.get_channel(self.vc_id)
        if not data or not vc:
            return await interaction.response.send_message("❌ Ma b9ach!", ephemeral=True)
        member = interaction.guild.get_member(uid)
        if not member:
            return await interaction.response.send_message("❌ Member ma kaynch!", ephemeral=True)
        data["permitted"].add(uid)
        data["blacklist"].discard(uid)
        overwrite = vc.overwrites_for(member)
        overwrite.connect = True
        overwrite.view_channel = True
        await vc.set_permissions(member, overwrite=overwrite)
        await interaction.response.send_message(f"✅ {member.mention} t-permit!", ephemeral=True)


class RejectModal(discord.ui.Modal, title="❌ Reject user"):
    user_id = discord.ui.TextInput(label="User ID", max_length=20)

    def __init__(self, cog: TempVoice, vc_id: int):
        super().__init__()
        self.cog = cog
        self.vc_id = vc_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = int(self.user_id.value)
        except ValueError:
            return await interaction.response.send_message("❌ ID ghalat!", ephemeral=True)
        data = TEMP_VOICE.get(self.vc_id)
        vc = interaction.guild.get_channel(self.vc_id)
        if not data or not vc:
            return await interaction.response.send_message("❌ Ma b9ach!", ephemeral=True)
        member = interaction.guild.get_member(uid)
        if not member:
            return await interaction.response.send_message("❌ Member ma kaynch!", ephemeral=True)
        data["blacklist"].add(uid)
        data["permitted"].discard(uid)
        overwrite = vc.overwrites_for(member)
        overwrite.connect = False
        overwrite.view_channel = False
        await vc.set_permissions(member, overwrite=overwrite)
        if member.voice and member.voice.channel and member.voice.channel.id == vc.id:
            try:
                await member.move_to(None)
            except discord.Forbidden:
                pass
        await interaction.response.send_message(f"❌ {member.mention} t-reject!", ephemeral=True)


class TransferModal(discord.ui.Modal, title="🔀 Transfer ownership"):
    user_id = discord.ui.TextInput(label="User ID dyal owner jdid", max_length=20)

    def __init__(self, cog: TempVoice, vc_id: int):
        super().__init__()
        self.cog = cog
        self.vc_id = vc_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = int(self.user_id.value)
        except ValueError:
            return await interaction.response.send_message("❌ ID ghalat!", ephemeral=True)
        data = TEMP_VOICE.get(self.vc_id)
        vc = interaction.guild.get_channel(self.vc_id)
        if not data or not vc:
            return await interaction.response.send_message("❌ Ma b9ach!", ephemeral=True)
        new_owner = interaction.guild.get_member(uid)
        if not new_owner:
            return await interaction.response.send_message("❌ Member ma kaynch!", ephemeral=True)

        old_owner = interaction.guild.get_member(data["owner_id"])
        if old_owner:
            ow = vc.overwrites_for(old_owner)
            ow.manage_channels = None
            ow.move_members = None
            ow.mute_members = None
            ow.deafen_members = None
            await vc.set_permissions(old_owner, overwrite=ow)

        data["owner_id"] = uid
        overwrite = vc.overwrites_for(new_owner)
        overwrite.manage_channels = True
        overwrite.move_members = True
        overwrite.mute_members = True
        overwrite.deafen_members = True
        await vc.set_permissions(new_owner, overwrite=overwrite)
        await interaction.response.send_message(f"🔀 Ownership t-3ta l {new_owner.mention}!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(TempVoice(bot))