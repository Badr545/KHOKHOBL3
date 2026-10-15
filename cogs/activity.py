# cogs/activity.py
"""Activity tracking — messages, voice time per user (kola week)"""
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from database import SqliteStore
from database.engine import execute, commit


def _ensure():
    execute("""CREATE TABLE IF NOT EXISTS activity (
        guild_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        data TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (guild_id, user_id))""")
    execute("CREATE INDEX IF NOT EXISTS idx_activity_guild ON activity(guild_id)")
    commit()


_ensure()
ACTIVITY = SqliteStore("activity")


class Activity(commands.Cog):
    """Track user activity (messages + voice time)"""

    def __init__(self, bot):
        self.bot = bot
        self._voice_joins = {}  # {guild_id: {user_id: join_time}}
        self.cleanup.start()

    def cog_unload(self):
        self.cleanup.cancel()

    def _get(self, gid, uid):
        ACTIVITY.setdefault(gid, {}).setdefault(uid, {
            "messages": 0, "voice_seconds": 0,
            "week_messages": 0, "week_voice_seconds": 0,
            "total_messages": 0, "total_voice_seconds": 0,
            "week_start": datetime.now().isoformat(),
        })
        return ACTIVITY[gid][uid]

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot or not msg.guild:
            return
        if len(msg.content) < 2:
            return
        d = self._get(msg.guild.id, msg.author.id)
        d["messages"] += 1
        d["week_messages"] += 1
        d["total_messages"] += 1
        ACTIVITY.mark_dirty(msg.guild.id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        gid, uid = member.guild.id, member.id

        # Join
        if before.channel is None and after.channel is not None:
            self._voice_joins.setdefault(gid, {})[uid] = datetime.now()
            return

        # Leave
        if before.channel is not None and after.channel is None:
            joins = self._voice_joins.get(gid, {})
            if uid in joins:
                delta = (datetime.now() - joins.pop(uid)).total_seconds()
                if delta > 30:  # skip very short
                    d = self._get(gid, uid)
                    d["voice_seconds"] += int(delta)
                    d["week_voice_seconds"] += int(delta)
                    d["total_voice_seconds"] += int(delta)
                    ACTIVITY.mark_dirty(gid)
            return

        # Move (machi join/leave)
        if before.channel != after.channel:
            # Leave old
            joins = self._voice_joins.get(gid, {})
            if uid in joins:
                delta = (datetime.now() - joins.pop(uid)).total_seconds()
                if delta > 30:
                    d = self._get(gid, uid)
                    d["voice_seconds"] += int(delta)
                    d["week_voice_seconds"] += int(delta)
                    d["total_voice_seconds"] += int(delta)
                    ACTIVITY.mark_dirty(gid)
            # Join new
            if after.channel is not None:
                joins[uid] = datetime.now()

    @tasks.loop(hours=24)
    async def cleanup(self):
        """Reset weekly stats kola week (Monday)."""
        now = datetime.now()
        if now.weekday() != 0:  # ghir Monday
            return
        try:
            ACTIVITY.bulk_load_all()
            for gid, users in ACTIVITY.items():
                for uid, d in users.items():
                    last = d.get("week_start")
                    if not last:
                        continue
                    try:
                        last_dt = datetime.fromisoformat(last)
                    except Exception:
                        continue
                    if (now - last_dt).days >= 7:
                        d["week_messages"] = 0
                        d["week_voice_seconds"] = 0
                        d["week_start"] = now.isoformat()
                        ACTIVITY.mark_dirty(gid)
        except Exception as e:
            print(f"❌ Activity cleanup: {e}")

    @cleanup.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    # ═══════════════════════════════════════════════════════════
    # ─── +activity @user
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="activity", aliases=["stats_user"])
    async def activity(self, ctx, member: discord.Member = None):
        """+activity [@user] — Chouf activity dyal user"""
        member = member or ctx.author
        d = self._get(ctx.guild.id, member.id)

        def fmt_time(secs):
            h = secs // 3600
            m = (secs % 3600) // 60
            if h > 0:
                return f"{h}h {m}m"
            return f"{m}m"

        embed = discord.Embed(
            title=f"📊 Activity — {member.display_name}",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="📅 This Week",
                        value=f"💬 `{d['week_messages']:,}` msgs\n"
                              f"🔊 `{fmt_time(d['week_voice_seconds'])}`",
                        inline=True)
        embed.add_field(name="📈 All-time",
                        value=f"💬 `{d['total_messages']:,}` msgs\n"
                              f"🔊 `{fmt_time(d['total_voice_seconds'])}`",
                        inline=True)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── +activity_top (messages + voice)
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="activity_top", aliases=["atop", "topactive"])
    async def activity_top(self, ctx, mode: str = "messages"):
        """+activity_top [messages|voice|week_messages|week_voice]"""
        ACTIVITY.bulk_load_all()
        gd = ACTIVITY.get(ctx.guild.id, {})
        if not gd:
            return await ctx.send("❌ Ma kaynch data!")

        sort_key = {
            "messages": "total_messages",
            "voice": "total_voice_seconds",
            "week_messages": "week_messages",
            "week_voice": "week_voice_seconds",
        }.get(mode, "total_messages")

        top = sorted(gd.items(), key=lambda x: x[1].get(sort_key, 0), reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (uid, d) in enumerate(top):
            try:
                u = await self.bot.fetch_user(uid)
                name = u.name
            except Exception:
                name = f"User {uid}"

            val = d.get(sort_key, 0)
            if "voice" in sort_key:
                h = val // 3600
                m = (val % 3600) // 60
                val_str = f"{h}h {m}m"
            else:
                val_str = f"{val:,}"

            prefix = medals[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{prefix} **{name}** — `{val_str}`")

        await ctx.send(f"📊 **Top 10 — {mode}**\n" + "\n".join(lines))


async def setup(bot):
    await bot.add_cog(Activity(bot))