# cogs/automod.py
# =====================================================================
# ─── AUTO-MOD — Anti-spam / Link / Invite / Caps / Bad-words
# =====================================================================
import discord
from discord.ext import commands
import json
import os
import re
import time
from collections import defaultdict, deque

DATA_FILE = "data/automod.json"


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


AUTOMOD = _load()


def _default_config():
    return {
        "enabled": True,
        "anti_spam": True,
        "spam_threshold": 5,          # 5 msgs
        "spam_window": 5,             # f 5 seconds
        "anti_link": False,
        "anti_invite": True,
        "anti_caps": False,
        "caps_threshold": 70,         # 70% caps
        "bad_words": [],
        "whitelist_channels": [],
        "whitelist_roles": [],
        "log_channel": None,
        "timeout_seconds": 300,
    }


def get_config(guild_id: int) -> dict:
    if guild_id not in AUTOMOD:
        AUTOMOD[guild_id] = _default_config()
        _save(AUTOMOD)
    return AUTOMOD[guild_id]


INVITE_RE = re.compile(r"(discord\.gg/|discord\.com/invite/|discordapp\.com/invite/)", re.I)
URL_RE = re.compile(r"https?://\S+", re.I)


class AutoMod(commands.Cog):
    """Auto-Mod système"""

    def __init__(self, bot):
        self.bot = bot
        self._user_msgs = defaultdict(lambda: deque(maxlen=20))

    def _is_whitelisted(self, message: discord.Message, cfg: dict) -> bool:
        if message.channel.id in cfg["whitelist_channels"]:
            return True
        if message.author.id == message.guild.owner_id:
            return True
        names = {r.name for r in message.author.roles}
        for r in cfg["whitelist_roles"]:
            if r in names:
                return True
        # Admin bypass
        for r in names:
            if r in ("⚜️ Community Manager", "🛡️ Administrator", "🐦‍🔥 𝓕𝓸𝓾𝓷𝓭𝓮𝓻"):
                return True
        return False

    async def _punish(self, message: discord.Message, reason: str, cfg: dict):
        try:
            await message.delete()
        except Exception:
            pass
        try:
            until = discord.utils.utcnow() + discord.timedelta(seconds=cfg["timeout_seconds"])
            await message.author.timeout(until, reason=f"AutoMod: {reason}")
        except Exception:
            pass

        log_id = cfg.get("log_channel")
        if log_id:
            ch = message.guild.get_channel(log_id)
            if ch:
                embed = discord.Embed(
                    title="🛡️ AutoMod Action",
                    description=f"{message.author.mention} → `{reason}`",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow(),
                )
                embed.add_field(name="Channel", value=message.channel.mention, inline=True)
                embed.add_field(name="Content", value=(message.content[:300] or "*empty*"), inline=False)
                try:
                    await ch.send(embed=embed)
                except Exception:
                    pass

        # DM
        try:
            await message.author.send(f"🛡️ **AutoMod** f **{message.guild.name}**\nReason: `{reason}`")
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        cfg = get_config(message.guild.id)
        if not cfg["enabled"]:
            return
        if self._is_whitelisted(message, cfg):
            return

        content = message.content or ""

        # ─── Anti-Spam
        if cfg["anti_spam"] and content:
            now = time.time()
            dq = self._user_msgs[message.author.id]
            dq.append(now)
            recent = [t for t in dq if now - t <= cfg["spam_window"]]
            if len(recent) >= cfg["spam_threshold"]:
                dq.clear()
                return await self._punish(message, "Spam", cfg)

        # ─── Anti-Invite
        if cfg["anti_invite"] and INVITE_RE.search(content):
            return await self._punish(message, "Discord invite", cfg)

        # ─── Anti-Link
        if cfg["anti_link"] and URL_RE.search(content):
            return await self._punish(message, "Link", cfg)

        # ─── Anti-Caps
        if cfg["anti_caps"] and len(content) >= 10:
            letters = [c for c in content if c.isalpha()]
            if letters:
                caps = sum(1 for c in letters if c.isupper())
                if (caps / len(letters)) * 100 >= cfg["caps_threshold"]:
                    return await self._punish(message, "CAPS", cfg)

        # ─── Bad words
        low = content.lower()
        for word in cfg["bad_words"]:
            if word and word.lower() in low:
                return await self._punish(message, f"Bad word: {word}", cfg)


async def setup(bot):
    await bot.add_cog(AutoMod(bot))