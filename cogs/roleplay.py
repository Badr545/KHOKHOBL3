# cogs/roleplay.py
"""Roleplay commands — hug, kiss, slap, pat, cuddle, bite, poke, dance"""
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import random


# (cmd_name, emoji, verb, target_verb, self_verb)
ACTIONS = {
    "hug":    ("🤗", "hugs",       "ng a hug"),
    "kiss":   ("💋", "kisses",     "a kiss"),
    "slap":   ("👋", "slaps",      "a slap"),
    "pat":    ("👐", "pats",       "head pats"),
    "cuddle": ("🫂", "cuddles",    "cuddles"),
    "bite":   ("🦷", "bites",      "a bite"),
    "poke":   ("👉", "pokes",      "a poke"),
    "dance":  ("💃", "dances with", "a dance"),
    "cry":    ("😢", "cries on",   "shoulder"),
    "blush":  ("😳", "blushes at", "shy"),
    "wave":   ("👋", "waves at",   "a wave"),
    "wink":   ("😉", "winks at",   "a wink"),
    "lick":   ("👅", "licks",      "a lick"),
    "tickle": ("🤣", "tickles",    "a tickle"),
    "feed":   ("🍰", "feeds",      "food"),
    "highfive": ("🙌", "high-fives", "high five"),
    "hold":   ("🤝", "holds",      "hand"),
    "stare":  ("👁️", "stares at",  "stare"),
    "smack":  ("🍑", "smacks",     "a smack"),
    "bonk":   ("🔨", "bonks",      "a bonk"),
}

# Anime API (free, no key)
API_ENDPOINTS = {
    "hug":    "https://api.waifu.pics/sfw/hug",
    "kiss":   "https://api.waifu.pics/sfw/kiss",
    "slap":   "https://api.waifu.pics/sfw/slap",
    "pat":    "https://api.waifu.pics/sfw/pat",
    "cuddle": "https://api.waifu.pics/sfw/cuddle",
    "bite":   "https://api.waifu.pics/sfw/bite",
    "poke":   "https://api.waifu.pics/sfw/poke",
    "dance":  "https://api.waifu.pics/sfw/dance",
    "cry":    "https://api.waifu.pics/sfw/cry",
    "blush":  "https://api.waifu.pics/sfw/blush",
    "wave":   "https://api.waifu.pics/sfw/wave",
    "wink":   "https://api.waifu.pics/sfw/wink",
    "lick":   "https://api.waifu.pics/sfw/lick",
    "tickle": "https://api.waifu.pics/sfw/tickle",
    "feed":   "https://api.waifu.pics/sfw/feed",
    "highfive": "https://api.waifu.pics/sfw/highfive",
    "hold":   "https://api.waifu.pics/sfw/handhold",
    "stare":  "https://api.waifu.pics/sfw/stare",
    "smack":  "https://api.waifu.pics/sfw/smack",
    "bonk":   "https://api.waifu.pics/sfw/bonk",
}


async def _fetch_gif(action: str) -> str | None:
    url = API_ENDPOINTS.get(action)
    if not url:
        return None
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status != 200:
                    return None
                data = await r.json()
                return data.get("url")
    except Exception:
        return None


def _rp_embed(action: str, gif: str, author: discord.Member,
              target: discord.Member, self_target: bool) -> discord.Embed:
    emoji, verb, thing = ACTIONS[action]

    if self_target:
        desc = f"{author.mention} {verb} rasso {emoji}"
    else:
        desc = f"{author.mention} {verb} {target.mention} {emoji}"

    embed = discord.Embed(description=desc, color=discord.Color.pink())
    if gif:
        embed.set_image(url=gif)
    return embed


