# cogs/gamerequests.py
# =====================================================================
# ─── GAME REQUESTS — &ff / &pes / &valo / &roblox → ping game role
# =====================================================================
import discord
from discord.ext import commands
import json
import os


DATA_FILE = "data/gamerequests.json"

# Default games (admin y9der ybeddel label/emoji via +setgame)
DEFAULT_GAMES = {
    "ff":        {"label": "Free Fire",         "emoji": "🔫"},
    "pes":       {"label": "PES",               "emoji": "⚽"},
    "valo":      {"label": "Valorant",          "emoji": "🎯"},
    "roblox":    {"label": "Roblox",            "emoji": "🟥"},
    "pubg":      {"label": "PUBG",              "emoji": "🪖"},
    "cod":       {"label": "Call of Duty",      "emoji": "🎖️"},
    "fortnite":  {"label": "Fortnite",          "emoji": "🏗️"},
    "lol":       {"label": "League of Legends", "emoji": "⚔️"},
    "mc":        {"label": "Minecraft",         "emoji": "⛏️"},
    "fifa":      {"label": "FIFA",              "emoji": "🥅"},
    "gta":       {"label": "GTA V",             "emoji": "🚗"},
    "apex":      {"label": "Apex Legends",      "emoji": "🛡️"},
    "overwatch": {"label": "Overwatch",         "emoji": "🎮"},
}


def _load():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {int(g): v for g, v in raw.items()}
    except Exception:
        return {}


def _save():
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(GAMES, f, indent=2, ensure_ascii=False)


GAMES: dict = _load()
# {guild_id: {cmd: {"label": str, "emoji": str, "role_id": int}}}


class GameRequests(commands.Cog):
    """Game invites: &ff, &pes, &valo, &roblox... (mention game role)"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════════════════════════
    # ─── on_message listener — commandes dynamiques
    # ═══════════════════════════════════════════════════════════
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if not message.content.startswith("&"):
            return

        parts = message.content[1:].strip().split(maxsplit=1)
        if not parts:
            return
        cmd = parts[0].lower()

        # Ila kayn command real b nafs smiya → skip
        if self.bot.get_command(cmd):
            return

        guild_games = GAMES.get(message.guild.id, {})
        if cmd not in guild_games:
            return

        cfg = guild_games[cmd]
        if not cfg.get("role_id"):
            return

        role = message.guild.get_role(cfg["role_id"])
        if role is None:
            return

        # Check user 3endou role dyal game (avoid spam)
        if role not in message.author.roles and message.author.id != message.guild.owner_id:
            try:
                await message.channel.send(
                    f"❌ {message.author.mention} Khass ykoun 3endek {role.mention} bash tst3mel `&{cmd}`!",
                    delete_after=8,
                )
            except Exception:
                pass
            return

        label = cfg.get("label", cmd)
        emoji = cfg.get("emoji", "🎮")

        embed = discord.Embed(
            title=f"{emoji} {label}",
            description=f"<@{message.author.id}> invites you to play with him **{label}**",
            color=discord.Color.from_rgb(88, 101, 242),
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.set_footer(
            text=f"Requested by {message.author.name}",
            icon_url=message.author.display_avatar.url,
        )

        try:
            await message.delete()
        except Exception:
            pass

        await message.channel.send(
            content=role.mention,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True, everyone=False),
        )

    # ═══════════════════════════════════════════════════════════
    # ─── ADMIN CONFIG (+)
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="setgame")
    @commands.has_permissions(administrator=True)
    async def setgame(self, ctx, cmd: str, role: discord.Role, *, label: str = None):
        """+setgame <cmd> @role [label]  →  ex: +setgame ff @FreeFire"""
        cmd = cmd.lower().strip().lstrip("&+")
        if not cmd or " " in cmd:
            return await ctx.send("❌ Command name khass bla espaces!")

        default = DEFAULT_GAMES.get(cmd, {})
        label = label or default.get("label", cmd.upper())
        emoji = default.get("emoji", "🎮")

        GAMES.setdefault(ctx.guild.id, {})[cmd] = {
            "label": label,
            "emoji": emoji,
            "role_id": role.id,
        }
        _save()

        await ctx.send(
            f"✅ `&{cmd}` tsayeb!\n"
            f"**Label:** {emoji} {label}\n"
            f"**Role:** {role.mention}"
        )

    @commands.command(name="delgame")
    @commands.has_permissions(administrator=True)
    async def delgame(self, ctx, cmd: str):
        """+delgame <cmd>"""
        cmd = cmd.lower().strip().lstrip("&+")
        guild_games = GAMES.get(ctx.guild.id, {})
        if cmd not in guild_games:
            return await ctx.send(f"❌ `{cmd}` ma kaynch!")
        guild_games.pop(cmd)
        _save()
        await ctx.send(f"✅ `&{cmd}` thyed!")

    @commands.command(name="listgames")
    async def listgames(self, ctx):
        """+listgames — Chouf games configurés"""
        guild_games = GAMES.get(ctx.guild.id, {})
        if not guild_games:
            return await ctx.send(
                "📋 Ma kaynch games configurés!\n"
                "Admin: `+setgame ff @FreeFireRole`"
            )
        lines = []
        for cmd, cfg in guild_games.items():
            role = ctx.guild.get_role(cfg["role_id"])
            role_str = role.mention if role else f"`{cfg['role_id']}` (❌ ma kaynch)"
            lines.append(
                f"**`&{cmd}`** — {cfg.get('emoji', '🎮')} {cfg.get('label', cmd)} → {role_str}"
            )
        await ctx.send("📋 **Game Requests:**\n" + "\n".join(lines))


async def setup(bot):
    await bot.add_cog(GameRequests(bot))