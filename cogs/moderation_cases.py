# cogs/moderation_cases.py
"""Moderation cases — track warn/kick/ban/mute/jail with IDs"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from database import SqliteStore
from database.engine import execute, commit


def _ensure():
    execute("""CREATE TABLE IF NOT EXISTS mod_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        mod_id INTEGER NOT NULL,
        case_type TEXT NOT NULL,
        reason TEXT,
        duration TEXT,
        active INTEGER DEFAULT 1,
        created TEXT NOT NULL,
        closed TEXT)""")
    execute("CREATE INDEX IF NOT EXISTS idx_cases_guild ON mod_cases(guild_id)")
    execute("CREATE INDEX IF NOT EXISTS idx_cases_user ON mod_cases(user_id)")
    commit()


_ensure()


class ModerationCases(commands.Cog):
    """Moderation cases system"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════════════════════════
    # ─── API (kayt3ayet mn admin.py)
    # ═══════════════════════════════════════════════════════════
    def create_case(self, guild_id: int, user_id: int, mod_id: int,
                    case_type: str, reason: str = "N/A",
                    duration: str = None) -> int:
        """Sayeb case jdid. Rje3 case ID."""
        cur = execute(
            "INSERT INTO mod_cases "
            "(guild_id, user_id, mod_id, case_type, reason, duration, active, created) "
            "VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
            (guild_id, user_id, mod_id, case_type, reason, duration,
             datetime.now().isoformat()),
        )
        commit()
        return cur.lastrowid

    def close_case(self, case_id: int):
        execute(
            "UPDATE mod_cases SET active=0, closed=? WHERE id=?",
            (datetime.now().isoformat(), case_id),
        )
        commit()

    def get_user_cases(self, guild_id: int, user_id: int, limit: int = 25):
        return execute(
            "SELECT * FROM mod_cases WHERE guild_id=? AND user_id=? "
            "ORDER BY id DESC LIMIT ?",
            (guild_id, user_id, limit),
        ).fetchall()

    # ═══════════════════════════════════════════════════════════
    # ─── +case view <id>
    # ═══════════════════════════════════════════════════════════
    @commands.group(name="case", aliases=["cases"], invoke_without_command=True)
    @commands.has_permissions(moderate_members=True)
    async def case_group(self, ctx: commands.Context, case_id: int = None):
        """+case <id> — Chouf case wa7ed"""
        if case_id is None:
            return await ctx.send(
                "**Usage:**\n"
                "`+case <id>` — Chouf case\n"
                "`+case user @user` — Cases dyal user\n"
                "`+case close <id>` — Close case\n"
                "`+case stats` — Stats"
            )
        row = execute(
            "SELECT * FROM mod_cases WHERE id=? AND guild_id=?",
            (case_id, ctx.guild.id),
        ).fetchone()
        if not row:
            return await ctx.send(f"❌ Case `#{case_id}` ma kaynch!")
        await ctx.send(embed=self._build_case_embed(ctx.guild, row))

    @case_group.command(name="user")
    @commands.has_permissions(moderate_members=True)
    async def case_user(self, ctx: commands.Context, member: discord.Member):
        """+case user @user — List cases"""
        rows = self.get_user_cases(ctx.guild.id, member.id, limit=15)
        if not rows:
            return await ctx.send(f"✅ {member.mention} 3endou 0 cases.")
        active = sum(1 for r in rows if r["active"])
        embed = discord.Embed(
            title=f"📋 Cases — {member.name}",
            description=f"**Total:** `{len(rows)}` • **Active:** `{active}`",
            color=discord.Color.orange(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        for r in rows[:10]:
            ts = int(datetime.fromisoformat(r["created"]).timestamp())
            mark = "🔴" if r["active"] else "⚪"
            embed.add_field(
                name=f"{mark} `#{r['id']}` — {r['case_type'].upper()}",
                value=f"**Reason:** {r['reason'][:80]}\n"
                      f"**By:** <@{r['mod_id']}> • <t:{ts}:R>",
                inline=False,
            )
        await ctx.send(embed=embed)

    @case_group.command(name="close")
    @commands.has_permissions(administrator=True)
    async def case_close(self, ctx: commands.Context, case_id: int):
        """+case close <id>"""
        row = execute(
            "SELECT * FROM mod_cases WHERE id=? AND guild_id=?",
            (case_id, ctx.guild.id),
        ).fetchone()
        if not row:
            return await ctx.send(f"❌ Case `#{case_id}` ma kaynch!")
        if not row["active"]:
            return await ctx.send(f"⚠️ Case `#{case_id}` deja closed!")
        self.close_case(case_id)
        await ctx.send(f"✅ Case `#{case_id}` closed!")

    @case_group.command(name="stats")
    @commands.has_permissions(moderate_members=True)
    async def case_stats(self, ctx: commands.Context):
        """+case stats — Stats dyal moderation"""
        rows = execute(
            "SELECT case_type, COUNT(*) as c FROM mod_cases "
            "WHERE guild_id=? GROUP BY case_type",
            (ctx.guild.id,),
        ).fetchall()
        if not rows:
            return await ctx.send("❌ Ma kaynch cases!")
        embed = discord.Embed(
            title="📊 Moderation Stats",
            color=discord.Color.red(),
        )
        total = 0
        for r in rows:
            emoji = {
                "warn": "⚠️", "kick": "👢", "ban": "🔨",
                "mute": "🔇", "timeout": "⏱️", "jail": "🔒",
                "unjail": "🔓", "unban": "✅", "unmute": "🔊",
            }.get(r["case_type"], "📝")
            embed.add_field(
                name=f"{emoji} {r['case_type'].title()}",
                value=f"`{r['c']}`",
                inline=True,
            )
            total += r["c"]
        embed.set_footer(text=f"Total: {total} cases")
        await ctx.send(embed=embed)

    def _build_case_embed(self, guild, row) -> discord.Embed:
        emoji = {
            "warn": "⚠️", "kick": "👢", "ban": "🔨",
            "mute": "🔇", "timeout": "⏱️", "jail": "🔒",
            "unjail": "🔓", "unban": "✅", "unmute": "🔊",
        }.get(row["case_type"], "📝")
        color = discord.Color.red() if row["active"] else discord.Color.greyple()

        ts = int(datetime.fromisoformat(row["created"]).timestamp())
        embed = discord.Embed(
            title=f"{emoji} Case #{row['id']} — {row['case_type'].upper()}",
            color=color,
            timestamp=datetime.now(),
        )
        embed.add_field(name="👤 User", value=f"<@{row['user_id']}>", inline=True)
        embed.add_field(name="👮 Mod", value=f"<@{row['mod_id']}>", inline=True)
        embed.add_field(name="📊 Status",
                        value="🔴 Active" if row["active"] else "⚪ Closed",
                        inline=True)
        embed.add_field(name="📝 Reason", value=row["reason"] or "N/A", inline=False)
        if row["duration"]:
            embed.add_field(name="⏰ Duration", value=f"`{row['duration']}`", inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{ts}:F> (<t:{ts}:R>)", inline=False)
        if row["closed"]:
            ts2 = int(datetime.fromisoformat(row["closed"]).timestamp())
            embed.add_field(name="🔒 Closed", value=f"<t:{ts2}:R>", inline=False)
        return embed


async def setup(bot):
    await bot.add_cog(ModerationCases(bot))