class Roleplay(commands.Cog):
    """Roleplay: hug, kiss, slap, pat + more"""

    def __init__(self, bot):
        self.bot = bot

    # ─── Dynamic command builder
    async def _do_action(self, ctx_or_it, action: str, target: discord.Member = None):
        emoji, verb, thing = ACTIONS[action]
        is_slash = hasattr(ctx_or_it, "response")
        author = ctx_or_it.user if is_slash else ctx_or_it.author
        guild = ctx_or_it.guild

        # Self target check
        self_target = (target is None) or (target.id == author.id)
        if target is None:
            target = author

        # No bots
        if target.bot and not self_target:
            msg = "❌ Ma tqderch t-roleplay m3a bot!"
            return await (ctx_or_it.response.send_message(msg, ephemeral=True)
                          if is_slash else ctx_or_it.send(msg))

        gif = await _fetch_gif(action)
        embed = _rp_embed(action, gif, author, target, self_target)

        if is_slash:
            await ctx_or_it.response.send_message(embed=embed)
        else:
            await ctx_or_it.send(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── Slash commands
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="hug", description="🤗 Hug chi wa7ed")
    async def hug(self, it: discord.Interaction, member: discord.Member = None):
        await self._do_action(it, "hug", member)

    @app_commands.command(name="kiss", description="💋 Kiss chi wa7ed")
    async def kiss(self, it: discord.Interaction, member: discord.Member = None):
        await self._do_action(it, "kiss", member)

    @app_commands.command(name="slap", description="👋 Slap chi wa7ed")
    async def slap(self, it: discord.Interaction, member: discord.Member = None):
        await self._do_action(it, "slap", member)

    @app_commands.command(name="pat", description="👐 Pat chi wa7ed")
    async def pat(self, it: discord.Interaction, member: discord.Member = None):
        await self._do_action(it, "pat", member)

    @app_commands.command(name="cuddle", description="🫂 Cuddle chi wa7ed")
    async def cuddle(self, it: discord.Interaction, member: discord.Member = None):
        await self._do_action(it, "cuddle", member)

    @app_commands.command(name="poke", description="👉 Poke chi wa7ed")
    async def poke(self, it: discord.Interaction, member: discord.Member = None):
        await self._do_action(it, "poke", member)

    @app_commands.command(name="bite", description="🦷 Bite chi wa7ed")
    async def bite(self, it: discord.Interaction, member: discord.Member = None):
        await self._do_action(it, "bite", member)

    @app_commands.command(name="dance", description="💃 Dance m3a chi wa7ed")
    async def dance(self, it: discord.Interaction, member: discord.Member = None):
        await self._do_action(it, "dance", member)

    @app_commands.command(name="tickle", description="🤣 Tickle chi wa7ed")
    async def tickle(self, it: discord.Interaction, member: discord.Member = None):
        await self._do_action(it, "tickle", member)

    # ═══════════════════════════════════════════════════════════
    # ─── Prefix commands
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="hug")
    async def hug_p(self, ctx, member: discord.Member = None):
        await self._do_action(ctx, "hug", member)

    @commands.command(name="kiss")
    async def kiss_p(self, ctx, member: discord.Member = None):
        await self._do_action(ctx, "kiss", member)

    @commands.command(name="slap")
    async def slap_p(self, ctx, member: discord.Member = None):
        await self._do_action(ctx, "slap", member)

    @commands.command(name="pat")
    async def pat_p(self, ctx, member: discord.Member = None):
        await self._do_action(ctx, "pat", member)

    @commands.command(name="cuddle")
    async def cuddle_p(self, ctx, member: discord.Member = None):
        await self._do_action(ctx, "cuddle", member)

    @commands.command(name="poke")
    async def poke_p(self, ctx, member: discord.Member = None):
        await self._do_action(ctx, "poke", member)

    @commands.command(name="bite")
    async def bite_p(self, ctx, member: discord.Member = None):
        await self._do_action(ctx, "bite", member)

    @commands.command(name="dance")
    async def dance_p(self, ctx, member: discord.Member = None):
        await self._do_action(ctx, "dance", member)

    @commands.command(name="tickle")
    async def tickle_p(self, ctx, member: discord.Member = None):
        await self._do_action(ctx, "tickle", member)

    @commands.command(name="blush")
    async def blush_p(self, ctx, member: discord.Member = None):
        await self._do_action(ctx, "blush", member)

    @commands.command(name="wave")
    async def wave_p(self, ctx, member: discord.Member = None):
        await self._do_action(ctx, "wave", member)

    @commands.command(name="wink")
    async def wink_p(self, ctx, member: discord.Member = None):
        await self._do_action(ctx, "wink", member)

    @commands.command(name="bonk")
    async def bonk_p(self, ctx, member: discord.Member = None):
        await self._do_action(ctx, "bonk", member)


async def setup(bot):
    await bot.add_cog(Roleplay(bot))