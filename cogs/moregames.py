# cogs/moregames.py
# =====================================================================
# ─── MORE GAMES — TicTacToe / Connect4 / Wordle / Chess (simplified)
# =====================================================================
import discord
from discord.ext import commands
import random

from data_manager import ECONOMY, save_economy as _save_economy

# ═══════════════════════════════════════════════════════════════════
# ─── TIC-TAC-TOE
# ═══════════════════════════════════════════════════════════════════
class TTTButton(discord.ui.Button):
    def __init__(self, idx: int, view):
        super().__init__(
            label="⬜", style=discord.ButtonStyle.secondary,
            row=idx // 3, custom_id=f"ttt:{idx}",
        )
        self.idx = idx
        self.view_ref = view

    async def callback(self, it: discord.Interaction):
        v = self.view_ref
        if it.user.id not in (v.p1, v.p2):
            return await it.response.send_message("❌ Machi dyalek!", ephemeral=True)
        if v.turn != it.user.id:
            return await it.response.send_message("⏳ Machi turn dyalek!", ephemeral=True)
        if v.board[self.idx] != " ":
            return await it.response.send_message("❌ Deja m3mmer!", ephemeral=True)

        symbol = "❌" if it.user.id == v.p1 else "⭕"
        v.board[self.idx] = symbol
        self.label = symbol
        self.disabled = True

        winner = v._check_winner()
        if winner:
            v.finished = True
            for c in v.children:
                c.disabled = True
            for c in v.children:
                if isinstance(c, TTTButton) and v.board[c.idx] != " ":
                    c.style = discord.ButtonStyle.success
            color = discord.Color.green() if winner == "X" else discord.Color.blurple()
            if winner == "D":
                embed = v.build_embed("🤝 Ta3adol!", discord.Color.yellow())
                if v.bet > 0:
                    # Refund
                    for uid in (v.p1, v.p2):
                        eco = ECONOMY.setdefault(it.guild.id, {}).setdefault(uid, {"balance": 0, "bank": 0})
                        eco["balance"] += v.bet
                    _save_economy()
            else:
                winner_id = v.p1 if winner == "X" else v.p2
                loser_id = v.p2 if winner == "X" else v.p1
                if v.bet > 0:
                    eco_w = ECONOMY.setdefault(it.guild.id, {}).setdefault(winner_id, {"balance": 0, "bank": 0})
                    eco_w["balance"] += v.bet * 2
                    _save_economy()
                embed = v.build_embed(f"🎉 <@{winner_id}> rb7!", color)
            await it.response.edit_message(embed=embed, view=v)
            v.stop()
            return

        v.turn = v.p2 if it.user.id == v.p1 else v.p1
        embed = v.build_embed()
        await it.response.edit_message(embed=embed, view=v)


class TTTView(discord.ui.View):
    def __init__(self, p1: int, p2: int, bet: int = 0):
        super().__init__(timeout=180)
        self.p1 = p1
        self.p2 = p2
        self.bet = bet
        self.board = [" "] * 9
        self.turn = p1
        self.finished = False
        for i in range(9):
            self.add_item(TTTButton(i, self))

    def _check_winner(self):
        b = self.board
        wins = [
            (0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6),
        ]
        for a, bb, c in wins:
            if b[a] != " " and b[a] == b[bb] == b[c]:
                return "X" if b[a] == "❌" else "O"
        if " " not in b:
            return "D"
        return None

    def build_embed(self, result: str = None, color=None):
        embed = discord.Embed(
            title="🎮 Tic-Tac-Toe",
            description=f"<@{self.p1}> ❌ vs ⭕ <@{self.p2}>",
            color=color or discord.Color.blurple(),
        )
        embed.add_field(name="Turn", value=f"<@{self.turn}>", inline=True)
        if self.bet > 0:
            embed.add_field(name="💰 Bet", value=f"`{self.bet:,}`", inline=True)
        if result:
            embed.add_field(name="Result", value=result, inline=False)
        return embed


