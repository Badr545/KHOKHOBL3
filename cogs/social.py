# cogs/social.py
# =====================================================================
# ─── SOCIAL — Marriage / Bio / Rep / Clans
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta

DATA_FILE = "data/social.json"


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


SOCIAL = _load()


def _get(gid: int, uid: int) -> dict:
    SOCIAL.setdefault(gid, {}).setdefault(uid, {
        "bio": "",
        "married_to": None,
        "married_at": None,
        "reps": 0,
        "last_rep": None,
        "clan": None,
        "social_links": {},
    })
    return SOCIAL[gid][uid]


class Social(commands.Cog):
    """Marriage / Bio / Rep / Clans"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════════════════════════
    # ─── /bio
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="bio", description="📝 Set bio dyalk")
    @app_commands.describe(text="Bio (max 200 chars)", member="Chouf bio dyal chi wa7ed")
    async def bio_cmd(self, it: discord.Interaction, text: str = None, member: discord.Member = None):
        if member is None:
            if text is None:
                # Show
                d = _get(it.guild.id, it.user.id)
                embed = discord.Embed(
                    title=f"📝 Bio — {it.user.display_name}",
                    description=d["bio"] or "*Ma kaynch bio*",
                    color=discord.Color.blurple(),
                )
                return await it.response.send_message(embed=embed)
            # Set
            text = text[:200]
            d = _get(it.guild.id, it.user.id)
            d["bio"] = text
            _save(SOCIAL)
            return await it.response.send_message(f"✅ Bio: {text}")

        # Show member
        d = _get(it.guild.id, member.id)
        embed = discord.Embed(
            title=f"📝 Bio — {member.display_name}",
            description=d["bio"] or "*Ma kaynch bio*",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await it.response.send_message(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /marry
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="marry", description="💍 3red zwaj 3la chi wa7ed")
    async def marry(self, it: discord.Interaction, member: discord.Member):
        if member.bot or member.id == it.user.id:
            return await it.response.send_message("❌ Ghir @user!", ephemeral=True)

        my = _get(it.guild.id, it.user.id)
        their = _get(it.guild.id, member.id)

        if my["married_to"]:
            return await it.response.send_message("❌ Deja mzewej!", ephemeral=True)
        if their["married_to"]:
            return await it.response.send_message(f"❌ {member.mention} deja mzewej!", ephemeral=True)

        embed = discord.Embed(
            title="💍 Marriage Proposal",
            description=f"{it.user.mention} 3red 3la {member.mention}!\n\n**{member.name}** — Accept?",
            color=discord.Color.pink(),
        )
        view = MarryView(it.user.id, member.id)
        await it.response.send_message(embed=embed, view=view)

    # ═══════════════════════════════════════════════════════════
    # ─── /divorce
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="divorce", description="💔 Talla9")
    async def divorce(self, it: discord.Interaction):
        d = _get(it.guild.id, it.user.id)
        if not d["married_to"]:
            return await it.response.send_message("❌ Ma nti mzewej!", ephemeral=True)

        partner_id = d["married_to"]
        d["married_to"] = None
        d["married_at"] = None

        partner = _get(it.guild.id, partner_id)
        partner["married_to"] = None
        partner["married_at"] = None
        _save(SOCIAL)

        await it.response.send_message(f"💔 Tallaqti mn <@{partner_id}>")

    # ═══════════════════════════════════════════════════════════
    # ─── /rep
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="rep", description="⭐ 3ti rep l chi wa7ed")
    async def rep(self, it: discord.Interaction, member: discord.Member):
        if member.bot or member.id == it.user.id:
            return await it.response.send_message("❌ Ghir @user!", ephemeral=True)

        my = _get(it.guild.id, it.user.id)
        now = datetime.now()
        if my["last_rep"]:
            last = datetime.fromisoformat(my["last_rep"])
            if now - last < timedelta(hours=24):
                rem = timedelta(hours=24) - (now - last)
                return await it.response.send_message(
                    f"⏰ 3awed mn ba3d `{rem.seconds // 3600}h {(rem.seconds % 3600) // 60}m`!",
                    ephemeral=True,
                )

        my["last_rep"] = now.isoformat()
        their = _get(it.guild.id, member.id)
        their["reps"] += 1
        _save(SOCIAL)

        await it.response.send_message(f"⭐ {member.mention} 3endou daba `{their['reps']}` reps!")

    # ═══════════════════════════════════════════════════════════
    # ─── CLANS
    # ═══════════════════════════════════════════════════════════
    clan_group = app_commands.Group(name="clan", description="⚔️ Clans system")

    @clan_group.command(name="create", description="Sayeb clan")
    async def clan_create(self, it: discord.Interaction, name: str):
        if len(name) > 30:
            return await it.response.send_message("❌ Name twil!", ephemeral=True)
        # Check name unique
        for gid, users in SOCIAL.items():
            if gid != it.guild.id:
                continue
            for uid, d in users.items():
                if d.get("clan") and d["clan"]["name"].lower() == name.lower():
                    return await it.response.send_message("❌ Name mst3ml!", ephemeral=True)

        d = _get(it.guild.id, it.user.id)
        if d["clan"]:
            return await it.response.send_message("❌ Deja f clan! `/clan leave`", ephemeral=True)

        d["clan"] = {"name": name, "founder": it.user.id, "created": datetime.now().isoformat()}
        _save(SOCIAL)
        await it.response.send_message(f"⚔️ Clan **{name}** tsayeb!")

    @clan_group.command(name="join", description="Dkhol l clan")
    async def clan_join(self, it: discord.Interaction, name: str):
        d = _get(it.guild.id, it.user.id)
        if d["clan"]:
            return await it.response.send_message("❌ Deja f clan!", ephemeral=True)
        # Find clan
        target = None
        for uid, ud in SOCIAL.get(it.guild.id, {}).items():
            if ud.get("clan") and ud["clan"]["name"].lower() == name.lower():
                target = ud["clan"]
                break
        if not target:
            return await it.response.send_message("❌ Clan ma kaynch!", ephemeral=True)

        d["clan"] = {"name": target["name"], "founder": target["founder"], "created": target["created"]}
        _save(SOCIAL)
        await it.response.send_message(f"✅ Dkhelti l **{target['name']}**!")

    @clan_group.command(name="leave", description="Kherj mn clan")
    async def clan_leave(self, it: discord.Interaction):
        d = _get(it.guild.id, it.user.id)
        if not d["clan"]:
            return await it.response.send_message("❌ Ma nti f clan!", ephemeral=True)
        name = d["clan"]["name"]
        d["clan"] = None
        _save(SOCIAL)
        await it.response.send_message(f"👋 Khrjti mn **{name}**")

    @clan_group.command(name="info", description="Chouf clan")
    async def clan_info(self, it: discord.Interaction, name: str = None):
        if name is None:
            d = _get(it.guild.id, it.user.id)
            if not d["clan"]:
                return await it.response.send_message("❌ Ma nti f clan!", ephemeral=True)
            name = d["clan"]["name"]

        members = []
        for uid, ud in SOCIAL.get(it.guild.id, {}).items():
            if ud.get("clan") and ud["clan"]["name"].lower() == name.lower():
                m = it.guild.get_member(uid)
                members.append(m.mention if m else f"<@{uid}>")

        embed = discord.Embed(title=f"⚔️ Clan — {name}", color=discord.Color.dark_red())
        embed.add_field(name="👥 Members", value=f"`{len(members)}`", inline=True)
        embed.add_field(name="📋 List", value="\n".join(members[:20]) or "—", inline=False)
        await it.response.send_message(embed=embed)

    @clan_group.command(name="top", description="Top clans")
    async def clan_top(self, it: discord.Interaction):
        clans = {}
        for uid, ud in SOCIAL.get(it.guild.id, {}).items():
            if ud.get("clan"):
                n = ud["clan"]["name"]
                clans[n] = clans.get(n, 0) + 1
        top = sorted(clans.items(), key=lambda x: x[1], reverse=True)[:10]
        if not top:
            return await it.response.send_message("❌ Ma kaynch clans!", ephemeral=True)
        medals = ["🥇", "🥈", "🥉"]
        lines = [
            f"{medals[i] if i < 3 else f'#{i+1}'} **{n}** — `{c}` members"
            for i, (n, c) in enumerate(top)
        ]
        await it.response.send_message("⚔️ **Top Clans:**\n" + "\n".join(lines))

    # ═══════════════════════════════════════════════════════════
    # ─── /socialcard — Full profile
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="socialcard", description="📇 Full social profile")
    async def socialcard(self, it: discord.Interaction, member: discord.Member = None):
        member = member or it.user
        d = _get(it.guild.id, member.id)

        embed = discord.Embed(
            title=f"📇 {member.display_name}",
            color=discord.Color.pink(),
            timestamp=datetime.now(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        if d["bio"]:
            embed.add_field(name="📝 Bio", value=d["bio"], inline=False)

        if d["married_to"]:
            partner = it.guild.get_member(d["married_to"])
            embed.add_field(name="💍 Married to", value=partner.mention if partner else "?", inline=True)
        else:
            embed.add_field(name="💍 Status", value="Single", inline=True)

        embed.add_field(name="⭐ Reps", value=f"`{d['reps']}`", inline=True)

        if d["clan"]:
            embed.add_field(name="⚔️ Clan", value=f"**{d['clan']['name']}**", inline=True)

        await it.response.send_message(embed=embed)


class MarryView(discord.ui.View):
    def __init__(self, proposer_id: int, target_id: int):
        super().__init__(timeout=120)
        self.proposer_id = proposer_id
        self.target_id = target_id

    async def interaction_check(self, it):
        if it.user.id != self.target_id:
            await it.response.send_message("❌ Machi dyalek!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Accept", emoji="💍", style=discord.ButtonStyle.success)
    async def accept(self, it: discord.Interaction, b):
        gid = it.guild.id
        p = _get(gid, self.proposer_id)
        t = _get(gid, self.target_id)

        if p["married_to"] or t["married_to"]:
            return await it.response.send_message("❌ Wa7ed mnk mzewej!", ephemeral=True)

        now = datetime.now().isoformat()
        p["married_to"] = self.target_id
        p["married_at"] = now
        t["married_to"] = self.proposer_id
        t["married_at"] = now
        _save(SOCIAL)

        for c in self.children:
            c.disabled = True
        embed = discord.Embed(
            title="💍 MABROUK!",
            description=f"<@{self.proposer_id}> ❤️ <@{self.target_id}>",
            color=discord.Color.pink(),
        )
        await it.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Reject", emoji="💔", style=discord.ButtonStyle.danger)
    async def reject(self, it: discord.Interaction, b):
        for c in self.children:
            c.disabled = True
        await it.response.edit_message(
            embed=discord.Embed(title="💔 Rejected", color=discord.Color.red()),
            view=self,
        )
        self.stop()


async def setup(bot):
    await bot.add_cog(Social(bot))