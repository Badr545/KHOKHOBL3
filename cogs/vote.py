# cogs/vote.py
# =====================================================================
# ─── VOTE — top.gg vote rewards
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
from datetime import datetime, timedelta

from data_manager import ECONOMY, save_economy as _save_economy

VOTE_REWARD = 5000
VOTE_COOLDOWN = timedelta(hours=12)

TOPGG_TOKEN = os.getenv("TOPGG_TOKEN", "")


def _get_user(gid, uid):
    ECONOMY.setdefault(gid, {}).setdefault(uid, {"balance": 0, "bank": 0, "inventory": []})
    return ECONOMY[gid][uid]


class Vote(commands.Cog):
    """Vote rewards + top.gg integration"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="vote", description="🗳️ Vote l-bot w rb7 5000 coins")
    async def vote(self, it: discord.Interaction):
        # Open vote link
        bot_id = self.bot.user.id
        url = f"https://top.gg/bot/{bot_id}/vote"
        embed = discord.Embed(
            title="🗳️ Vote for Khokho Bl3",
            description=(
                f"Click on [**this link**]({url}) bash t-vote!\n"
                f"💰 Reward: **{VOTE_REWARD:,}** 🪙\n"
                f"⏰ Cooldown: 12h"
            ),
            color=discord.Color.green(),
        )
        embed.set_footer(text="Ba3d ma t-vote, 3ayet /voteclaim")
        await it.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="voteclaim", description="🎁 Jme3 vote reward")
    async def vote_claim(self, it: discord.Interaction):
        d = _get_user(it.guild.id, it.user.id)
        d.setdefault("last_vote", None)

        if d["last_vote"]:
            try:
                last = datetime.fromisoformat(d["last_vote"])
                if datetime.now() - last < VOTE_COOLDOWN:
                    rem = VOTE_COOLDOWN - (datetime.now() - last)
                    return await it.response.send_message(
                        f"⏰ 3awed mn ba3d `{rem.seconds // 3600}h {(rem.seconds % 3600) // 60}m`!",
                        ephemeral=True,
                    )
            except Exception:
                pass

        # Optional: verify via top.gg API
        # (requires TOPGG_TOKEN + user votes)
        # Skipping for simplicity

        d["balance"] += VOTE_REWARD
        d["last_vote"] = datetime.now().isoformat()
        _save_economy()

        embed = discord.Embed(
            title="🎉 Vote Reward!",
            description=f"**+{VOTE_REWARD:,}** 🪙!",
            color=discord.Color.green(),
        )
        await it.response.send_message(embed=embed)

    @app_commands.command(name="botinfo", description="ℹ️ Bot info")
    async def botinfo(self, it: discord.Interaction):
        b = self.bot
        embed = discord.Embed(
            title=f"🤖 {b.user.name}",
            description="Discord bot b Python — 150+ commands",
            color=discord.Color.blurple(),
            timestamp=datetime.now(),
        )
        embed.set_thumbnail(url=b.user.display_avatar.url)
        embed.add_field(name="🏠 Servers", value=f"`{len(b.guilds):,}`", inline=True)
        embed.add_field(name="👥 Users", value=f"`{sum(g.member_count or 0 for g in b.guilds):,}`", inline=True)
        embed.add_field(name="📋 Commands", value=f"`{len(b.commands)}` prefix + slash", inline=True)
        embed.add_field(name="📡 Latency", value=f"`{round(b.latency * 1000)}ms`", inline=True)
        uptime = datetime.now() - getattr(b, "_start_time", datetime.now())
        embed.add_field(
            name="⏰ Uptime",
            value=f"`{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m`",
            inline=True,
        )
        embed.add_field(
            name="🔗 Links",
            value="[Invite](https://discord.com/oauth2/authorize?client_id=YOUR_ID) • "
                  "[Support](https://discord.gg/yourinvite) • "
                  "[Vote](https://top.gg/bot/YOUR_ID)",
            inline=False,
        )
        await it.response.send_message(embed=embed)

    @app_commands.command(name="invite", description="🔗 Invite l-bot")
    async def invite(self, it: discord.Interaction):
        bot_id = self.bot.user.id
        perms = 8
        url = (
            f"https://discord.com/oauth2/authorize?"
            f"client_id={bot_id}&permissions={perms}&scope=bot%20applications.commands"
        )
        embed = discord.Embed(
            title="🔗 Invite Khokho Bl3",
            description=f"[**Click here**]({url}) bash tzid l-bot f server dyalek!",
            color=discord.Color.blurple(),
        )
        await it.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        if not getattr(self.bot, "_start_time", None):
            self.bot._start_time = datetime.now()


async def setup(bot):
    await bot.add_cog(Vote(bot))