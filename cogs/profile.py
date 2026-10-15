# cogs/profile.py
# =====================================================================
# ─── PROFILE — Bio + Status customization
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
import json
import os

DATA_FILE = "data/profiles.json"


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


PROFILES = _load()


def _get(gid: int, uid: int) -> dict:
    PROFILES.setdefault(gid, {}).setdefault(uid, {
        "status": "",
        "social_links": {},
    })
    return PROFILES[gid][uid]


class Profile(commands.Cog):
    """Profile customization"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="status", description="🎭 Set custom status f profile")
    @app_commands.describe(text="Status (max 100) — khawi = view")
    async def status_cmd(self, it: discord.Interaction, text: str = None):
        d = _get(it.guild.id, it.user.id)
        if text is None:
            current = d["status"] or "*none*"
            return await it.response.send_message(
                f"🎭 Status dyalek: {current}", ephemeral=True
            )
        d["status"] = text[:100]
        _save(PROFILES)
        await it.response.send_message(f"✅ Status: {d['status']}", ephemeral=True)

    @app_commands.command(name="sociallinks", description="🔗 Set social links")
    @app_commands.describe(platform="twitter/youtube/github/website/twitch/tiktok", url="URL (khawi = remove)")
    async def sociallinks(self, it: discord.Interaction, platform: str, url: str = None):
        d = _get(it.guild.id, it.user.id)
        platform = platform.lower()
        valid = ("twitter", "youtube", "github", "website", "twitch", "tiktok")
        if platform not in valid:
            return await it.response.send_message(
                f"❌ Platform khass: {', '.join(valid)}", ephemeral=True
            )
        if url is None:
            d["social_links"].pop(platform, None)
            _save(PROFILES)
            return await it.response.send_message(f"✅ {platform} removed!", ephemeral=True)
        d["social_links"][platform] = url[:200]
        _save(PROFILES)
        await it.response.send_message(f"✅ {platform}: {url}", ephemeral=True)

    @app_commands.command(name="myprofile", description="👤 Chouf profile dyalek")
    @app_commands.describe(member="L-user")
    async def myprofile(self, it: discord.Interaction, member: discord.Member = None):
        member = member or it.user
        d = _get(it.guild.id, member.id)

        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        if d["status"]:
            embed.add_field(name="🎭 Status", value=d["status"], inline=False)

        if d["social_links"]:
            links = "\n".join(f"• **{k}**: {v}" for k, v in d["social_links"].items())
            embed.add_field(name="🔗 Links", value=links, inline=False)
        else:
            embed.add_field(name="🔗 Links", value="*none*", inline=False)

        embed.set_footer(text=f"ID: {member.id}")
        await it.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Profile(bot))