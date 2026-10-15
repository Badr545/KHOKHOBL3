# cogs/counting.py
"""Counting game — count f channel, ila ghelt → reset"""
import discord
from discord.ext import commands
from datetime import datetime
from database import SqliteStore
from database.engine import execute, commit


def _ensure():
    execute("""CREATE TABLE IF NOT EXISTS counting (
        guild_id INTEGER PRIMARY KEY,
        channel_id INTEGER,
        current_number INTEGER DEFAULT 0,
        last_user_id INTEGER,
        high_score INTEGER DEFAULT 0,
        total_messages INTEGER DEFAULT 0)""")
    commit()


_ensure()
COUNTING = SqliteStore("counting_data")


class Counting(commands.Cog):
    """Counting game — setup + listener"""

    def __init__(self, bot):
        self.bot = bot

    def _get(self, gid):
        row = execute("SELECT * FROM counting WHERE guild_id=?", (gid,)).fetchone()
        if not row:
            return None
        return dict(row)

    def _setup(self, gid, channel_id):
        execute(
            "INSERT INTO counting (guild_id, channel_id, current_number, high_score) "
            "VALUES (?, ?, 0, 0) "
            "ON CONFLICT(guild_id) DO UPDATE SET channel_id=excluded.channel_id",
            (gid, channel_id),
        )
        commit()

    def _set_number(self, gid, num, uid):
        execute(
            "UPDATE counting SET current_number=?, last_user_id=?, "
            "total_messages=total_messages+1 WHERE guild_id=?",
            (num, uid, gid),
        )
        commit()

    def _reset(self, gid):
        row = self._get(gid)
        if row and row["current_number"] > row["high_score"]:
            execute(
                "UPDATE counting SET high_score=?, current_number=0, last_user_id=NULL WHERE guild_id=?",
                (row["current_number"], gid),
            )
        else:
            execute(
                "UPDATE counting SET current_number=0, last_user_id=NULL WHERE guild_id=?",
                (gid,),
            )
        commit()

    def _is_counting_channel(self, channel):
        row = self._get(channel.guild.id)
        return row and row["channel_id"] == channel.id

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot or not msg.guild:
            return
        if not self._is_counting_channel(msg.channel):
            return

        content = msg.content.strip()
        if not content.lstrip("-").isdigit():
            return

        row = self._get(msg.guild.id)
        expected = row["current_number"] + 1
        number = int(content)

        # Same user can't count twice
        if row["last_user_id"] == msg.author.id:
            try:
                await msg.add_reaction("❌")
            except Exception:
                pass
            self._reset(msg.guild.id)
            await msg.channel.send(
                f"🚫 {msg.author.mention} — **Machi turn dyalek!**\n"
                f"🔄 Count rje3 l **0**. Bda mn **1**."
            )
            return

        # Wrong number
        if number != expected:
            try:
                await msg.add_reaction("❌")
            except Exception:
                pass
            high = row["high_score"]
            current = row["current_number"]
            if current > high:
                high = current
            self._reset(msg.guild.id)
            await msg.channel.send(
                f"❌ {msg.author.mention} — **Ghelti!**\n"
                f"Kan khass **{expected}** (ktebti `{number}`)\n"
                f"🏆 High score: **{high}**\n"
                f"🔄 Bda mn **1**."
            )
            return

        # Correct!
        try:
            await msg.add_reaction("✅")
        except Exception:
            pass
        self._set_number(msg.guild.id, number, msg.author.id)

        # Milestone
        if number in (10, 25, 50, 100, 250, 500, 1000):
            await msg.channel.send(f"🎉 **Milestone!** Wselna **{number}**! 🔥")

    # ═══════════════════════════════════════════════════════════
    # ─── +counting setup
    # ═══════════════════════════════════════════════════════════
    @commands.group(name="counting", aliases=["count"], invoke_without_command=True)
    async def counting_group(self, ctx):
        """+counting — Info"""
        row = self._get(ctx.guild.id)
        if not row:
            return await ctx.send(
                "❌ **Counting machi setup!**\n"
                "Admin: `+counting setup #channel`"
            )
        ch = ctx.guild.get_channel(row["channel_id"])
        embed = discord.Embed(title="🔢 Counting Game", color=discord.Color.blue())
        embed.add_field(name="📍 Channel", value=ch.mention if ch else "❌", inline=True)
        embed.add_field(name="🔢 Current", value=f"`{row['current_number']}`", inline=True)
        embed.add_field(name="🏆 High Score", value=f"`{row['high_score']}`", inline=True)
        embed.add_field(name="💬 Total Counts", value=f"`{row['total_messages']:,}`", inline=True)
        await ctx.send(embed=embed)

    @counting_group.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def counting_setup(self, ctx, channel: discord.TextChannel):
        """+counting setup #channel"""
        self._setup(ctx.guild.id, channel.id)
        await ctx.send(
            f"✅ **Counting setup!** Channel: {channel.mention}\n"
            f"💡 Bda b **1** f had channel."
        )

    @counting_group.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def counting_reset(self, ctx):
        """+counting reset"""
        self._reset(ctx.guild.id)
        await ctx.send("🔄 Count rje3 l **0**!")