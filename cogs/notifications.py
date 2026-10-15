# cogs/notifications.py
# =====================================================================
# ─── NOTIFICATIONS — Twitch / YouTube / RSS feeds
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import aiohttp
import feedparser
from datetime import datetime

DATA_FILE = "data/notifications.json"


def _load():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {int(g): v for g, v in raw.items()}
    except Exception:
        return {}


def _save(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


NOTIF = _load()


class Notifications(commands.Cog):
    """Twitch + YouTube + RSS notifications"""

    def __init__(self, bot):
        self.bot = bot
        self.checker.start()

    def cog_unload(self):
        self.checker.cancel()

    @tasks.loop(minutes=5)
    async def checker(self):
        try:
            for gid, data in list(NOTIF.items()):
                guild = self.bot.get_guild(gid)
                if not guild:
                    continue

                # ─── RSS
                for feed in list(data.get("rss", [])):
                    try:
                        await self._check_rss(guild, feed)
                    except Exception as e:
                        print(f"❌ RSS {feed.get('url')}: {e}")

                # ─── Twitch
                for streamer in list(data.get("twitch", [])):
                    try:
                        await self._check_twitch(guild, streamer)
                    except Exception as e:
                        print(f"❌ Twitch {streamer.get('user')}: {e}")
        except Exception as e:
            print(f"❌ Notif checker: {e}")

    @checker.before_loop
    async def before(self):
        await self.bot.wait_until_ready()

    async def _check_rss(self, guild, feed):
        url = feed["url"]
        ch = guild.get_channel(feed["channel_id"])
        if not ch:
            return

        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    content = await r.text()
            parsed = feedparser.parse(content)
        except Exception:
            return

        if not parsed.entries:
            return

        latest = parsed.entries[0]
        link = latest.get("link", "")
        if feed.get("last_link") == link:
            return

        feed["last_link"] = link
        _save(NOTIF)

        title = latest.get("title", "No title")
        published = latest.get("published", "")
        embed = discord.Embed(
            title=f"📰 {title}",
            url=link,
            description=(latest.get("summary", "") or "")[:300],
            color=discord.Color.orange(),
            timestamp=datetime.now(),
        )
        embed.set_footer(text=f"RSS • {feed.get('name', 'feed')}")
        try:
            await ch.send(embed=embed)
        except Exception:
            pass

    async def _check_twitch(self, guild, streamer):
        # Simplified: needs Twitch API key. Skip ila makaynch.
        return

    # ═══════════════════════════════════════════════════════════
    # ─── /notify
    # ═══════════════════════════════════════════════════════════
    notify_group = app_commands.Group(name="notify", description="🔔 Notifications manager")

    @notify_group.command(name="rss", description="📰 Zid RSS feed")
    @app_commands.describe(url="RSS URL", name="Smiya (optionnel)", channel="Channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def notify_rss(
        self,
        it: discord.Interaction,
        url: str,
        name: str = None,
        channel: discord.TextChannel = None,
    ):
        ch = channel or it.channel
        g = NOTIF.setdefault(it.guild.id, {"rss": [], "twitch": [], "youtube": []})
        g.setdefault("rss", []).append({
            "url": url,
            "name": name or url,
            "channel_id": ch.id,
            "last_link": None,
        })
        _save(NOTIF)
        await it.response.send_message(f"✅ RSS added → {ch.mention}", ephemeral=True)

    @notify_group.command(name="twitch", description="🎮 Zid Twitch streamer")
    @app_commands.describe(user="Twitch username", channel="Channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def notify_twitch(self, it: discord.Interaction, user: str, channel: discord.TextChannel = None):
        ch = channel or it.channel
        g = NOTIF.setdefault(it.guild.id, {"rss": [], "twitch": [], "youtube": []})
        g.setdefault("twitch", []).append({"user": user, "channel_id": ch.id})
        _save(NOTIF)
        await it.response.send_message(
            f"✅ Twitch **{user}** added → {ch.mention}\n"
            f"⚠️ Needs Twitch API in .env",
            ephemeral=True,
        )

    @notify_group.command(name="list", description="📋 List notifications")
    async def notify_list(self, it: discord.Interaction):
        g = NOTIF.get(it.guild.id, {})
        embed = discord.Embed(title="🔔 Notifications", color=discord.Color.blurple())
        rss = g.get("rss", [])
        if rss:
            lines = [f"• **{x['name']}** → <#{x['channel_id']}>" for x in rss[:10]]
            embed.add_field(name=f"📰 RSS ({len(rss)})", value="\n".join(lines), inline=False)
        tw = g.get("twitch", [])
        if tw:
            lines = [f"• **{x['user']}** → <#{x['channel_id']}>" for x in tw[:10]]
            embed.add_field(name=f"🎮 Twitch ({len(tw)})", value="\n".join(lines), inline=False)
        if not rss and not tw:
            embed.description = "❌ Ma kaynch notifications!"
        await it.response.send_message(embed=embed, ephemeral=True)

    @notify_group.command(name="remove", description="🗑️ Hyed notification")
    @app_commands.describe(name="Smiya wla URL")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def notify_remove(self, it: discord.Interaction, name: str):
        g = NOTIF.get(it.guild.id, {})
        removed = False
        for key in ("rss", "twitch", "youtube"):
            for item in list(g.get(key, [])):
                if item.get("name") == name or item.get("url") == name or item.get("user") == name:
                    g[key].remove(item)
                    removed = True
        if removed:
            _save(NOTIF)
            await it.response.send_message(f"✅ Removed `{name}`!")
        else:
            await it.response.send_message("❌ Ma l9itch!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Notifications(bot))