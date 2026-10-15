# cogs/stats.py
# =====================================================================
# ─── STATS — Voice Channel Updates (kola 1h + live)
# =====================================================================
import discord
from discord.ext import commands, tasks
import asyncio


STATS_CONFIG = [
    {"name": "👥 Members: {count}", "type": "members"},
    {"name": "🟢 Online: {count}",  "type": "online"},
    {"name": "🤖 Bots: {count}",     "type": "bots"},
    {"name": "📢 Channels: {count}", "type": "channels"},
    {"name": "🎭 Roles: {count}",    "type": "roles"},
]


class Stats(commands.Cog):
    """Stats f voice channels + update kola 1h"""

    def __init__(self, bot):
        self.bot = bot
        self.channel_ids = {}
        self.update_loop.start()

    def cog_unload(self):
        self.update_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        await self._setup_all_guilds()
        await self._update_all_stats()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self._setup_guild(guild)
        await self._update_all_stats()

    async def _setup_all_guilds(self):
        for guild in self.bot.guilds:
            await self._setup_guild(guild)

    async def _setup_guild(self, guild):
        self.channel_ids.setdefault(guild.id, {})

        category = discord.utils.get(guild.categories, name="📊 STATS")
        if category is None:
            try:
                category = await guild.create_category("📊 STATS")
                print(f"✅ Category '📊 STATS' tsayeb f {guild.name}")
            except discord.Forbidden:
                print(f"❌ Ma qdertch nsayeb category f {guild.name}")
                return

        for cfg in STATS_CONFIG:
            stat_type = cfg["type"]
            base_name = cfg["name"].split(":")[0].strip()
            existing = None
            for ch in category.voice_channels:
                if ch.name.startswith(base_name):
                    existing = ch
                    break

            if existing:
                self.channel_ids[guild.id][stat_type] = existing.id
            else:
                try:
                    new_ch = await guild.create_voice_channel(
                        name=cfg["name"].format(count="0"),
                        category=category,
                        reason="Stats channel auto-created",
                    )
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(connect=False),
                    }
                    await new_ch.edit(overwrites=overwrites)
                    self.channel_ids[guild.id][stat_type] = new_ch.id
                    print(f"✅ Channel '{new_ch.name}' tsayeb f {guild.name}")
                except discord.Forbidden:
                    print(f"❌ Ma qdertch nsayeb channel f {guild.name}")

    @tasks.loop(hours=1)
    async def update_loop(self):
        await self._update_all_stats()

    @update_loop.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

    async def _update_all_stats(self):
        for guild in self.bot.guilds:
            stats = self._get_stats(guild)
            guild_channels = self.channel_ids.get(guild.id, {})

            for cfg in STATS_CONFIG:
                stat_type = cfg["type"]
                ch_id = guild_channels.get(stat_type)
                if not ch_id:
                    continue
                channel = guild.get_channel(ch_id)
                if channel is None:
                    continue

                new_name = cfg["name"].format(count=stats[stat_type])
                if channel.name != new_name:
                    try:
                        await channel.edit(name=new_name, reason="Stats update")
                    except (discord.Forbidden, discord.HTTPException):
                        pass

    # ─── TRIGGERS
    @commands.Cog.listener()
    async def on_member_join(self, member):
        await asyncio.sleep(2)
        await self._update_all_stats()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await asyncio.sleep(2)
        await self._update_all_stats()

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if before.status != after.status:
            await self._update_all_stats()

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self._update_all_stats()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self._update_all_stats()

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self._update_all_stats()

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self._update_all_stats()

    def _get_stats(self, guild) -> dict:
        online = sum(1 for m in guild.members if m.status != discord.Status.offline)
        bots = sum(1 for m in guild.members if m.bot)
        return {
            "members": guild.member_count,
            "online": online,
            "bots": bots,
            "channels": len(guild.channels),
            "roles": len(guild.roles),
        }


async def setup(bot):
    await bot.add_cog(Stats(bot))