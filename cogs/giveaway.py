# cogs/giveaway.py
# =====================================================================
# ─── GIVEAWAY — Reaction-based b auto-end
# =====================================================================
import discord
from discord.ext import commands, tasks
import json
import os
import random
import asyncio
from datetime import datetime, timedelta

DATA_FILE = "data/giveaways.json"


def _load():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {int(g): {int(m): v for m, v in d.items()} for g, d in raw.items()}
    except Exception:
        return {}


def _save(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


GIVEAWAYS = _load()


class Giveaway(commands.Cog):
    """Giveaway system"""

    def __init__(self, bot):
        self.bot = bot
        self.checker.start()

    def cog_unload(self):
        self.checker.cancel()

    async def start_giveaway(self, channel: discord.TextChannel, prize: str,
                             duration_s: int, winners: int, host: discord.Member):
        until = datetime.now() + timedelta(seconds=duration_s)
        embed = discord.Embed(
            title="🎁 GIVEAWAY",
            description=(
                f"**Prize:** {prize}\n"
                f"**Winners:** `{winners}`\n"
                f"**Ends:** <t:{int(until.timestamp())}:R>\n\n"
                f"React b 🎉 bash tparticipi!"
            ),
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text=f"Hosted by {host.name}")
        msg = await channel.send(embed=embed)
        await msg.add_reaction("🎉")

        GIVEAWAYS.setdefault(channel.guild.id, {})[msg.id] = {
            "channel_id": channel.id,
            "prize": prize,
            "winners": winners,
            "host_id": host.id,
            "until": until.isoformat(),
            "ended": False,
        }
        _save()
        return msg

    @tasks.loop(seconds=30)
    async def checker(self):
        now = datetime.now()
        for gid in list(GIVEAWAYS.keys()):
            guild = self.bot.get_guild(gid)
            if not guild:
                continue
            for mid in list(GIVEAWAYS[gid].keys()):
                g = GIVEAWAYS[gid][mid]
                if g["ended"]:
                    continue
                try:
                    until = datetime.fromisoformat(g["until"])
                except Exception:
                    continue
                if until <= now:
                    await self._end_giveaway(guild, mid)

    @checker.before_loop
    async def before(self):
        await self.bot.wait_until_ready()

    async def _end_giveaway(self, guild: discord.Guild, message_id: int):
        g = GIVEAWAYS[guild.id][message_id]
        channel = guild.get_channel(g["channel_id"])
        if not channel:
            g["ended"] = True
            _save()
            return
        try:
            msg = await channel.fetch_message(message_id)
        except Exception:
            g["ended"] = True
            _save()
            return

        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        users = []
        if reaction:
            async for u in reaction.users():
                if not u.bot:
                    users.append(u)

        g["ended"] = True
        _save()

        if not users:
            embed = discord.Embed(
                title="🎁 Giveaway Ended",
                description=f"**Prize:** {g['prize']}\n❌ Ma kaynch winners.",
                color=discord.Color.red(),
            )
            try:
                await channel.send(embed=embed)
            except Exception:
                pass
            return

        winners_count = min(g["winners"], len(users))
        winners = random.sample(users, winners_count)
        mentions = ", ".join(w.mention for w in winners)
        embed = discord.Embed(
            title="🎁 Giveaway Ended",
            description=f"**Prize:** {g['prize']}\n**Winners:** {mentions}",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        try:
            await channel.send(content=mentions, embed=embed)
        except Exception:
            pass

    async def reroll(self, channel: discord.TextChannel, message_id: int):
        g = GIVEAWAYS.get(channel.guild.id, {}).get(message_id)
        if not g or not g.get("ended"):
            return None
        try:
            msg = await channel.fetch_message(message_id)
        except Exception:
            return None
        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        users = []
        if reaction:
            async for u in reaction.users():
                if not u.bot:
                    users.append(u)
        if not users:
            return None
        return random.choice(users)


async def setup(bot):
    await bot.add_cog(Giveaway(bot))