# cogs/tournaments.py
import discord
from discord import app_commands
from discord.ext import commands
import random
from database import KVStore, SqliteStore
from database.engine import execute, commit
from data_manager import ECONOMY, save_economy

def _ensure():
    execute("""CREATE TABLE IF NOT EXISTS tournaments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER, host_id INTEGER, game TEXT,
        entry INTEGER, max_players INTEGER, prize_pool INTEGER,
        status TEXT, created TEXT, winner_id INTEGER)""")
    execute("""CREATE TABLE IF NOT EXISTS tournament_players (
        tournament_id INTEGER, user_id INTEGER,
        PRIMARY KEY (tournament_id, user_id))""")
    commit()
_ensure()

class Tournaments(commands.Cog):
    """Tournament system"""
    def __init__(self, bot):
        self.bot = bot

    def _next_id(self):
        row = execute("SELECT MAX(id) as m FROM tournaments").fetchone()
        return (row["m"] or 0) + 1

    @commands.group(name="tournament", aliases=["tourney","tr"], invoke_without_command=True)
    async def tour_group(self, ctx):
        rows = execute("SELECT * FROM tournaments WHERE guild_id=? AND status='open' ORDER BY id DESC LIMIT 10", (ctx.guild.id,)).fetchall()
        if not rows:
            return await ctx.send("❌ Ma kaynch tournaments mfto7in!")
        embed = discord.Embed(title="🏆 Open Tournaments", color=discord.Color.gold())
        for r in rows:
            cnt = execute("SELECT COUNT(*) as c FROM tournament_players WHERE tournament_id=?", (r["id"],)).fetchone()["c"]
            embed.add_field(
                name=f"#{r['id']} — {r['game']}",
                value=f"Entry: `{r['entry']:,}` 🪙 | `{cnt}/{r['max_players']}` | Prize: `{r['prize_pool']:,}` 🪙",
                inline=False,
            )
        await ctx.send(embed=embed)

    @tour_group.command(name="create")
    async def create(self, ctx, game: str, entry: int, max_players: int = 8, *, prize_pool: int = 0):
        """&tournament create <game> <entry_fee> <max_players> [prize_pool]"""
        if entry < 0 or max_players < 2 or max_players > 32:
            return await ctx.send("❌ entry>=0, max_players 2-32")
        tid = self._next_id()
        prize = prize_pool if prize_pool > 0 else entry * max_players
        execute("INSERT INTO tournaments (id, guild_id, host_id, game, entry, max_players, prize_pool, status, created) VALUES (?,?,?,?,?,?,?,?,?)",
                (tid, ctx.guild.id, ctx.author.id, game, entry, max_players, prize, "open", __import__("datetime").datetime.now().isoformat()))
        commit()
        await ctx.send(f"✅ Tournament **#{tid}** — {game}\nEntry: `{entry:,}` | Max: `{max_players}` | Prize: `{prize:,}` 🪙\n**`&tournament join {tid}`**")

    @tour_group.command(name="join")
    async def join(self, ctx, tid: int):
        row = execute("SELECT * FROM tournaments WHERE id=? AND guild_id=?", (tid, ctx.guild.id)).fetchone()
        if not row or row["status"] != "open":
            return await ctx.send("❌ Tournament machi mfto7!")
        cnt = execute("SELECT COUNT(*) as c FROM tournament_players WHERE tournament_id=?", (tid,)).fetchone()["c"]
        if cnt >= row["max_players"]:
            return await ctx.send("❌ Deja 3amer!")
        exists = execute("SELECT 1 FROM tournament_players WHERE tournament_id=? AND user_id=?", (tid, ctx.author.id)).fetchone()
        if exists: return await ctx.send("❌ Deja fih!")
        eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(ctx.author.id, {"balance":0,"bank":0,"inventory":[]})
        if eco["balance"] < row["entry"]:
            return await ctx.send(f"❌ Khass `{row['entry']:,}` 🪙!")
        eco["balance"] -= row["entry"]
        save_economy()
        execute("INSERT INTO tournament_players (tournament_id, user_id) VALUES (?,?)", (tid, ctx.author.id))
        commit()
        await ctx.send(f"✅ Dkhelti f **#{tid}**! ({cnt+1}/{row['max_players']})")

    @tour_group.command(name="start")
    async def start(self, ctx, tid: int):
        row = execute("SELECT * FROM tournaments WHERE id=? AND guild_id=?", (tid, ctx.guild.id)).fetchone()
        if not row or row["host_id"] != ctx.author.id:
            return await ctx.send("❌ Ghir host!")
        players = execute("SELECT user_id FROM tournament_players WHERE tournament_id=?", (tid,)).fetchall()
        if len(players) < 2:
            return await ctx.send("❌ Khass 2+ players!")
        winner_id = random.choice([p["user_id"] for p in players])
        execute("UPDATE tournaments SET status='finished', winner_id=? WHERE id=?", (winner_id, tid))
        commit()
        eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(winner_id, {"balance":0,"bank":0,"inventory":[]})
        eco["balance"] += row["prize_pool"]
        save_economy()
        await ctx.send(f"🏆 **Tournament #{tid} khlat!**\n🥇 Winner: <@{winner_id}>\n💰 Prize: `{row['prize_pool']:,}` 🪙")

    @tour_group.command(name="leave")
    async def leave(self, ctx, tid: int):
        row = execute("SELECT * FROM tournaments WHERE id=? AND guild_id=?", (tid, ctx.guild.id)).fetchone()
        if not row: return await ctx.send("❌ Ma kaynch!")
        exists = execute("SELECT 1 FROM tournament_players WHERE tournament_id=? AND user_id=?", (tid, ctx.author.id)).fetchone()
        if not exists: return await ctx.send("❌ Machi fih!")
        execute("DELETE FROM tournament_players WHERE tournament_id=? AND user_id=?", (tid, ctx.author.id))
        commit()
        eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(ctx.author.id, {"balance":0,"bank":0,"inventory":[]})
        eco["balance"] += row["entry"]
        save_economy()
        await ctx.send("👋 Khrjti + refund!")

async def setup(bot): await bot.add_cog(Tournaments(bot))