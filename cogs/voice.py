# cogs/voice.py
# =====================================================================
# ─── VOICE 24/7 — Bot kayb9a f channel dima
# =====================================================================
import discord
from discord.ext import commands, tasks
import asyncio
from botconfig import VOICE_CHANNEL_ID


class Voice247(commands.Cog):
    """Bot kayb9a f voice channel 24/7"""

    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.channel_id = VOICE_CHANNEL_ID
        self.fail_count = 0
        self.max_fails = 3

    @commands.Cog.listener()
    async def on_ready(self):
        print("🎙️ Voice247: Kanconnecti l voice...")
        await self._connect()
        if not self.voice_watcher.is_running() and self.fail_count < self.max_fails:
            self.voice_watcher.start()

    async def _connect(self):
        if self.fail_count >= self.max_fails:
            return

        channel = self.bot.get_channel(self.channel_id)
        if channel is None:
            print(f"❌ Voice channel {self.channel_id} ma kaynach!")
            return

        if channel.guild.voice_client and channel.guild.voice_client.is_connected():
            self.voice_client = channel.guild.voice_client
            self.fail_count = 0
            print(f"✅ Deja connecté f: {channel.name}")
            return

        try:
            self.voice_client = await channel.connect(self_deaf=True, timeout=20.0)
            self.fail_count = 0
            print(f"✅ Connecté l voice: {channel.name}")
        except discord.ClientException as e:
            self.fail_count += 1
            print(f"❌ Erreur connect: {e}")
        except asyncio.TimeoutError:
            self.fail_count += 1
            print(f"❌ Timeout: ma qdertch nconnecti l {channel.name}")
        except Exception as e:
            self.fail_count += 1
            print(f"❌ Erreur: {e}")

    @tasks.loop(seconds=5)
    async def voice_watcher(self):
        if self.fail_count >= self.max_fails:
            if self.voice_watcher.is_running():
                print(f"🛑 VoiceWatcher wqef ba3d {self.max_fails} failures.")
                self.voice_watcher.cancel()
            return

        channel = self.bot.get_channel(self.channel_id)
        if channel is None:
            return

        guild = channel.guild
        vc = guild.voice_client

        if vc is None or not vc.is_connected():
            print("🔄 Bot tqte3 mn voice, kanrje3...")
            await self._connect()
            return

        if vc.channel.id != self.channel_id:
            print(f"🔄 Bot f channel akhor, kanrje3 l {channel.name}...")
            try:
                await vc.move_to(channel)
            except Exception as e:
                print(f"❌ Erreur move: {e}")
            return

    @voice_watcher.before_loop
    async def before_watcher(self):
        await self.bot.wait_until_ready()

    @commands.command(name="join")
    @commands.has_permissions(administrator=True)
    async def join(self, ctx: commands.Context):
        """&join — Connect bot l voice"""
        channel = self.bot.get_channel(self.channel_id)
        if channel is None:
            return await ctx.send(f"❌ Voice channel `{self.channel_id}` ma kaynach!")

        if ctx.guild.voice_client:
            await ctx.guild.voice_client.move_to(channel)
        else:
            await channel.connect(self_deaf=True)
        await ctx.send(f"✅ Dkhelt l {channel.mention}!")

    @commands.command(name="leave")
    @commands.has_permissions(administrator=True)
    async def leave(self, ctx: commands.Context):
        """&leave — Kherrej bot mn voice"""
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()
            await ctx.send("👋 Khrjt mn voice!")
        else:
            await ctx.send("❌ Machi connecté f voice!")

    @commands.command(name="voice247")
    @commands.has_permissions(administrator=True)
    async def voice247(self, ctx: commands.Context):
        """&voice247 — Status dyal voice 24/7"""
        channel = self.bot.get_channel(self.channel_id)
        vc = ctx.guild.voice_client

        embed = discord.Embed(title="🎙️ Voice 24/7 Status", color=discord.Color.blue())
        embed.add_field(
            name="📌 Channel target",
            value=f"{channel.mention} (`{self.channel_id}`)" if channel else "❌ Ma kaynach",
            inline=False,
        )
        embed.add_field(
            name="🔌 Connexion",
            value=f"✅ Connecté f {vc.channel.mention}" if vc and vc.is_connected() else "❌ Machi connecté",
            inline=False,
        )
        embed.add_field(
            name="👂 Deafened",
            value=f"`{vc.is_deaf()}`" if vc else "N/A",
            inline=True,
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Voice247(bot))