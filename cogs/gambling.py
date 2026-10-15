# cogs/gambling.py
# =====================================================================
# ─── GAMBLING — Casino games (UnbelievaBoat-style) KOLCHI
# =====================================================================
import discord
from discord.ext import commands
import random
import asyncio

from data_manager import ECONOMY, save_economy as _save_economy
from botconfig import CASINO_CHANNEL_ID, CASINO_CATEGORY_KEYWORDS


# ═══════════════════════════════════════════════════════════════════
# ─── CASINO CHECK
# ═══════════════════════════════════════════════════════════════════
def is_casino_channel(channel) -> bool:
    if CASINO_CHANNEL_ID and channel.id == CASINO_CHANNEL_ID:
        return True
    if channel.category:
        cat_name = channel.category.name.lower()
        if any(kw in cat_name for kw in CASINO_CATEGORY_KEYWORDS):
            return True
    ch_name = channel.name.lower()
    if any(kw in ch_name for kw in CASINO_CATEGORY_KEYWORDS):
        return True
    return False


def casino_only():
    async def predicate(ctx: commands.Context) -> bool:
        if not is_casino_channel(ctx.channel):
            raise commands.CheckFailure(
                "❌ Had command khedma **ghir f Casino channels**! 🎰\n"
                "> Category: **Grow Casino** wla smiya fih 'casino'"
            )
        return True
    return commands.check(predicate)


