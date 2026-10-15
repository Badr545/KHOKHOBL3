# cogs/customcommands.py
# =====================================================================
# ─── CUSTOM COMMANDS — Admin ykriy commands bla code (FIXED + Image)
# =====================================================================
import discord
from discord.ext import commands
import json
import os
import re

DATA_FILE = "data/customcommands.json"

# ─── Regex bash n3erfo wach URL dyal image
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


CUSTOM = _load()


class CustomCommands(commands.Cog):
    """Custom commands — kaykhdem b on_message listener"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # ─── Jbed prefix
        try:
            prefixes = await self.bot.get_prefix(message)
        except Exception:
            return
        if isinstance(prefixes, str):
            prefixes = [prefixes]

        matched_prefix = None
        for p in prefixes:
            if isinstance(p, str) and p and message.content.startswith(p):
                matched_prefix = p
                break
        if matched_prefix is None:
            return

        # ─── Jbed command name
        content = message.content[len(matched_prefix):].strip()
        if not content:
            return
        cmd_name = content.split(maxsplit=1)[0].lower()

        # ─── Check custom commands
        guild_id = message.guild.id
        cmds = CUSTOM.get(guild_id, {})
        if cmd_name not in cmds:
            return

        # ─── Real command 3endou priority
        if self.bot.get_command(cmd_name):
            return

        # ─── Send response
        data = cmds[cmd_name]
        try:
            # Jbed l-image: mn data["image"] wla mn content ila kan URL dyal image
            image_url = data.get("image")
            raw_content = data.get("content", "") or ""

            # Auto-detect: ila content rah URL dyal image bo7do
            if not image_url and IMAGE_URL_RE.match(raw_content.strip()):
                image_url = raw_content.strip()

            has_embed = bool(data.get("title") or image_url or data.get("embed"))

            if has_embed:
                color_hex = str(data.get("color", "5865F2")).replace("#", "")
                try:
                    color = discord.Color(int(color_hex, 16))
                except Exception:
                    color = discord.Color.blurple()

                e = discord.Embed(
                    title=data.get("title") or None,
                    description=raw_content if raw_content != image_url else None,
                    color=color,
                )
                if image_url:
                    e.set_image(url=image_url)

                await message.channel.send(embed=e)
            else:
                await message.channel.send(raw_content)
        except discord.Forbidden:
            pass
        except Exception as ex:
            print(f"❌ Custom cmd error [{cmd_name}]: {ex}")

    # ═══════════════════════════════════════════════════════════
    # ─── API
    # ═══════════════════════════════════════════════════════════
    def add_command(self, guild_id: int, name: str, data: dict) -> bool:
        name = name.strip().lower()
        if not name or " " in name:
            return False
        CUSTOM.setdefault(guild_id, {})[name] = data
        _save(CUSTOM)
        return True

    def remove_command(self, guild_id: int, name: str) -> bool:
        name = name.strip().lower()
        if guild_id in CUSTOM and name in CUSTOM[guild_id]:
            CUSTOM[guild_id].pop(name)
            if not CUSTOM[guild_id]:
                CUSTOM.pop(guild_id)
            _save(CUSTOM)
            return True
        return False

    def list_commands(self, guild_id: int) -> dict:
        return CUSTOM.get(guild_id, {})


async def setup(bot):
    await bot.add_cog(CustomCommands(bot))