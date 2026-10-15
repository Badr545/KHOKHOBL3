# cogs/auto_responses.py
# =====================================================================
# ─── AUTO RESPONSES — Trigger b kelma (bla prefix) → sift message/image
# =====================================================================
import discord
from discord.ext import commands
import json
import os
import re

DATA_FILE = "data/auto_responses.json"

IMAGE_URL_RE = re.compile(
    r"^https?://\S+\.(?:png|jpg|jpeg|gif|webp|bmp)(?:\?\S*)?$",
    re.IGNORECASE,
)


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


AUTO = _load()


class AutoResponses(commands.Cog):
    """Auto responses: kelma wahda → reply b message/image"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        content = message.content.strip()
        if not content:
            return

        guild_id = message.guild.id
        rules = AUTO.get(guild_id, {})
        if not rules:
            return

        low = content.lower()

        for trigger, data in rules.items():
            matched = False
            if data.get("exact"):
                matched = low == trigger.lower()
            else:
                matched = re.search(
                    rf"(?<!\w){re.escape(trigger.lower())}(?!\w)", low
                ) is not None

            if not matched:
                continue

            allowed_channels = data.get("channels") or []
            if allowed_channels and message.channel.id not in allowed_channels:
                continue

            try:
                image = data.get("image")
                raw = data.get("content", "") or ""
                title = data.get("title") or None
                has_embed = bool(data.get("embed") or title or image)

                if has_embed:
                    color_hex = str(data.get("color", "5865F2")).replace("#", "")
                    try:
                        color = discord.Color(int(color_hex, 16))
                    except Exception:
                        color = discord.Color.blurple()

                    desc = raw if raw and raw != image else None
                    e = discord.Embed(title=title, description=desc, color=color)
                    if image:
                        e.set_image(url=image)
                    await message.channel.send(embed=e)
                else:
                    if raw:
                        await message.channel.send(raw)
            except discord.Forbidden:
                pass
            except Exception as ex:
                print(f"❌ Auto-response error [{trigger}]: {ex}")
            return

    # ═══════════════════════════════════════════════════════════
    # ─── API (l panel)
    # ═══════════════════════════════════════════════════════════
    def add(self, guild_id: int, trigger: str, data: dict) -> bool:
        trigger = trigger.strip().lower()
        if not trigger or " " in trigger:
            return False
        AUTO.setdefault(guild_id, {})[trigger] = data
        _save(AUTO)
        return True

    def remove(self, guild_id: int, trigger: str) -> bool:
        trigger = trigger.strip().lower()
        if guild_id in AUTO and trigger in AUTO[guild_id]:
            AUTO[guild_id].pop(trigger)
            if not AUTO[guild_id]:
                AUTO.pop(guild_id)
            _save(AUTO)
            return True
        return False

    def clear(self, guild_id: int) -> int:
        if guild_id not in AUTO:
            return 0
        n = len(AUTO[guild_id])
        AUTO.pop(guild_id, None)
        _save(AUTO)
        return n

    def list_all(self, guild_id: int) -> dict:
        return AUTO.get(guild_id, {})

    def get(self, guild_id: int, trigger: str):
        return AUTO.get(guild_id, {}).get(trigger.strip().lower())


async def setup(bot):
    await bot.add_cog(AutoResponses(bot))