# ═══════════════════════════════════════════════════════════════════
# ─── CONNECT 4
# ═══════════════════════════════════════════════════════════════════
class C4Button(discord.ui.Button):
    def __init__(self, col: int, view):
        super().__init__(label=f"⬇️{c+1}", style=discord.ButtonStyle.primary,
                         row=0, custom_id=f"c4:{col}")
        self.col = col
        self.view_ref = view

    async def callback(self, it: discord.Interaction):
        v = self.view_ref
        if it.user.id not in (v.p1, v.p2):
            return await it.response.send_message("❌ Machi dyalek!", ephemeral=True)
        if v.turn != it.user.id:
            return await it.response.send_message("⏳ Machi turn dyalek!", ephemeral=True)

        # Drop piece
        for r in range(5, -1, -1):
            if v.board[r][self.col] == "⚫":
                v.board[r][self.col] = "🔴" if it.user.id == v.p1 else "🟡"
                break
        else:
            return await it.response.send_message("❌ Column m3ammra!", ephemeral=True)

        winner = v._check_winner()
        if winner:
            v.finished = True
            for c in v.children:
                c.disabled = True
            if winner == "D":
                embed = v.build_embed("🤝 Ta3adol!", discord.Color.yellow())
                if v.bet > 0:
                    for uid in (v.p1, v.p2):
                        eco = ECONOMY.setdefault(it.guild.id, {}).setdefault(uid, {"balance": 0, "bank": 0})
                        eco["balance"] += v.bet
                    _save_economy()
            else:
                wid = v.p1 if winner == "🔴" else v.p2
                if v.bet > 0:
                    eco = ECONOMY.setdefault(it.guild.id, {}).setdefault(wid, {"balance": 0, "bank": 0})
                    eco["balance"] += v.bet * 2
                    _save_economy()
                embed = v.build_embed(f"🎉 <@{wid}> rb7!", discord.Color.green())
            await it.response.edit_message(embed=embed, view=v)
            v.stop()
            return

        v.turn = v.p2 if it.user.id == v.p1 else v.p1
        await it.response.edit_message(embed=v.build_embed(), view=v)


class C4View(discord.ui.View):
    def __init__(self, p1: int, p2: int, bet: int = 0):
        super().__init__(timeout=300)
        self.p1 = p1
        self.p2 = p2
        self.bet = bet
        self.board = [["⚫"] * 7 for _ in range(6)]  # 6 rows × 7 cols
        self.turn = p1
        self.finished = False
        for c in range(7):
            self.add_item(C4Button(c, self))

    def _check_winner(self):
        b = self.board
        # Horizontal
        for r in range(6):
            for c in range(4):
                if b[r][c] != "⚫" and b[r][c] == b[r][c+1] == b[r][c+2] == b[r][c+3]:
                    return b[r][c]
        # Vertical
        for r in range(3):
            for c in range(7):
                if b[r][c] != "⚫" and b[r][c] == b[r+1][c] == b[r+2][c] == b[r+3][c]:
                    return b[r][c]
        # Diag ↘
        for r in range(3):
            for c in range(4):
                if b[r][c] != "⚫" and b[r][c] == b[r+1][c+1] == b[r+2][c+2] == b[r+3][c+3]:
                    return b[r][c]
        # Diag ↙
        for r in range(3):
            for c in range(3, 7):
                if b[r][c] != "⚫" and b[r][c] == b[r+1][c-1] == b[r+2][c-2] == b[r+3][c-3]:
                    return b[r][c]
        if all(b[0][c] != "⚫" for c in range(7)):
            return "D"
        return None

    def build_embed(self, result: str = None, color=None):
        board_str = "\n".join("".join(row) for row in self.board)
        embed = discord.Embed(
            title="🔴 Connect 4",
            description=f"<@{self.p1}> 🔴 vs 🟡 <@{self.p2}>\n\n{board_str}",
            color=color or discord.Color.blurple(),
        )
        embed.add_field(name="Turn", value=f"<@{self.turn}>", inline=True)
        if self.bet > 0:
            embed.add_field(name="💰 Bet", value=f"`{self.bet:,}`", inline=True)
        if result:
            embed.add_field(name="Result", value=result, inline=False)
        return embed


# ═══════════════════════════════════════════════════════════════════
# ─── WORDLE (FR/EN mix — simple word list)
# ═══════════════════════════════════════════════════════════════════
WORDLE_WORDS = [
    "apple", "brain", "candy", "dream", "eagle", "flame", "ghost", "heart",
    "igloo", "joker", "knife", "lemon", "magic", "north", "ocean", "piano",
    "queen", "river", "smile", "tiger", "unity", "voice", "water", "xenon",
    "yacht", "zebra", "actor", "beach", "cloud", "dance", "earth", "fairy",
    "green", "house", "input", "jelly", "kayak", "light", "money", "night",
]


def _wordle_feedback(guess: str, target: str) -> str:
    """🟩 exact, 🟨 present, ⬛ absent"""
    guess = guess.lower()
    target = target.lower()
    result = ["⬛"] * 5
    used = [False] * 5
    # Greens
    for i in range(5):
        if guess[i] == target[i]:
            result[i] = "🟩"
            used[i] = True
    # Yellows
    for i in range(5):
        if result[i] == "🟩":
            continue
        for j in range(5):
            if not used[j] and guess[i] == target[j]:
                result[i] = "🟨"
                used[j] = True
                break
    return "".join(result)


