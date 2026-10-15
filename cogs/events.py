# cogs/events.py
import discord
from discord.ext import commands, tasks
from datetime import datetime
import random
from database import KVStore
from data_manager import ECONOMY, save_economy

EVENTS = KVStore("events", {"last": None, "active": None})

class Events(commands.Cog):
    """Random server events"""
    def __init__(self, bot):
        self.bot = bot
        self.event_loop.start()

    def cog_unload(self): self.event_loop.cancel()

    @tasks.loop(minutes=30)
    async def event_loop(self):
        try:
            for guild in self.bot.guilds:
                if random.random() < 0.15:
                    await self._trigger(guild)
        except Exception as e:
            print(f"❌ Event loop: {e}")

    @event_loop.before_loop
    async def before(self): await self.bot.wait_until_ready()

    async def _trigger(self, guild):
        ch = discord.utils.get(guild.text_channels, name="event-chat") or guild.system_channel
        if not ch: return
        event_type = random.choice(["rain","hunt","bomb"])
        if event_type == "rain":
            embed = discord.Embed(title="💰 COIN RAIN!", description="Awal 5 users ykteb **claim** ghadi yjibou `5,000` 🪙!", color=discord.Color.gold())
            msg = await ch.send(embed=embed)
            def check(m): return m.channel.id == ch.id and m.content.lower() == "claim"
            winners = []
            for _ in range(5):
                try:
                    m = await self.bot.wait_for("message", timeout=60, check=check)
                    if m.author.id in winners: continue
                    winners.append(m.author.id)
                    eco = ECONOMY.setdefault(guild.id, {}).setdefault(m.author.id, {"balance":0,"bank":0,"inventory":[]})
                    eco["balance"] += 5000
                    save_economy()
                    await ch.send(f"💰 {m.author.mention} +`5,000` 🪙!")
                except: break
        elif event_type == "hunt":
            word = random.choice(["dragon","khokho","bot","pizza","moon"])
            embed = discord.Embed(title="🎯 WORD HUNT", description=f"Awal wa7ed ykteb **{word}** yjib `10,000` 🪙!", color=discord.Color.green())
            await ch.send(embed=embed)
            def check(m): return m.channel.id == ch.id and m.content.lower() == word.lower()
            try:
                m = await self.bot.wait_for("message", timeout=120, check=check)
                eco = ECONOMY.setdefault(guild.id, {}).setdefault(m.author.id, {"balance":0,"bank":0,"inventory":[]})
                eco["balance"] += 10000
                save_economy()
                await ch.send(f"🎉 {m.author.mention} rb7! +`10,000` 🪙")
            except: pass

    @commands.command(name="events")
    async def events_cmd(self, ctx):
        await ctx.send("🎉 Events kaynin auto kola 30min f **#event-chat**!")

async def setup(bot): await bot.add_cog(Events(bot))