# cogs/achievements.py
# =====================================================================
# ─── ACHIEVEMENTS + BADGES — Unlock system + Profile card
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

from data_manager import ECONOMY, LEVELS, BIR

DATA_FILE = "data/achievements.json"


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


ACHIEVEMENTS = _load()


# ═══════════════════════════════════════════════════════════════════
# ─── CATALOG
# ═══════════════════════════════════════════════════════════════════
ACHIEVEMENTS_LIST = {
    # ─── Money
    "first_1k":     {"name": "💰 First 1K",      "desc": "Wsel l 1,000 coins",      "emoji": "💰"},
    "rich_10k":     {"name": "💎 10K Club",      "desc": "Wsel l 10,000 coins",     "emoji": "💎"},
    "rich_100k":    {"name": "👑 100K Club",     "desc": "Wsel l 100,000 coins",    "emoji": "👑"},
    "millionaire":  {"name": "🏆 Millionaire",   "desc": "Wsel l 1,000,000 coins",  "emoji": "🏆"},
    # ─── Levels
    "lvl_10":       {"name": "🎯 Level 10",      "desc": "Wsel l Level 10",         "emoji": "🎯"},
    "lvl_25":       {"name": "⚡ Level 25",      "desc": "Wsel l Level 25",         "emoji": "⚡"},
    "lvl_50":       {"name": "🔥 Level 50",      "desc": "Wsel l Level 50",         "emoji": "🔥"},
    "lvl_100":      {"name": "🌟 Level 100",     "desc": "Wsel l Level 100",        "emoji": "🌟"},
    # ─── Bir
    "bir_100":      {"name": "🔮 Bir Beginner",  "desc": "Jme3 100 Bir",            "emoji": "🔮"},
    "bir_1000":     {"name": "✨ Bir Master",     "desc": "Jme3 1,000 Bir",          "emoji": "✨"},
    # ─── Gambling
    "bj_winner":    {"name": "🃏 Blackjack Pro", "desc": "Rb7 blackjack",           "emoji": "🃏"},
    "slots_jackpot":{"name": "🎰 Jackpot!",      "desc": "Rb7 slots jackpot",       "emoji": "🎰"},
    "gambler":      {"name": "🎲 Gambler",        "desc": "L3eb 50 casino games",   "emoji": "🎲"},
    # ─── Social
    "first_daily":  {"name": "🎁 Daily Grind",    "desc": "Claimi daily awal mra",  "emoji": "🎁"},
    "robber":       {"name": "🥷 Robber",         "desc": "Srq chi wa7ed بنجاح",   "emoji": "🥷"},
    "business_owner":{"name": "🏢 Businessman",   "desc": "Chri business",           "emoji": "🏢"},
    "trader":       {"name": "📈 Trader",         "desc": "Chri stocks",             "emoji": "📈"},
    "collector":    {"name": "📋 Collector",      "desc": "Jme3 income 10 mrat",     "emoji": "📋"},
}