class WordleView(discord.ui.View):
    def __init__(self, user_id: int, word: str, bet: int = 0):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.word = word
        self.bet = bet
        self.guesses = []
        self.max_guesses = 6

    async def interaction_check(self, it):
        return it.user.id == self.user_id

    def build_embed(self, result: str = None, color=None):
        lines = []
        for g in self.guesses:
            fb = _wordle_feedback(g, self.word)
            lines.append(f"`{g.upper()}` {fb}")
        for _ in range(self.max_guesses - len(self.guesses)):
            lines.append("`?????` ⬛⬛⬛⬛⬛")

        embed = discord.Embed(
            title="🎯 Wordle",
            description="\n".join(lines),
            color=color or discord.Color.blurple(),
        )
        embed.add_field(name="Guesses", value=f"`{len(self.guesses)}/{self.max_guesses}`", inline=True)
        if self.bet > 0:
            embed.add_field(name="💰 Bet", value=f"`{self.bet:,}`", inline=True)
        if result:
            embed.add_field(name="Result", value=result, inline=False)
        return embed

    @discord.ui.button(label="Guess", emoji="⌨️", style=discord.ButtonStyle.primary)
    async def guess_btn(self, it, b):
        await it.response.send_modal(WordleGuessModal(self))


class WordleGuessModal(discord.ui.Modal, title="🎯 Wordle Guess"):
    word_input = discord.ui.TextInput(label="5-letter word", min_length=5, max_length=5)

    def __init__(self, view: WordleView):
        super().__init__()
        self.view_ref = view

    async def on_submit(self, it):
        v = self.view_ref
        guess = self.word_input.value.lower().strip()
        if not guess.isalpha() or len(guess) != 5:
            return await it.response.send_message("❌ 5 letters ghir!", ephemeral=True)

        v.guesses.append(guess)

        if guess == v.word:
            v.finished = True
            for c in v.children:
                c.disabled = True
            if v.bet > 0:
                eco = ECONOMY.setdefault(it.guild.id, {}).setdefault(it.user.id, {"balance": 0, "bank": 0})
                eco["balance"] += v.bet * 2
                _save_economy()
            embed = v.build_embed(f"🎉 **Sahih!** `{v.word.upper()}`", discord.Color.green())
            try:
                await v.message.edit(embed=embed, view=v)
            except Exception:
                pass
            return await it.response.send_message("🎉 Rb7ti!", ephemeral=True)

        if len(v.guesses) >= v.max_guesses:
            v.finished = True
            for c in v.children:
                c.disabled = True
            embed = v.build_embed(f"😢 **Word kan:** `{v.word.upper()}`", discord.Color.red())
            try:
                await v.message.edit(embed=embed, view=v)
            except Exception:
                pass
            return await it.response.send_message("😢 Khserti!", ephemeral=True)

        try:
            await v.message.edit(embed=v.build_embed(), view=v)
        except Exception:
            pass
        await it.response.send_message("✅ Guess registered!", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════
# ─── COG
# ═══════════════════════════════════════════════════════════════════
class MoreGames(commands.Cog):
    """TicTacToe / Connect4 / Wordle"""

    def __init__(self, bot):
        self.bot = bot

    # ─── Tic-Tac-Toe
    @commands.command(name="ttt", aliases=["tictactoe"])
    async def ttt(self, ctx: commands.Context, opponent: discord.Member, bet: int = 0):
        """`&ttt @user [bet]`"""
        if opponent.bot or opponent.id == ctx.author.id:
            return await ctx.send("❌ @user s7i7 (machi bot wla rasek)")
        if bet > 0:
            eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(ctx.author.id, {"balance": 0, "bank": 0})
            if eco["balance"] < bet:
                return await ctx.send("❌ Ma 3endekch flous!")
            eco["balance"] -= bet
            _save_economy()

        view = TTTView(ctx.author.id, opponent.id, bet)
        embed = view.build_embed()
        embed.description = (
            f"<@{view.p1}> ❌ vs ⭕ <@{view.p2}>\n\n"
            f"<@{view.p1}> bda!"
        )
        msg = await ctx.send(f"{opponent.mention} — {ctx.author.mention} 3ayet lik!", embed=embed, view=view)

    # ─── Connect 4
    @commands.command(name="c4", aliases=["connect4"])
    async def c4(self, ctx: commands.Context, opponent: discord.Member, bet: int = 0):
        """`&c4 @user [bet]`"""
        if opponent.bot or opponent.id == ctx.author.id:
            return await ctx.send("❌ @user s7i7!")
        if bet > 0:
            eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(ctx.author.id, {"balance": 0, "bank": 0})
            if eco["balance"] < bet:
                return await ctx.send("❌ Ma 3endekch flous!")
            eco["balance"] -= bet
            _save_economy()

        view = C4View(ctx.author.id, opponent.id, bet)
        await ctx.send(f"{opponent.mention}!", embed=view.build_embed(), view=view)

    # ─── Wordle
    @commands.command(name="wordle")
    async def wordle(self, ctx: commands.Context, bet: int = 0):
        """`&wordle [bet]`"""
        if bet > 0:
            eco = ECONOMY.setdefault(ctx.guild.id, {}).setdefault(ctx.author.id, {"balance": 0, "bank": 0})
            if eco["balance"] < bet:
                return await ctx.send("❌ Ma 3endekch flous!")
            eco["balance"] -= bet
            _save_economy()

        word = random.choice(WORDLE_WORDS)
        view = WordleView(ctx.author.id, word, bet)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg


async def setup(bot):
    await bot.add_cog(MoreGames(bot))