# cogs/status_rotation.py
"""Rotating bot status (activity)"""
import discord
from discord.ext import commands, tasks
import itertools
import random


STATUSES = [
    # (type, text)
    ("playing", "🎰 with {guilds} servers"),
    ("watching", "👀 {members} users"),
    ("listening", "🎵 /help for commands"),
    ("playing", "💎 Khokho Bl3"),
    ("watching", "🔥 {guilds} servers"),
    ("playing", "🎲 /casino"),
    ("listening", "🌙 {members} members"),
    ("watching", "💬 Custom commands"),
    ("playing", "👑 Premium"),
    ("watching", "🛡️ Protecting {guilds} servers"),
]


class StatusRotation(commands.Cog):
    """Rotate bot status"""

    def __init__(self, bot):
        self.bot = bot
        self.iterator = itertools.cycle(STATUSES)
        self.rotate.start()

    def cog_unload(self):
        self.rotate.cancel()

    @tasks.loop(seconds=45)
    async def rotate(self):
        try:
            status_type, text = next(self.iterator)
            # Replace placeholders
            guilds = len(self.bot.guilds)
            members = sum(g.member_count or 0 for g in self.bot.guilds)
            text = text.format(guilds=guilds, members=members)

            activity = {
                "playing": discord.ActivityType.playing,
                "watching": discord.ActivityType.watching,
                "listening": discord.ActivityType.listening,
                "streaming": discord.ActivityType.streaming,
            }.get(status_type, discord.ActivityType.playing)

            await self.bot.change_presence(
                activity=discord.Activity(type=activity, name=text),
                status=discord.Status.online,
            )
        except Exception as e:
            print(f"❌ Status rotation: {e}")

    @rotate.before_loop
    async def before(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(StatusRotation(bot))