# ═══════════════════════════════════════════════════════════════════
# ─── CARD HELPERS
# ═══════════════════════════════════════════════════════════════════
SUITS = ["♠️", "♥️", "♦️", "♣️"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


def draw_card():
    return (random.choice(RANKS), random.choice(SUITS))


def card_value(rank: str) -> int:
    if rank in ("J", "Q", "K"):
        return 10
    if rank == "A":
        return 11
    return int(rank)


def hand_value(hand: list) -> int:
    total = 0
    aces = 0
    for rank, _ in hand:
        if rank == "A":
            aces += 1
            total += 11
        else:
            total += card_value(rank)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def fmt_hand(hand: list) -> str:
    return " ".join(f"`{r}{s}`" for r, s in hand)


def fmt_cards(cards: list) -> str:
    return " ".join(f"`{r}{s}`" for r, s in cards)


def card_int(rank: str) -> int:
    if rank == "A":
        return 14
    if rank == "J":
        return 11
    if rank == "Q":
        return 12
    if rank == "K":
        return 13
    return int(rank)


def poker_value(rank):
    if rank == "A":
        return 14
    if rank == "K":
        return 13
    if rank == "Q":
        return 12
    if rank == "J":
        return 11
    return int(rank)


def evaluate_poker(hand):
    """Rje3 (name, multiplier) dyal 5-card poker hand."""
    ranks = [poker_value(r) for r, _ in hand]
    suits = [s for _, s in hand]
    counts = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1

    is_flush = len(set(suits)) == 1
    sorted_ranks = sorted(ranks)
    is_straight = all(sorted_ranks[i] + 1 == sorted_ranks[i + 1] for i in range(4))
    if sorted_ranks == [2, 3, 4, 5, 14]:
        is_straight = True

    count_vals = sorted(counts.values(), reverse=True)

    if is_straight and is_flush and sorted_ranks == [10, 11, 12, 13, 14]:
        return ("🌟 Royal Flush", 250)
    if is_straight and is_flush:
        return ("💫 Straight Flush", 50)
    if count_vals[0] == 4:
        return ("🎯 Four of a Kind", 25)
    if count_vals[0] == 3 and count_vals[1] == 2:
        return ("🏠 Full House", 9)
    if is_flush:
        return ("🌈 Flush", 6)
    if is_straight:
        return ("📏 Straight", 4)
    if count_vals[0] == 3:
        return ("🎪 Three of a Kind", 3)
    if count_vals[0] == 2 and count_vals[1] == 2:
        return ("👯 Two Pair", 2)
    if count_vals[0] == 2:
        return ("👤 Jacks or Better", 1)
    return ("❌ Nothing", 0)


# ═══════════════════════════════════════════════════════════════════
# ─── GAMBLING COG
# ═══════════════════════════════════════════════════════════════════
class Gambling(commands.Cog):
    """Casino: cf, d, rl, s, bj, hl, hr, wheel, mines, crash, bac, poker, tower, plinko, rlt"""

    def __init__(self, bot):
        self.bot = bot

    def _get_user(self, guild_id: int, user_id: int) -> dict:
        ECONOMY.setdefault(guild_id, {}).setdefault(user_id, {
            "balance": 0, "bank": 0, "inventory": [],
        })
        return ECONOMY[guild_id][user_id]

    def _check_bet(self, data: dict, amount: int) -> str | None:
        if amount <= 0:
            return "❌ Amount khass > 0!"
        if data["balance"] < amount:
            return f"❌ Ma 3endkch `{amount:,}` 🪙 f wallet!"
        return None

    # ═══════════════════════════════════════════════════════════
    # ─── COINFLIP
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="cf")
    @casino_only()
    async def cf(self, ctx: commands.Context, amount: int, choice: str):
        """&cf <amount> <pile|face>"""
        choice = choice.lower()
        if choice not in ("pile", "face"):
            return await ctx.send("❌ Khtar `pile` wla `face`!")
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        result = random.choice(["pile", "face"])
        emoji = "🪙" if result == "pile" else "🎭"
        if result == choice:
            data["balance"] += amount
            _save_economy()
            await ctx.send(f"🎉 {emoji} **{result.upper()}**! +`{amount:,}` 🪙")
        else:
            data["balance"] -= amount
            _save_economy()
            await ctx.send(f"😢 {emoji} **{result.upper()}**! -`{amount:,}` 🪙")

    # ═══════════════════════════════════════════════════════════
    # ─── DICE
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="d")
    @casino_only()
    async def d(self, ctx: commands.Context, amount: int, number: int):
        """&d <amount> <1-6>"""
        if not 1 <= number <= 6:
            return await ctx.send("❌ Ra9m 1-6!")
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        roll = random.randint(1, 6)
        dice_emojis = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
        if roll == number:
            win = amount * 5
            data["balance"] += win
            _save_economy()
            await ctx.send(f"🎉 {dice_emojis[roll-1]} **{roll}**! +`{win:,}` 🪙 (5x)")
        else:
            data["balance"] -= amount
            _save_economy()
            await ctx.send(f"😢 {dice_emojis[roll-1]} **{roll}**! -`{amount:,}` 🪙")

    # ═══════════════════════════════════════════════════════════
    # ─── ROULETTE (simple)
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="rl", aliases=["rp"])
    @casino_only()
    async def rl(self, ctx: commands.Context, amount: int, choice: str):
        """&rl <amount> <red|black|green>"""
        choice = choice.lower()
        if choice not in ("red", "black", "green"):
            return await ctx.send("❌ Khtar `red`, `black`, wla `green`!")
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        number = random.randint(0, 36)
        if number == 0:
            result = "green"
        elif 1 <= number <= 18:
            result = "red"
        else:
            result = "black"
        emoji = {"red": "🔴", "black": "⚫", "green": "🟢"}[result]
        if result == choice:
            multiplier = 14 if result == "green" else 2
            win = amount * multiplier
            data["balance"] += win
            _save_economy()
            await ctx.send(f"🎉 {emoji} **{number}** ({result.upper()})! +`{win:,}` 🪙 ({multiplier}x)")
        else:
            data["balance"] -= amount
            _save_economy()
            await ctx.send(f"😢 {emoji} **{number}** ({result.upper()})! -`{amount:,}` 🪙")

    # ═══════════════════════════════════════════════════════════
    # ─── SLOTS
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="s")
    @casino_only()
    async def s(self, ctx: commands.Context, amount: int):
        """&s <amount>"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        emojis = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣"]
        result = [random.choice(emojis) for _ in range(3)]
        msg = " | ".join(result)
        if result[0] == result[1] == result[2]:
            win = amount * 10
            data["balance"] += win
            _save_economy()
            await ctx.send(f"🎉 **JACKPOT!** 🎰 {msg}\n+`{win:,}` 🪙 (10x)")
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            win = amount * 2
            data["balance"] += win
            _save_economy()
            await ctx.send(f"✨ **Zouj!** 🎰 {msg}\n+`{win:,}` 🪙 (2x)")
        else:
            data["balance"] -= amount
            _save_economy()
            await ctx.send(f"😢 🎰 {msg}\n-`{amount:,}` 🪙")

    # ═══════════════════════════════════════════════════════════
    # ─── BLACKJACK
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="bj", aliases=["blackjack"])
    @casino_only()
    async def bj(self, ctx: commands.Context, amount: int):
        """&bj <amount> — Blackjack interactif"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        player = [draw_card(), draw_card()]
        dealer = [draw_card(), draw_card()]
        view = BlackjackView(ctx.author.id, amount, player, dealer, data)
        embed = view.build_embed(show_dealer=False)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    # ═══════════════════════════════════════════════════════════
    # ─── HIGH-LOW
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="hl", aliases=["highlow"])
    @casino_only()
    async def hl(self, ctx: commands.Context, amount: int):
        """&hl <amount> — High or Low"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        card = draw_card()
        view = HighLowView(ctx.author.id, amount, card, data)
        embed = view.build_embed()
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    # ═══════════════════════════════════════════════════════════
    # ─── HORSE RACE
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="hr", aliases=["horserace"])
    @casino_only()
    async def hr(self, ctx: commands.Context, horse: int, amount: int):
        """&hr <1-5> <amount> — Rahan 3la 7isan"""
        if not 1 <= horse <= 5:
            return await ctx.send("❌ Khtar 7isan bin `1` w `5`!")
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        horses = ["🐎", "🏇", "🦄", "🐴", "🎠"]
        names = ["Thunder", "Shadow", "Comet", "Blaze", "Storm"]
        positions = [0] * 5
        finish_order = []
        steps = 0

        embed = discord.Embed(
            title="🏁 Horse Race",
            description=self._race_display(horses, names, positions, horse - 1),
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"Rahant 3la {horses[horse-1]} **{names[horse-1]}** — {amount:,} 🪙")
        msg = await ctx.send(embed=embed)

        while len(finish_order) < 5 and steps < 60:
            await asyncio.sleep(1.2)
            for i in range(5):
                if i in finish_order:
                    continue
                positions[i] += random.choice([0, 1, 1, 2, 3])
                if positions[i] >= 15:
                    finish_order.append(i)

            embed.description = self._race_display(horses, names, positions, horse - 1)
            try:
                await msg.edit(embed=embed)
            except Exception:
                break
            steps += 1

        if not finish_order:
            winner = max(range(5), key=lambda i: positions[i])
        else:
            winner = finish_order[0]

        if winner == horse - 1:
            win = amount * 4
            data["balance"] += win
            _save_economy()
            result = f"🏆 **{horses[winner]} {names[winner]}** rb7! +`{win:,}` 🪙 (4x)"
            color = discord.Color.green()
        else:
            data["balance"] -= amount
            _save_economy()
            result = f"😢 **{horses[winner]} {names[winner]}** rb7! -`{amount:,}` 🪙"
            color = discord.Color.red()

        embed.add_field(name="Result", value=result, inline=False)
        embed.color = color
        try:
            await msg.edit(embed=embed)
        except Exception:
            await ctx.send(result)

    def _race_display(self, horses, names, positions, chosen):
        lines = []
        for i in range(5):
            track = "▬" * min(positions[i], 15) + horses[i]
            marker = " ⬅️" if i == chosen else ""
            lines.append(f"**{i+1}.** `{names[i]:<8}` {track}{marker}")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════
    # ─── WHEEL
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="wheel", aliases=["wf"])
    @casino_only()
    async def wheel(self, ctx: commands.Context, amount: int):
        """&wheel <amount> — Spin wheel"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        segments = [
            ("💀 0x", 0, 25),
            ("🍒 0.5x", 0.5, 20),
            ("🍋 1x", 1, 15),
            ("🍊 1.5x", 1.5, 12),
            ("🍇 2x", 2, 12),
            ("💎 3x", 3, 8),
            ("⭐ 5x", 5, 5),
            ("👑 10x", 10, 3),
        ]
        labels = [s[0] for s in segments]
        mults = [s[1] for s in segments]
        weights = [s[2] for s in segments]
        chosen = random.choices(range(len(segments)), weights=weights, k=1)[0]

        msg = await ctx.send("🎡 **Spin...**")
        for _ in range(8):
            idx = random.randint(0, len(segments) - 1)
            await asyncio.sleep(0.25)
            await msg.edit(content=f"🎡 Spinning... {labels[idx]}")
        await asyncio.sleep(0.5)
        await msg.edit(content=f"🎡 **{labels[chosen]}**")

        mult = mults[chosen]
        if mult == 0:
            data["balance"] -= amount
            _save_economy()
            await ctx.send(f"💀 **Khserti!** -`{amount:,}` 🪙")
        elif mult == 1:
            await ctx.send("🤝 **Ta3adol** — bla rb7 wla khsara")
        else:
            win = int(amount * mult)
            data["balance"] += win - amount
            _save_economy()
            await ctx.send(f"🎉 **{labels[chosen]}**! +`{win - amount:,}` 🪙 ({mult}x)")

    # ═══════════════════════════════════════════════════════════
    # ─── MINES
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="mines", aliases=["mine"])
    @casino_only()
    async def mines(self, ctx: commands.Context, amount: int, bombs: int = 3):
        """&mines <amount> [bombs=3]"""
        if not 1 <= bombs <= 24:
            return await ctx.send("❌ Bombs khass bin `1` w `24`!")
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        view = MinesView(ctx.author.id, amount, bombs, data)
        embed = view.build_embed()
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    # ═══════════════════════════════════════════════════════════
    # ─── CRASH
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="crash")
    @casino_only()
    async def crash(self, ctx: commands.Context, amount: int):
        """&crash <amount> — Cash out 9bel crash"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        view = CrashView(ctx.author.id, amount, data)
        embed = view.build_embed()
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg
        view.start()

    # ═══════════════════════════════════════════════════════════
    # ─── BACCARAT
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="bac", aliases=["baccarat"])
    @casino_only()
    async def bac(self, ctx, amount: int, choice: str = None):
        """&bac <amount> [player|banker|tie]"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        if choice is None:
            view = BaccaratBetView(ctx.author.id, amount, data)
            await ctx.send(
                embed=discord.Embed(
                    title="🎴 Baccarat",
                    description=f"**Bet:** `{amount:,}` 🪙\nKhtar 3la chkoun rahan:",
                    color=discord.Color.dark_green(),
                ),
                view=view,
            )
            return

        c = choice.lower()
        if c in ("p", "player"):
            c = "player"
        elif c in ("b", "banker"):
            c = "banker"
        elif c in ("t", "tie"):
            c = "tie"
        else:
            return await ctx.send("❌ Khtar: `player`, `banker`, wla `tie`!")

        await self._play_baccarat(ctx, ctx.author.id, amount, c, data, None)

    async def _play_baccarat(self, ctx_or_it, user_id, amount, choice, data, interaction):
        player = [draw_card(), draw_card()]
        banker = [draw_card(), draw_card()]

        def bval(cards):
            return sum(
                1 if r == "A" else 0 if r in ("10", "J", "Q", "K") else int(r)
                for r, _ in cards
            ) % 10

        p_total = bval(player)
        b_total = bval(banker)

        if p_total < 8 and b_total < 8:
            if p_total <= 5:
                player.append(draw_card())
                p_total = bval(player)
            if b_total <= 5:
                banker.append(draw_card())
                b_total = bval(banker)

        if p_total > b_total:
            winner = "player"
        elif b_total > p_total:
            winner = "banker"
        else:
            winner = "tie"

        if choice == winner:
            mult = 9 if winner == "tie" else 2
            win = amount * mult
            data["balance"] += win
            result = f"🎉 **{winner.upper()}** rb7! +`{win:,}` 🪙 ({mult}x)"
            color = discord.Color.green()
        else:
            data["balance"] -= amount
            result = f"😢 **{winner.upper()}** rb7! -`{amount:,}` 🪙"
            color = discord.Color.red()
        _save_economy()

        embed = discord.Embed(title="🎴 Baccarat", color=color)
        embed.add_field(name=f"👤 Player ({p_total})", value=fmt_cards(player), inline=False)
        embed.add_field(name=f"🏦 Banker ({b_total})", value=fmt_cards(banker), inline=False)
        embed.add_field(name="Result", value=result, inline=False)
        embed.set_footer(text=f"Rahant 3la: {choice.upper()}")

        if interaction:
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            await ctx_or_it.send(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── VIDEO POKER
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="poker", aliases=["vp"])
    @casino_only()
    async def poker(self, ctx, amount: int):
        """&poker <amount> — Video Poker"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        hand = [draw_card() for _ in range(5)]
        data["balance"] -= amount
        _save_economy()

        view = VideoPokerView(ctx.author.id, amount, hand, data)
        embed = view.build_embed(phase="hold")
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    # ═══════════════════════════════════════════════════════════
    # ─── TOWER
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="tower", aliases=["tw"])
    @casino_only()
    async def tower(self, ctx, amount: int):
        """&tower <amount> — 8 floors, khtar 1 mn 3"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        view = TowerView(ctx.author.id, amount, data)
        embed = view.build_embed()
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    # ═══════════════════════════════════════════════════════════
    # ─── PLINKO
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="plinko", aliases=["pl"])
    @casino_only()
    async def plinko(self, ctx, amount: int, risk: str = "medium"):
        """&plinko <amount> [low|medium|high]"""
        risk = risk.lower()
        if risk not in ("low", "medium", "high"):
            return await ctx.send("❌ Risk: `low`, `medium`, wla `high`!")

        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        tables = {
            "low":    [1.5, 1.2, 1.1, 1.0, 0.5, 1.0, 1.1, 1.2, 1.5],
            "medium": [5.0, 2.0, 1.2, 0.7, 0.2, 0.7, 1.2, 2.0, 5.0],
            "high":   [15.0, 5.0, 1.5, 0.4, 0.1, 0.4, 1.5, 5.0, 15.0],
        }
        mults = tables[risk]

        slot = 0
        msg = await ctx.send("🎯 **Kanrmi l-ball...**")
        await asyncio.sleep(0.6)

        for row in range(9):
            await asyncio.sleep(0.35)
            display = self._plinko_frame(row, slot, mults)
            try:
                await msg.edit(content=display)
            except Exception:
                break
            if row < 8:
                if random.random() < 0.5:
                    slot += 1

        slot = min(slot, 8)
        mult = mults[slot]

        # ─── FIX: Sub amount 9bel, mn ba3d zid win
        data["balance"] -= amount
        win = int(amount * mult)
        data["balance"] += win
        _save_economy()

        if mult > 1:
            profit = win - amount
            result = f"🎉 **{mult}x** → +`{profit:,}` 🪙"
            color = discord.Color.green()
        elif mult == 1:
            result = f"🤝 **{mult}x** → Ta3adol"
            color = discord.Color.yellow()
        else:
            profit = amount - win
            result = f"😢 **{mult}x** → -`{profit:,}` 🪙"
            color = discord.Color.red()

        embed = discord.Embed(
            title=f"🎯 Plinko ({risk})",
            description=f"Ball wqe3 f slot **{slot+1}**\n{result}",
            color=color,
        )
        embed.add_field(name="Bet", value=f"`{amount:,}` 🪙", inline=True)
        embed.add_field(name="Multiplier", value=f"`{mult}x`", inline=True)
        embed.add_field(name="Win", value=f"`{win:,}` 🪙", inline=True)
        try:
            await msg.edit(content=None, embed=embed)
        except Exception:
            await ctx.send(embed=embed)

    def _plinko_frame(self, current_row: int, ball_slot: int, mults):
        rows = 9
        lines = ["🎯 **Plinko** — Ball falling...\n"]
        for r in range(rows):
            pad = " " * (rows - r)
            pegs = "· " * (r + 1)
            if r == current_row:
                ball_line = " " * (rows - r) + "  " * ball_slot + "🔴"
                lines.append(ball_line)
            else:
                lines.append(pad + pegs)
        mult_line = " ".join(f"`{m}x`" for m in mults)
        lines.append(f"\n{mult_line}")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════
    # ─── ROULETTE INTERACTIVE
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="rlt", aliases=["roulette_int"])
    @casino_only()
    async def rlt(self, ctx, amount: int):
        """&rlt <amount> — Interactive roulette b buttons"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        err = self._check_bet(data, amount)
        if err:
            return await ctx.send(err)

        view = RouletteBetView(ctx.author.id, amount, data)
        embed = discord.Embed(
            title="🎡 Roulette",
            description=(
                f"**Bet:** `{amount:,}` 🪙\n\n"
                "Khtar:\n"
                "🔴 **Red** (2x)\n"
                "⚫ **Black** (2x)\n"
                "🟢 **Green** (14x)"
            ),
            color=discord.Color.dark_red(),
        )
        await ctx.send(embed=embed, view=view)


# ═══════════════════════════════════════════════════════════════════
# ─── BLACKJACK VIEW
# ═══════════════════════════════════════════════════════════════════
class BlackjackView(discord.ui.View):
    def __init__(self, user_id, amount, player, dealer, data):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.amount = amount
        self.player = player
        self.dealer = dealer
        self.data = data
        self.finished = False
        self.message = None

    def build_embed(self, show_dealer=False):
        p = hand_value(self.player)
        if show_dealer:
            d = hand_value(self.dealer)
            dealer_str = fmt_hand(self.dealer)
            dealer_val = f"**{d}**"
        else:
            dealer_str = f"`{self.dealer[0][0]}{self.dealer[0][1]}` 🎴"
            dealer_val = f"**{card_value(self.dealer[0][0])}** + ?"

        embed = discord.Embed(title="🃏 Blackjack", color=discord.Color.dark_green())
        embed.add_field(name="🤖 Dealer", value=f"{dealer_str}\nTotal: {dealer_val}", inline=False)
        embed.add_field(name="👤 You", value=f"{fmt_hand(self.player)}\nTotal: **{p}**", inline=False)
        embed.set_footer(text=f"Bet: {self.amount:,} 🪙")
        return embed

    async def interaction_check(self, it: discord.Interaction) -> bool:
        if it.user.id != self.user_id:
            await it.response.send_message("❌ Machi dyalek!", ephemeral=True)
            return False
        return True

    async def _end_game(self, it, result: str, color: discord.Color):
        self.finished = True
        for c in self.children:
            c.disabled = True
        embed = self.build_embed(show_dealer=True)
        embed.color = color
        embed.add_field(name="Result", value=result, inline=False)
        await it.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Hit", emoji="🃏", style=discord.ButtonStyle.success)
    async def hit_btn(self, it, b):
        self.player.append(draw_card())
        p = hand_value(self.player)
        if p > 21:
            self.data["balance"] -= self.amount
            _save_economy()
            return await self._end_game(it, f"💥 **BUST!** ({p}) -`{self.amount:,}` 🪙", discord.Color.red())
        if p == 21:
            return await self._dealer_play(it)
        await it.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Stand", emoji="✋", style=discord.ButtonStyle.primary)
    async def stand_btn(self, it, b):
        await self._dealer_play(it)

    @discord.ui.button(label="Double", emoji="💰", style=discord.ButtonStyle.danger)
    async def double_btn(self, it, b):
        if self.data["balance"] < self.amount * 2:
            return await it.response.send_message("❌ Ma 3endkch flous l double!", ephemeral=True)
        self.amount *= 2
        self.player.append(draw_card())
        p = hand_value(self.player)
        if p > 21:
            self.data["balance"] -= self.amount
            _save_economy()
            return await self._end_game(it, f"💥 **BUST!** ({p}) -`{self.amount:,}` 🪙", discord.Color.red())
        await self._dealer_play(it)

    async def _dealer_play(self, it):
        while hand_value(self.dealer) < 17:
            self.dealer.append(draw_card())
        p = hand_value(self.player)
        d = hand_value(self.dealer)

        if d > 21:
            self.data["balance"] += self.amount
            _save_economy()
            await self._end_game(it, f"🎉 **Dealer BUST!** ({d}) +`{self.amount:,}` 🪙", discord.Color.green())
        elif p > d:
            self.data["balance"] += self.amount
            _save_economy()
            await self._end_game(it, f"🎉 **Rb7ti!** ({p} vs {d}) +`{self.amount:,}` 🪙", discord.Color.green())
        elif p < d:
            self.data["balance"] -= self.amount
            _save_economy()
            await self._end_game(it, f"😢 **Khserti!** ({p} vs {d}) -`{self.amount:,}` 🪙", discord.Color.red())
        else:
            await self._end_game(it, f"🤝 **Ta3adol!** ({p} vs {d})", discord.Color.yellow())


# ═══════════════════════════════════════════════════════════════════
# ─── HIGH-LOW VIEW
# ═══════════════════════════════════════════════════════════════════
class HighLowView(discord.ui.View):
    def __init__(self, user_id, amount, card, data):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.amount = amount
        self.card = card
        self.data = data
        self.message = None

    def build_embed(self, result: str = None):
        r, s = self.card
        embed = discord.Embed(
            title="📈 High-Low",
            description=f"### Card: `{r}{s}` ({card_int(r)})\n"
                        f"Next card ghadi ykoun **Higher** wla **Lower**?",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Bet: {self.amount:,} 🪙")
        if result:
            embed.add_field(name="Result", value=result, inline=False)
        return embed

    async def interaction_check(self, it: discord.Interaction) -> bool:
        if it.user.id != self.user_id:
            await it.response.send_message("❌ Machi dyalek!", ephemeral=True)
            return False
        return True

    async def _resolve(self, it, choice: str):
        for c in self.children:
            c.disabled = True

        old_val = card_int(self.card[0])
        new_card = draw_card()
        new_val = card_int(new_card[0])
        if new_val == old_val:
            new_card = draw_card()
            new_val = card_int(new_card[0])

        r, s = new_card
        winner = "higher" if new_val > old_val else "lower"

        if winner == choice:
            self.data["balance"] += self.amount
            _save_economy()
            result = f"🎉 **Sahih!** `{r}{s}` ({new_val}) — +`{self.amount:,}` 🪙"
            color = discord.Color.green()
        else:
            self.data["balance"] -= self.amount
            _save_economy()
            result = f"😢 **Ghalat!** `{r}{s}` ({new_val}) — -`{self.amount:,}` 🪙"
            color = discord.Color.red()

        embed = discord.Embed(
            title="📈 High-Low",
            description=f"**9bel:** `{self.card[0]}{self.card[1]}` ({old_val})\n"
                        f"**Daba:** `{r}{s}` ({new_val})",
            color=color,
        )
        embed.add_field(name="Result", value=result, inline=False)
        await it.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Higher ⬆️", style=discord.ButtonStyle.success)
    async def higher_btn(self, it, b):
        await self._resolve(it, "higher")

    @discord.ui.button(label="Lower ⬇️", style=discord.ButtonStyle.danger)
    async def lower_btn(self, it, b):
        await self._resolve(it, "lower")


# ═══════════════════════════════════════════════════════════════════
# ─── MINES VIEW
# ═══════════════════════════════════════════════════════════════════
class MinesView(discord.ui.View):
    def __init__(self, user_id, amount, bombs, data):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.amount = amount
        self.bombs = bombs
        self.data = data
        self.revealed = {}
        self.bomb_positions = set(random.sample(range(25), bombs))
        self.message = None
        self.finished = False

        for i in range(25):
            btn = discord.ui.Button(
                label="⬜", style=discord.ButtonStyle.secondary,
                row=i // 5, custom_id=f"mine:{i}",
            )
            btn.callback = self._make_callback(i)
            self.add_item(btn)

    def _make_callback(self, idx):
        async def cb(it: discord.Interaction):
            await self._click(it, idx)
        return cb

    def _multiplier(self) -> float:
        safe_count = sum(1 for v in self.revealed.values() if v == "safe")
        if safe_count == 0:
            return 1.0
        safe = 25 - self.bombs
        m = 1.0
        for i in range(safe_count):
            m *= (25 - i) / (safe - i)
        return max(1.0, m * 0.97)

    def build_embed(self, result: str = None, color=None):
        safe_count = sum(1 for v in self.revealed.values() if v == "safe")
        mult = self._multiplier()
        potential = int(self.amount * mult)
        embed = discord.Embed(
            title="💣 Mines",
            description=(
                f"**Bombs:** `{self.bombs}` | **Safe:** `{safe_count}`\n"
                f"**Multiplier:** `{mult:.2f}x` | **Potential:** `{potential:,}` 🪙"
            ),
            color=color or discord.Color.dark_red(),
        )
        embed.set_footer(text=f"Bet: {self.amount:,} 🪙 • Cash out 9bel bomb")
        if result:
            embed.add_field(name="Result", value=result, inline=False)
        return embed

    async def interaction_check(self, it: discord.Interaction) -> bool:
        if it.user.id != self.user_id:
            await it.response.send_message("❌ Machi dyalek!", ephemeral=True)
            return False
        return True

    async def _click(self, it, idx):
        if self.finished:
            return
        if idx in self.revealed:
            return await it.response.send_message("⚠️ Deja mfto7!", ephemeral=True)

        btn = None
        for c in self.children:
            if isinstance(c, discord.ui.Button) and c.custom_id == f"mine:{idx}":
                btn = c
                break

        if idx in self.bomb_positions:
            self.finished = True
            self.data["balance"] -= self.amount
            _save_economy()
            if btn:
                btn.label = "💣"
                btn.style = discord.ButtonStyle.danger
            for i in self.bomb_positions:
                for c in self.children:
                    if isinstance(c, discord.ui.Button) and c.custom_id == f"mine:{i}":
                        c.label = "💣"
                        c.disabled = True
            for c in self.children:
                c.disabled = True
            embed = self.build_embed(f"💥 **BOMB!** -`{self.amount:,}` 🪙", discord.Color.red())
            await it.response.edit_message(embed=embed, view=self)
            self.stop()
            return

        self.revealed[idx] = "safe"
        if btn:
            btn.label = "💎"
            btn.style = discord.ButtonStyle.success
            btn.disabled = True

        mult = self._multiplier()
        potential = int(self.amount * mult)
        safe_total = 25 - self.bombs
        safe_count = sum(1 for v in self.revealed.values() if v == "safe")

        if safe_count == safe_total:
            self.finished = True
            self.data["balance"] += potential
            _save_economy()
            for c in self.children:
                c.disabled = True
            embed = self.build_embed(f"🏆 **Perfect!** +`{potential:,}` 🪙 ({mult:.2f}x)", discord.Color.green())
            await it.response.edit_message(embed=embed, view=self)
            self.stop()
            return

        await it.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="💰 Cash Out", style=discord.ButtonStyle.success, row=5)
    async def cashout_btn(self, it, b):
        if self.finished:
            return
        safe_count = sum(1 for v in self.revealed.values() if v == "safe")
        if safe_count == 0:
            return await it.response.send_message("❌ Ma fte7ti ta 7aja!", ephemeral=True)

        self.finished = True
        mult = self._multiplier()
        profit = int(self.amount * mult) - self.amount
        self.data["balance"] += profit
        _save_economy()

        for c in self.children:
            c.disabled = True
        embed = self.build_embed(f"💰 **Cash Out!** +`{profit:,}` 🪙 ({mult:.2f}x)", discord.Color.green())
        await it.response.edit_message(embed=embed, view=self)
        self.stop()


# ═══════════════════════════════════════════════════════════════════
# ─── CRASH VIEW
# ═══════════════════════════════════════════════════════════════════
class CrashView(discord.ui.View):
    def __init__(self, user_id, amount, data):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.amount = amount
        self.data = data
        self.multiplier = 1.00
        self.crashed = False
        self.cashed_out = False
        self.message = None
        self.crash_point = self._generate_crash()

    def _generate_crash(self) -> float:
        r = random.random()
        if r < 0.04:
            return 1.00
        return round(1 / (1 - random.random() * 0.96), 2)

    def build_embed(self, result: str = None):
        if self.crashed:
            color = discord.Color.red()
            title = "🚀 Crash — 💥 CRASHED!"
        elif self.cashed_out:
            color = discord.Color.green()
            title = "🚀 Crash — 💰 CASHED OUT"
        else:
            color = discord.Color.blurple()
            title = "🚀 Crash"

        embed = discord.Embed(
            title=title,
            description=f"### Multiplier: **{self.multiplier:.2f}x**",
            color=color,
        )
        potential = int(self.amount * self.multiplier)
        embed.add_field(name="Bet", value=f"`{self.amount:,}` 🪙", inline=True)
        embed.add_field(name="Current win", value=f"`{potential:,}` 🪙", inline=True)
        if result:
            embed.add_field(name="Result", value=result, inline=False)
        embed.set_footer(text="Click Cash Out 9bel ma ycrash!")
        return embed

    async def interaction_check(self, it: discord.Interaction) -> bool:
        if it.user.id != self.user_id:
            await it.response.send_message("❌ Machi dyalek!", ephemeral=True)
            return False
        return True

    def start(self):
        self._task = asyncio.create_task(self._loop())

    async def _loop(self):
        await asyncio.sleep(2)
        while not self.crashed and not self.cashed_out:
            await asyncio.sleep(0.8)
            self.multiplier = round(self.multiplier + random.uniform(0.05, 0.25), 2)

            if self.multiplier >= self.crash_point:
                self.crashed = True
                self.data["balance"] -= self.amount
                _save_economy()
                for c in self.children:
                    c.disabled = True
                embed = self.build_embed(f"💥 **CRASHED** f `{self.multiplier:.2f}x` — -`{self.amount:,}` 🪙")
                try:
                    if self.message:
                        await self.message.edit(embed=embed, view=self)
                except Exception:
                    pass
                self.stop()
                return

            try:
                if self.message:
                    await self.message.edit(embed=self.build_embed(), view=self)
            except Exception:
                pass

    @discord.ui.button(label="💰 Cash Out", style=discord.ButtonStyle.success)
    async def cashout_btn(self, it, b):
        if self.crashed or self.cashed_out:
            return await it.response.send_message("❌ Game khlat!", ephemeral=True)

        self.cashed_out = True
        win = int(self.amount * self.multiplier) - self.amount
        self.data["balance"] += win
        _save_economy()

        for c in self.children:
            c.disabled = True
        embed = self.build_embed(f"💰 **Cash Out f `{self.multiplier:.2f}x`** — +`{win:,}` 🪙")
        await it.response.edit_message(embed=embed, view=self)
        self.stop()


# ═══════════════════════════════════════════════════════════════════
# ─── BACCARAT BET VIEW
# ═══════════════════════════════════════════════════════════════════
class BaccaratBetView(discord.ui.View):
    def __init__(self, user_id, amount, data):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.amount = amount
        self.data = data

    async def interaction_check(self, it):
        if it.user.id != self.user_id:
            await it.response.send_message("❌ Machi dyalek!", ephemeral=True)
            return False
        return True

    async def _play(self, it, choice):
        cog = it.client.get_cog("Gambling")
        await cog._play_baccarat(None, self.user_id, self.amount, choice, self.data, it)
        self.stop()

    @discord.ui.button(label="Player", emoji="👤", style=discord.ButtonStyle.success)
    async def player_btn(self, it, b):
        await self._play(it, "player")

    @discord.ui.button(label="Banker", emoji="🏦", style=discord.ButtonStyle.primary)
    async def banker_btn(self, it, b):
        await self._play(it, "banker")

    @discord.ui.button(label="Tie", emoji="🤝", style=discord.ButtonStyle.secondary)
    async def tie_btn(self, it, b):
        await self._play(it, "tie")


# ═══════════════════════════════════════════════════════════════════
# ─── VIDEO POKER VIEW
# ═══════════════════════════════════════════════════════════════════
class VideoPokerView(discord.ui.View):
    def __init__(self, user_id, amount, hand, data):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.amount = amount
        self.hand = hand
        self.data = data
        self.held = [False] * 5
        self.message = None
        self.phase = "hold"

        for i in range(5):
            btn = discord.ui.Button(
                label=f"Card {i+1}", emoji="🃏",
                style=discord.ButtonStyle.secondary,
                row=0, custom_id=f"hold:{i}",
            )
            btn.callback = self._make_hold_cb(i)
            self.add_item(btn)

    def _make_hold_cb(self, idx):
        async def cb(it):
            await self._toggle_hold(it, idx)
        return cb

    async def interaction_check(self, it):
        if it.user.id != self.user_id:
            await it.response.send_message("❌ Machi dyalek!", ephemeral=True)
            return False
        return True

    def build_embed(self, phase="hold"):
        r_strs = [f"{r}{s}" for r, s in self.hand]
        hand_display = "  ".join(
            f"{'🔒' if self.held[i] else '🃏'} `{r_strs[i]}`"
            for i in range(5)
        )
        embed = discord.Embed(title="🃏 Video Poker", color=discord.Color.dark_green())
        embed.add_field(name="Your Hand", value=hand_display, inline=False)
        if phase == "hold":
            embed.description = (
                f"**Bet:** `{self.amount:,}` 🪙\n"
                "Click 3la kartat li bghiti **t-hold** (🔒), mn ba3d **Draw**"
            )
        else:
            name, mult = evaluate_poker(self.hand)
            embed.add_field(name="Result", value=f"{name} — **{mult}x**", inline=False)
        return embed

    async def _toggle_hold(self, it, idx):
        self.held[idx] = not self.held[idx]
        btn = None
        for c in self.children:
            if isinstance(c, discord.ui.Button) and c.custom_id == f"hold:{idx}":
                btn = c
                break
        if btn:
            btn.emoji = "🔒" if self.held[idx] else "🃏"
            btn.style = discord.ButtonStyle.success if self.held[idx] else discord.ButtonStyle.secondary
        await it.response.edit_message(embed=self.build_embed("hold"), view=self)

    @discord.ui.button(label="Draw", emoji="🎴", style=discord.ButtonStyle.primary, row=1)
    async def draw_btn(self, it, b):
        for i in range(5):
            if not self.held[i]:
                self.hand[i] = draw_card()

        name, mult = evaluate_poker(self.hand)
        if mult > 0:
            win = self.amount * mult
            self.data["balance"] += win
            _save_economy()
            result = f"🎉 **{name}** — +`{win:,}` 🪙 ({mult}x)"
            color = discord.Color.green()
        else:
            _save_economy()
            result = f"😢 **{name}** — -`{self.amount:,}` 🪙"
            color = discord.Color.red()

        for c in self.children:
            c.disabled = True

        embed = discord.Embed(title="🃏 Video Poker", color=color)
        hand_display = "  ".join(f"`{r}{s}`" for r, s in self.hand)
        embed.add_field(name="Final Hand", value=hand_display, inline=False)
        embed.add_field(name="Result", value=result, inline=False)
        await it.response.edit_message(embed=embed, view=self)
        self.stop()


# ═══════════════════════════════════════════════════════════════════
# ─── TOWER VIEW
# ═══════════════════════════════════════════════════════════════════
class TowerView(discord.ui.View):
    FLOORS = 8
    MULT_PER_FLOOR = 1.4

    def __init__(self, user_id, amount, data):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.amount = amount
        self.data = data
        self.floor = 0
        self.multiplier = 1.0
        self.trap_index = random.randint(0, 2)
        self.finished = False
        self.message = None
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        for i in range(3):
            btn = discord.ui.Button(
                label=f"🚪 Door {i+1}", style=discord.ButtonStyle.primary,
                row=0, custom_id=f"door:{i}",
            )
            btn.callback = self._make_cb(i)
            self.add_item(btn)

        co = discord.ui.Button(
            label="💰 Cash Out", style=discord.ButtonStyle.success,
            row=1, custom_id="tower:cashout",
        )
        co.callback = self._cashout
        self.add_item(co)

    def _make_cb(self, idx):
        async def cb(it):
            await self._pick(it, idx)
        return cb

    async def interaction_check(self, it):
        if it.user.id != self.user_id:
            await it.response.send_message("❌ Machi dyalek!", ephemeral=True)
            return False
        return True

    def build_embed(self, result=None, color=None):
        display = []
        for f in range(self.FLOORS, 0, -1):
            if f <= self.floor:
                display.append(f"`F{f:>2}` ✅ Safe")
            elif f == self.floor + 1:
                display.append(f"`F{f:>2}` 🎯 **← Hna**")
            else:
                display.append(f"`F{f:>2}` ⬜ ??")
        tower = "\n".join(display)
        potential = int(self.amount * self.multiplier)

        embed = discord.Embed(
            title="🗼 Tower",
            description=f"```\n{tower}\n```",
            color=color or discord.Color.dark_teal(),
        )
        embed.add_field(name="Floor", value=f"`{self.floor}/{self.FLOORS}`", inline=True)
        embed.add_field(name="Multiplier", value=f"`{self.multiplier:.2f}x`", inline=True)
        embed.add_field(name="Potential", value=f"`{potential:,}` 🪙", inline=True)
        embed.set_footer(text=f"Bet: {self.amount:,} 🪙 • Khtar 1 mn 3 • 1 fih bomb")
        if result:
            embed.add_field(name="Result", value=result, inline=False)
        return embed

    async def _pick(self, it, idx):
        if self.finished:
            return
        if idx == self.trap_index:
            self.finished = True
            self.data["balance"] -= self.amount
            _save_economy()
            for c in self.children:
                c.disabled = True
            embed = self.build_embed(
                f"💥 **BOOM!** Door {idx+1} kan fih bomb — -`{self.amount:,}` 🪙",
                discord.Color.red(),
            )
            await it.response.edit_message(embed=embed, view=self)
            self.stop()
            return

        self.floor += 1
        self.multiplier *= self.MULT_PER_FLOOR

        if self.floor >= self.FLOORS:
            self.finished = True
            win = int(self.amount * self.multiplier)
            self.data["balance"] += win
            _save_economy()
            for c in self.children:
                c.disabled = True
            embed = self.build_embed(
                f"🏆 **PERFECT!** +`{win:,}` 🪙 ({self.multiplier:.2f}x)",
                discord.Color.gold(),
            )
            await it.response.edit_message(embed=embed, view=self)
            self.stop()
            return

        self.trap_index = random.randint(0, 2)
        self._build_buttons()
        await it.response.edit_message(embed=self.build_embed(), view=self)

    async def _cashout(self, it):
        if self.finished:
            return
        if self.floor == 0:
            return await it.response.send_message("❌ Ma tl3ti ta floor!", ephemeral=True)

        self.finished = True
        win = int(self.amount * self.multiplier)
        profit = win - self.amount
        self.data["balance"] += profit
        _save_economy()

        for c in self.children:
            c.disabled = True
        embed = self.build_embed(
            f"💰 **Cash Out f F{self.floor}** — +`{profit:,}` 🪙 ({self.multiplier:.2f}x)",
            discord.Color.green(),
        )
        await it.response.edit_message(embed=embed, view=self)
        self.stop()


# ═══════════════════════════════════════════════════════════════════
# ─── ROULETTE BET VIEW
# ═══════════════════════════════════════════════════════════════════
class RouletteBetView(discord.ui.View):
    def __init__(self, user_id, amount, data):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.amount = amount
        self.data = data

    async def interaction_check(self, it):
        if it.user.id != self.user_id:
            await it.response.send_message("❌ Machi dyalek!", ephemeral=True)
            return False
        return True

    async def _spin(self, it, choice, mult):
        await it.response.send_message("🎡 **Kan-spin...**")
        await asyncio.sleep(0.4)
        emojis = ["🔴", "⚫", "🟢"]
        for _ in range(6):
            await asyncio.sleep(0.25)
            try:
                await it.edit_original_response(content=f"🎡 {random.choice(emojis)}")
            except Exception:
                break

        number = random.randint(0, 36)
        if number == 0:
            result = "green"
        elif 1 <= number <= 18:
            result = "red"
        else:
            result = "black"
        emoji = {"red": "🔴", "black": "⚫", "green": "🟢"}[result]

        if result == choice:
            win = self.amount * mult
            self.data["balance"] += win
            _save_economy()
            final = f"🎉 **{emoji} {number} ({result.upper()})** — +`{win:,}` 🪙 ({mult}x)"
            color = discord.Color.green()
        else:
            self.data["balance"] -= self.amount
            _save_economy()
            final = f"😢 **{emoji} {number} ({result.upper()})** — -`{self.amount:,}` 🪙"
            color = discord.Color.red()

        embed = discord.Embed(title="🎡 Roulette Result", description=final, color=color)
        try:
            await it.edit_original_response(content=None, embed=embed)
        except Exception:
            pass
        self.stop()

    @discord.ui.button(label="Red", emoji="🔴", style=discord.ButtonStyle.danger)
    async def red_btn(self, it, b):
        await self._spin(it, "red", 2)

    @discord.ui.button(label="Black", emoji="⚫", style=discord.ButtonStyle.secondary)
    async def black_btn(self, it, b):
        await self._spin(it, "black", 2)

    @discord.ui.button(label="Green", emoji="🟢", style=discord.ButtonStyle.success)
    async def green_btn(self, it, b):
        await self._spin(it, "green", 14)


async def setup(bot):
    await bot.add_cog(Gambling(bot))