class Achievements(commands.Cog):
    """Achievements + Badges system"""

    def __init__(self, bot):
        self.bot = bot

    def _get(self, gid: int, uid: int) -> dict:
        ACHIEVEMENTS.setdefault(gid, {}).setdefault(uid, {
            "unlocked": [],
            "unlocked_at": {},
            "casino_plays": 0,
            "collects": 0,
        })
        return ACHIEVEMENTS[gid][uid]

    async def unlock(self, member: discord.Member, ach_id: str) -> bool:
        """Unlock achievement ila machi deja unlocked."""
        if ach_id not in ACHIEVEMENTS_LIST:
            return False
        data = self._get(member.guild.id, member.id)
        if ach_id in data["unlocked"]:
            return False
        data["unlocked"].append(ach_id)
        data["unlocked_at"][ach_id] = datetime.now().isoformat()
        _save(ACHIEVEMENTS)

        ach = ACHIEVEMENTS_LIST[ach_id]
        try:
            embed = discord.Embed(
                title=f"🏆 Achievement Unlocked!",
                description=f"{ach['emoji']} **{ach['name']}**\n{ach['desc']}",
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow(),
            )
            embed.set_footer(text=f"{member.display_name}", icon_url=member.display_avatar.url)
            await member.send(embed=embed)
        except Exception:
            pass
        return True

    async def check_money(self, member: discord.Member):
        eco = ECONOMY.get(member.guild.id, {}).get(member.id, {})
        total = eco.get("balance", 0) + eco.get("bank", 0)
        if total >= 1_000:      await self.unlock(member, "first_1k")
        if total >= 10_000:     await self.unlock(member, "rich_10k")
        if total >= 100_000:    await self.unlock(member, "rich_100k")
        if total >= 1_000_000:  await self.unlock(member, "millionaire")

    async def check_level(self, member: discord.Member):
        lv = LEVELS.get(member.guild.id, {}).get(member.id, {}).get("level", 0)
        if lv >= 10:   await self.unlock(member, "lvl_10")
        if lv >= 25:   await self.unlock(member, "lvl_25")
        if lv >= 50:   await self.unlock(member, "lvl_50")
        if lv >= 100:  await self.unlock(member, "lvl_100")

    async def check_bir(self, member: discord.Member):
        b = BIR.get(member.guild.id, {}).get(member.id, {}).get("bir", 0)
        if b >= 100:   await self.unlock(member, "bir_100")
        if b >= 1000:  await self.unlock(member, "bir_1000")

    # ═══════════════════════════════════════════════════════════
    # ─── LISTENERS (auto-check)
    # ═══════════════════════════════════════════════════════════
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        # Check every 20 messages
        data = self._get(message.guild.id, message.author.id)
        if (len(data["unlocked"]) % 5) == 0:
            await self.check_money(message.author)
            await self.check_level(message.author)
            await self.check_bir(message.author)

    # ═══════════════════════════════════════════════════════════
    # ─── /profile
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="profile", description="🏆 Profile dyalk b badges")
    @app_commands.describe(member="L-user")
    async def profile(self, it: discord.Interaction, member: discord.Member = None):
        member = member or it.user
        data = self._get(it.guild.id, member.id)
        eco = ECONOMY.get(it.guild.id, {}).get(member.id, {})
        lv = LEVELS.get(it.guild.id, {}).get(member.id, {})
        bir = BIR.get(it.guild.id, {}).get(member.id, {}).get("bir", 0)

        unlocked = data["unlocked"]
        total_ach = len(ACHIEVEMENTS_LIST)
        progress = len(unlocked) / total_ach * 100

        embed = discord.Embed(
            title=f"🏆 {member.display_name}",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="💰 Coins", value=f"`{(eco.get('balance',0)+eco.get('bank',0)):,}` 🪙", inline=True)
        embed.add_field(name="📊 Level", value=f"`{lv.get('level',0)}`", inline=True)
        embed.add_field(name="🔮 Bir", value=f"`{bir:,}`", inline=True)

        embed.add_field(
            name=f"🏆 Achievements ({len(unlocked)}/{total_ach})",
            value=f"`{progress:.1f}%`",
            inline=False,
        )

        if unlocked:
            badges = " ".join(ACHIEVEMENTS_LIST[a]["emoji"] for a in unlocked[-15:] if a in ACHIEVEMENTS_LIST)
            embed.add_field(name="🎖️ Badges", value=badges or "—", inline=False)

        embed.set_footer(text=f"ID: {member.id}")
        await it.response.send_message(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /achievements
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="achievements", description="📋 List dyal achievements")
    async def achievements_list(self, it: discord.Interaction, member: discord.Member = None):
        member = member or it.user
        data = self._get(it.guild.id, member.id)
        unlocked = data["unlocked"]

        embed = discord.Embed(
            title=f"🏆 Achievements — {member.display_name}",
            description=f"**{len(unlocked)}/{len(ACHIEVEMENTS_LIST)}** unlocked",
            color=discord.Color.gold(),
        )
        for aid, ach in ACHIEVEMENTS_LIST.items():
            done = aid in unlocked
            emoji = "✅" if done else "🔒"
            embed.add_field(
                name=f"{emoji} {ach['emoji']} {ach['name']}",
                value=ach["desc"],
                inline=False,
            )
        await it.response.send_message(embed=embed, ephemeral=True)

    # ═══════════════════════════════════════════════════════════
    # ─── /topbadges
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="topbadges", description="🏅 Top 10 badges")
    async def top_badges(self, it: discord.Interaction):
        guild_data = ACHIEVEMENTS.get(it.guild.id, {})
        if not guild_data:
            return await it.response.send_message("❌ Ma kaynch data!", ephemeral=True)

        sorted_users = sorted(
            guild_data.items(),
            key=lambda x: len(x[1].get("unlocked", [])),
            reverse=True,
        )[:10]

        embed = discord.Embed(title="🏅 Top Badges", color=discord.Color.gold())
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, d) in enumerate(sorted_users):
            try:
                u = await self.bot.fetch_user(uid)
                name = u.name
            except Exception:
                name = f"User {uid}"
            prefix = medals[i] if i < 3 else f"`#{i+1}`"
            embed.add_field(
                name=f"{prefix} {name}",
                value=f"🏆 `{len(d.get('unlocked', []))}` badges",
                inline=False,
            )
        await it.response.send_message(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── PREFIX
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="profile")
    async def profile_prefix(self, ctx: commands.Context, member: discord.Member = None):
        """&profile [@user]"""
        member = member or ctx.author
        data = self._get(ctx.guild.id, member.id)
        eco = ECONOMY.get(ctx.guild.id, {}).get(member.id, {})
        lv = LEVELS.get(ctx.guild.id, {}).get(member.id, {})
        bir = BIR.get(ctx.guild.id, {}).get(member.id, {}).get("bir", 0)
        unlocked = data["unlocked"]

        embed = discord.Embed(title=f"🏆 {member.display_name}", color=discord.Color.gold())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="💰 Coins", value=f"`{(eco.get('balance',0)+eco.get('bank',0)):,}`", inline=True)
        embed.add_field(name="📊 Level", value=f"`{lv.get('level',0)}`", inline=True)
        embed.add_field(name="🔮 Bir", value=f"`{bir:,}`", inline=True)
        embed.add_field(
            name=f"🏆 Badges ({len(unlocked)}/{len(ACHIEVEMENTS_LIST)})",
            value=" ".join(ACHIEVEMENTS_LIST[a]["emoji"] for a in unlocked[-15:] if a in ACHIEVEMENTS_LIST) or "—",
            inline=False,
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Achievements(bot))