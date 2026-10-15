# cogs/banking.py
# =====================================================================
# ─── BANKING SYSTEM KAMEL — Loans / Businesses / Stocks / Crypto /
#     Savings / Credit / Transactions / Interest / Auctions / Pools
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import random
import uuid
from datetime import datetime, timedelta

from data_manager import (
    ECONOMY, save_economy as _save_economy,
    BANKING, save_banking,
    MARKET, save_market,
)


# ═══════════════════════════════════════════════════════════════════
# ─── CONFIG
# ═══════════════════════════════════════════════════════════════════
BANK_INTEREST_RATE   = 0.005
LOAN_BASE_INTEREST   = 0.05
LOAN_MAX_MULTIPLIER  = 3
LOAN_TERM_DAYS       = 7
SAVINGS_INTEREST     = 0.02
SAVINGS_LOCK_HOURS   = 24
TRANSACTION_LOG_MAX  = 50

CREDIT_MIN   = 300
CREDIT_MAX   = 850
CREDIT_START = 700

COIN = "🪙"


# ═══════════════════════════════════════════════════════════════════
# ─── BUSINESSES CATALOG
# ═══════════════════════════════════════════════════════════════════
BUSINESSES = {
    "food_stand": {
        "name": "🍔 Food Stand", "price": 5_000, "income": 200,
        "upgrade_cost": 3_000, "max_level": 10, "min_credit": 600,
    },
    "coffee_shop": {
        "name": "☕ Coffee Shop", "price": 15_000, "income": 600,
        "upgrade_cost": 10_000, "max_level": 10, "min_credit": 650,
    },
    "restaurant": {
        "name": "🍽️ Restaurant", "price": 50_000, "income": 2_500,
        "upgrade_cost": 35_000, "max_level": 10, "min_credit": 700,
    },
    "tech_startup": {
        "name": "💻 Tech Startup", "price": 150_000, "income": 8_000,
        "upgrade_cost": 100_000, "max_level": 10, "min_credit": 750,
    },
    "real_estate": {
        "name": "🏢 Real Estate", "price": 500_000, "income": 30_000,
        "upgrade_cost": 350_000, "max_level": 10, "min_credit": 800,
    },
    "casino_chain": {
        "name": "🎰 Casino Chain", "price": 1_500_000, "income": 100_000,
        "upgrade_cost": 1_000_000, "max_level": 10, "min_credit": 820,
    },
}

# ═══════════════════════════════════════════════════════════════════
# ─── STOCKS + CRYPTO
# ═══════════════════════════════════════════════════════════════════
DEFAULT_STOCKS = {
    "DISC": {"name": "Discord Inc.", "price": 150.0,  "volatility": 0.03},
    "GOGL": {"name": "Google",       "price": 2800.0, "volatility": 0.025},
    "APPL": {"name": "Apple",        "price": 180.0,  "volatility": 0.02},
    "MSFT": {"name": "Microsoft",    "price": 380.0,  "volatility": 0.02},
    "AMZN": {"name": "Amazon",       "price": 150.0,  "volatility": 0.03},
    "TSLA": {"name": "Tesla",        "price": 240.0,  "volatility": 0.05},
    "NVDA": {"name": "NVIDIA",       "price": 500.0,  "volatility": 0.045},
    "MEME": {"name": "Meme Corp",    "price": 5.0,    "volatility": 0.15},
}

DEFAULT_CRYPTOS = {
    "BTC":  {"name": "Bitcoin",    "price": 43_000.0, "volatility": 0.06},
    "ETH":  {"name": "Ethereum",   "price": 2_200.0,  "volatility": 0.07},
    "SOL":  {"name": "Solana",     "price": 95.0,     "volatility": 0.09},
    "DOGE": {"name": "Dogecoin",   "price": 0.08,     "volatility": 0.15},
    "XRP":  {"name": "Ripple",     "price": 0.60,     "volatility": 0.10},
    "KHK":  {"name": "KhokhoCoin", "price": 1.0,      "volatility": 0.20},
}


# ═══════════════════════════════════════════════════════════════════
# ─── MARKET INIT
# ═══════════════════════════════════════════════════════════════════
def _init_market():
    changed = False
    if "stocks" not in MARKET:
        MARKET["stocks"] = {
            s: {"name": d["name"], "price": d["price"], "volatility": d["volatility"]}
            for s, d in DEFAULT_STOCKS.items()
        }
        changed = True
    if "crypto" not in MARKET:
        MARKET["crypto"] = {
            s: {"name": d["name"], "price": d["price"], "volatility": d["volatility"]}
            for s, d in DEFAULT_CRYPTOS.items()
        }
        changed = True
    if changed:
        save_market()


def _market(section: str) -> dict:
    _init_market()
    return MARKET[section]


# ═══════════════════════════════════════════════════════════════════
# ─── HELPERS
# ═══════════════════════════════════════════════════════════════════
def _get_eco(gid: int, uid: int) -> dict:
    ECONOMY.setdefault(gid, {}).setdefault(uid, {
        "balance": 0, "bank": 0, "inventory": [],
    })
    return ECONOMY[gid][uid]


def _get_bank(gid: int, uid: int) -> dict:
    BANKING.setdefault(gid, {}).setdefault(uid, {
        "loans": [],
        "businesses": [],
        "stocks": {},
        "crypto": {},
        "savings": 0.0,
        "savings_locked_until": None,
        "last_interest_claim": None,
        "credit_score": CREDIT_START,
        "transactions": [],
        "total_loans_taken": 0,
        "total_loans_paid": 0,
        "loans_defaulted": 0,
    })
    return BANKING[gid][uid]


def _log_tx(bank: dict, tx_type: str, amount: float, note: str = ""):
    bank["transactions"].append({
        "type": tx_type, "amount": amount,
        "note": note, "time": datetime.now().isoformat(),
    })
    if len(bank["transactions"]) > TRANSACTION_LOG_MAX:
        bank["transactions"] = bank["transactions"][-TRANSACTION_LOG_MAX:]


def _recalc_credit(bank: dict) -> int:
    score = CREDIT_START
    score += min(bank["total_loans_paid"] * 5, 100)
    score -= bank["loans_defaulted"] * 50
    active = [l for l in bank["loans"] if l["paid"] < l["amount_due"]]
    score -= len(active) * 20
    score += min(len(bank["businesses"]) * 10, 40)
    score = max(CREDIT_MIN, min(CREDIT_MAX, score))
    bank["credit_score"] = score
    return score


def _net_worth(eco: dict, bank: dict) -> float:
    stocks_val = sum(
        h["shares"] * _market("stocks").get(s, {}).get("price", h["avg_price"])
        for s, h in bank["stocks"].items()
    )
    crypto_val = sum(
        h["amount"] * _market("crypto").get(s, {}).get("price", h["avg_price"])
        for s, h in bank["crypto"].items()
    )
    biz_val = sum(
        BUSINESSES.get(b["type"], {}).get("price", 0) * (b["level"] ** 0.8)
        for b in bank["businesses"]
    )
    return (
        eco.get("balance", 0) + eco.get("bank", 0)
        + bank["savings"] + stocks_val + crypto_val + biz_val
    )


def _max_loan(eco: dict, bank: dict) -> float:
    nw = _net_worth(eco, bank)
    credit_ratio = (bank["credit_score"] - CREDIT_MIN) / (CREDIT_MAX - CREDIT_MIN)
    cap = nw * LOAN_MAX_MULTIPLIER * (0.4 + 0.6 * credit_ratio)
    unpaid = sum(l["amount_due"] - l["paid"] for l in bank["loans"] if l["paid"] < l["amount_due"])
    return max(0.0, cap - unpaid)


def _fmt(n) -> str:
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)


# ═══════════════════════════════════════════════════════════════════
# ─── COG
# ═══════════════════════════════════════════════════════════════════
class Banking(commands.Cog):
    """Banking Kamel — Loans / Businesses / Stocks / Crypto / Savings"""

    def __init__(self, bot):
        self.bot = bot
        _init_market()
        self.market_loop.start()
        self.interest_loop.start()
        self.loan_check_loop.start()

    def cog_unload(self):
        self.market_loop.cancel()
        self.interest_loop.cancel()
        self.loan_check_loop.cancel()

    # ═══════════════════════════════════════════════════════════
    # ─── LOOPS
    # ═══════════════════════════════════════════════════════════
    @tasks.loop(minutes=5)
    async def market_loop(self):
        try:
            for section in ("stocks", "crypto"):
                for sym, data in _market(section).items():
                    vol = data["volatility"]
                    change = random.gauss(0, vol)
                    new_price = data["price"] * (1 + change)
                    floor = data["price"] * 0.75
                    ceil  = data["price"] * 1.25
                    new_price = max(floor, min(ceil, new_price))
                    data["price"] = round(max(0.01, new_price), 4)
            save_market()
        except Exception as e:
            print(f"❌ Market loop: {e}")

    @market_loop.before_loop
    async def before_market(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24)
    async def interest_loop(self):
        try:
            for gid, users in BANKING.items():
                for uid, bank in users.items():
                    if bank.get("last_interest_claim"):
                        continue
                    eco = ECONOMY.get(gid, {}).get(uid)
                    if not eco or eco.get("bank", 0) <= 0:
                        continue
                    interest = int(eco["bank"] * BANK_INTEREST_RATE)
                    if interest <= 0:
                        continue
                    eco["bank"] += interest
                    _log_tx(bank, "bank_interest", interest, "Daily bank interest")
                _save_economy()
                save_banking()
        except Exception as e:
            print(f"❌ Interest loop: {e}")

    @interest_loop.before_loop
    async def before_interest(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=1)
    async def loan_check_loop(self):
        try:
            now = datetime.now()
            changed = False
            for gid, users in BANKING.items():
                for uid, bank in users.items():
                    for loan in bank["loans"]:
                        if loan["paid"] >= loan["amount_due"]:
                            continue
                        try:
                            due = datetime.fromisoformat(loan["due_at"])
                        except Exception:
                            continue
                        if now > due:
                            loan["defaulted"] = True
                            bank["loans_defaulted"] += 1
                            _log_tx(bank, "loan_default", loan["amount_due"] - loan["paid"],
                                    f"Loan {loan['id']} defaulted")
                            changed = True
                    _recalc_credit(bank)
            if changed:
                save_banking()
        except Exception as e:
            print(f"❌ Loan check: {e}")

    @loan_check_loop.before_loop
    async def before_loans(self):
        await self.bot.wait_until_ready()

    # ═══════════════════════════════════════════════════════════
    # ─── /bank
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="bank", description="🏦 Dashboard dyal bank dyalk")
    @app_commands.describe(member="L-user (optionnel)")
    async def bank(self, it: discord.Interaction, member: discord.Member = None):
        member = member or it.user
        eco = _get_eco(it.guild.id, member.id)
        b = _get_bank(it.guild.id, member.id)

        nw = _net_worth(eco, b)
        active_loans = [l for l in b["loans"] if l["paid"] < l["amount_due"]]

        embed = discord.Embed(
            title=f"🏦 Bank — {member.display_name}",
            color=discord.Color.gold(),
            timestamp=datetime.now(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="👛 Wallet", value=f"`{_fmt(eco['balance'])}` {COIN}", inline=True)
        embed.add_field(name="🏦 Bank", value=f"`{_fmt(eco['bank'])}` {COIN}", inline=True)
        embed.add_field(name="💎 Savings", value=f"`{_fmt(b['savings'])}` {COIN}", inline=True)

        embed.add_field(name="📊 Net Worth", value=f"`{_fmt(nw)}` {COIN}", inline=True)
        embed.add_field(name="🎖️ Credit", value=f"`{b['credit_score']}`", inline=True)
        embed.add_field(name="📉 Loans", value=f"`{len(active_loans)}`", inline=True)

        if b["businesses"]:
            total_income = sum(
                BUSINESSES[bz["type"]]["income"] * bz["level"]
                for bz in b["businesses"]
            )
            embed.add_field(
                name=f"🏢 Businesses ({len(b['businesses'])})",
                value=f"Income: `{_fmt(total_income)}` {COIN} / 30min",
                inline=False,
            )
        if b["stocks"] or b["crypto"]:
            embed.add_field(
                name="📈 Portfolio",
                value=f"Stocks: `{len(b['stocks'])}` • Crypto: `{len(b['crypto'])}`",
                inline=False,
            )

        embed.set_footer(text="St3mel /loan /business /stocks /crypto /savings")
        await it.response.send_message(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /loan GROUP (slash)
    # ═══════════════════════════════════════════════════════════
    loan_group = app_commands.Group(name="loan", description="💰 Loans system")

    @loan_group.command(name="take", description="Khoud loan")
    @app_commands.describe(amount="Ch7al bghiti tsellef")
    async def loan_take(self, it: discord.Interaction, amount: int):
        if amount < 100:
            return await it.response.send_message("❌ Minimum loan: `100` 🪙", ephemeral=True)

        eco = _get_eco(it.guild.id, it.user.id)
        b = _get_bank(it.guild.id, it.user.id)
        _recalc_credit(b)

        max_amt = int(_max_loan(eco, b))
        if amount > max_amt:
            return await it.response.send_message(
                f"❌ Max loan dyalek: `{_fmt(max_amt)}` {COIN}\n"
                f"🎖️ Credit: `{b['credit_score']}`",
                ephemeral=True,
            )

        interest = int(amount * LOAN_BASE_INTEREST)
        amount_due = amount + interest
        loan_id = f"L{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now()

        b["loans"].append({
            "id": loan_id,
            "principal": amount,
            "interest": interest,
            "amount_due": amount_due,
            "paid": 0,
            "taken_at": now.isoformat(),
            "due_at": (now + timedelta(days=LOAN_TERM_DAYS)).isoformat(),
            "defaulted": False,
        })
        b["total_loans_taken"] += 1
        eco["balance"] += amount
        _log_tx(b, "loan_take", amount, f"Loan {loan_id}")
        _recalc_credit(b)

        _save_economy()
        save_banking()

        embed = discord.Embed(
            title="💰 Loan Approved!",
            color=discord.Color.green(),
            timestamp=now,
        )
        embed.add_field(name="🆔 Loan ID", value=f"`{loan_id}`", inline=True)
        embed.add_field(name="💵 Amount", value=f"`{_fmt(amount)}` {COIN}", inline=True)
        embed.add_field(name="📈 Interest", value=f"`{_fmt(interest)}` {COIN}", inline=True)
        embed.add_field(name="💸 Total Due", value=f"`{_fmt(amount_due)}` {COIN}", inline=False)
        embed.add_field(name="⏰ Due", value=f"<t:{int((now + timedelta(days=LOAN_TERM_DAYS)).timestamp())}:R>", inline=False)
        embed.set_footer(text=f"Credit: {b['credit_score']}")
        await it.response.send_message(embed=embed)

    @loan_group.command(name="pay", description="Khalles loan")
    @app_commands.describe(loan_id="ID dyal loan (wla 'all')", amount="Ch7al bghiti tkhalles")
    async def loan_pay(self, it: discord.Interaction, loan_id: str, amount: int):
        if amount <= 0:
            return await it.response.send_message("❌ Amount khass > 0!", ephemeral=True)

        eco = _get_eco(it.guild.id, it.user.id)
        b = _get_bank(it.guild.id, it.user.id)

        if loan_id.lower() == "all":
            loans = [l for l in b["loans"] if l["paid"] < l["amount_due"]]
            if not loans:
                return await it.response.send_message("❌ Ma 3endekch loans!", ephemeral=True)
            if amount > eco["balance"]:
                return await it.response.send_message("❌ Ma 3endekch flous kafyin!", ephemeral=True)
            paid_total = 0
            for l in loans:
                remaining = l["amount_due"] - l["paid"]
                pay = min(amount - paid_total, remaining)
                if pay <= 0:
                    break
                l["paid"] += pay
                paid_total += pay
                if l["paid"] >= l["amount_due"]:
                    b["total_loans_paid"] += 1
            eco["balance"] -= paid_total
            _log_tx(b, "loan_pay", -paid_total, f"Paid all loans")
            _recalc_credit(b)
            _save_economy()
            save_banking()
            return await it.response.send_message(
                f"✅ Khallesti `{_fmt(paid_total)}` {COIN}!\n"
                f"🎖️ Credit: `{b['credit_score']}`"
            )

        loan = next((l for l in b["loans"] if l["id"] == loan_id.upper()), None)
        if not loan:
            return await it.response.send_message(f"❌ Loan `{loan_id}` ma kaynch!", ephemeral=True)
        if loan["paid"] >= loan["amount_due"]:
            return await it.response.send_message("❌ Had loan deja mkhelles!", ephemeral=True)

        remaining = loan["amount_due"] - loan["paid"]
        if amount > eco["balance"]:
            return await it.response.send_message("❌ Ma 3endekch flous kafyin!", ephemeral=True)

        pay = min(amount, remaining)
        loan["paid"] += pay
        eco["balance"] -= pay
        _log_tx(b, "loan_pay", -pay, f"Loan {loan['id']}")

        if loan["paid"] >= loan["amount_due"]:
            b["total_loans_paid"] += 1
        _recalc_credit(b)
        _save_economy()
        save_banking()

        embed = discord.Embed(
            title="✅ Loan Payment",
            color=discord.Color.green(),
        )
        embed.add_field(name="🆔 Loan", value=f"`{loan['id']}`", inline=True)
        embed.add_field(name="💸 Paid", value=f"`{_fmt(pay)}` {COIN}", inline=True)
        embed.add_field(name="💰 Remaining", value=f"`{_fmt(loan['amount_due'] - loan['paid'])}` {COIN}", inline=True)
        if loan["paid"] >= loan["amount_due"]:
            embed.add_field(name="🎉", value="**Loan mkhelles kamel!**", inline=False)
        embed.set_footer(text=f"Credit: {b['credit_score']}")
        await it.response.send_message(embed=embed)

    @loan_group.command(name="info", description="Chouf loans dyalk")
    async def loan_info(self, it: discord.Interaction):
        b = _get_bank(it.guild.id, it.user.id)
        active = [l for l in b["loans"] if l["paid"] < l["amount_due"]]
        paid = [l for l in b["loans"] if l["paid"] >= l["amount_due"]]

        embed = discord.Embed(
            title="💰 Loans",
            color=discord.Color.gold(),
        )
        embed.add_field(name="🎖️ Credit Score", value=f"`{b['credit_score']}`", inline=True)
        embed.add_field(name="✅ Paid", value=f"`{len(paid)}`", inline=True)
        embed.add_field(name="⚠️ Active", value=f"`{len(active)}`", inline=True)

        if active:
            lines = []
            for l in active[:5]:
                try:
                    due = datetime.fromisoformat(l["due_at"])
                    ts = int(due.timestamp())
                except Exception:
                    ts = 0
                rem = l["amount_due"] - l["paid"]
                lines.append(
                    f"**`{l['id']}`** — `{_fmt(rem)}` {COIN} due <t:{ts}:R>"
                )
            embed.add_field(name="⚠️ Active Loans", value="\n".join(lines), inline=False)

        if b["loans_defaulted"]:
            embed.add_field(name="❌ Defaulted", value=f"`{b['loans_defaulted']}`", inline=True)

        await it.response.send_message(embed=embed, ephemeral=True)

    # ═══════════════════════════════════════════════════════════
    # ─── /business GROUP
    # ═══════════════════════════════════════════════════════════
    biz_group = app_commands.Group(name="business", description="🏢 Business system")

    @biz_group.command(name="list", description="List dyal businesses")
    async def biz_list(self, it: discord.Interaction):
        embed = discord.Embed(
            title="🏢 Businesses",
            description="Chri business → passive income kola 30min.",
            color=discord.Color.blurple(),
        )
        for key, data in BUSINESSES.items():
            embed.add_field(
                name=f"{data['name']} — `{key}`",
                value=(
                    f"💵 Price: `{_fmt(data['price'])}` {COIN}\n"
                    f"💰 Income: `{_fmt(data['income'])}` {COIN} / 30min\n"
                    f"🎖️ Min Credit: `{data['min_credit']}`"
                ),
                inline=False,
            )
        await it.response.send_message(embed=embed)

    @biz_group.command(name="buy", description="Chri business")
    @app_commands.describe(biz_type="Type dyal business (chouf /business list)")
    async def biz_buy(self, it: discord.Interaction, biz_type: str):
        biz_type = biz_type.lower()
        biz = BUSINESSES.get(biz_type)
        if not biz:
            return await it.response.send_message("❌ Business ma kaynch! Chouf `/business list`.", ephemeral=True)

        eco = _get_eco(it.guild.id, it.user.id)
        b = _get_bank(it.guild.id, it.user.id)

        if eco["balance"] + eco["bank"] < biz["price"]:
            return await it.response.send_message(
                f"❌ Khass `{_fmt(biz['price'])}` {COIN}", ephemeral=True
            )
        if b["credit_score"] < biz["min_credit"]:
            return await it.response.send_message(
                f"❌ Credit dyalek `{b['credit_score']}` — khass `{biz['min_credit']}`",
                ephemeral=True,
            )

        cost = biz["price"]
        if eco["balance"] >= cost:
            eco["balance"] -= cost
        else:
            rem = cost - eco["balance"]
            eco["balance"] = 0
            eco["bank"] -= rem

        biz_id = f"B{uuid.uuid4().hex[:6].upper()}"
        b["businesses"].append({
            "id": biz_id,
            "type": biz_type,
            "level": 1,
            "bought_at": datetime.now().isoformat(),
            "last_collect": None,
        })
        _log_tx(b, "business_buy", -cost, f"{biz['name']} ({biz_id})")
        _recalc_credit(b)
        _save_economy()
        save_banking()

        embed = discord.Embed(
            title=f"✅ {biz['name']} tsayeb!",
            color=discord.Color.green(),
        )
        embed.add_field(name="🆔 ID", value=f"`{biz_id}`", inline=True)
        embed.add_field(name="💵 Cost", value=f"`{_fmt(cost)}` {COIN}", inline=True)
        embed.add_field(name="💰 Income", value=f"`{_fmt(biz['income'])}` {COIN} / 30min", inline=True)
        embed.set_footer(text="St3mel /business collect")
        await it.response.send_message(embed=embed)

    @biz_group.command(name="collect", description="Jme3 income mn businesses")
    async def biz_collect(self, it: discord.Interaction):
        eco = _get_eco(it.guild.id, it.user.id)
        b = _get_bank(it.guild.id, it.user.id)

        if not b["businesses"]:
            return await it.response.send_message("❌ Ma 3endekch businesses!", ephemeral=True)

        now = datetime.now()
        total = 0
        collected = []

        for biz in b["businesses"]:
            data = BUSINESSES.get(biz["type"])
            if not data:
                continue
            last = biz.get("last_collect")
            if last:
                try:
                    last_dt = datetime.fromisoformat(last)
                except Exception:
                    last_dt = now - timedelta(minutes=30)
            else:
                last_dt = now - timedelta(minutes=30)

            elapsed_min = (now - last_dt).total_seconds() / 60
            periods = int(elapsed_min // 30)
            if periods <= 0:
                continue

            earned = data["income"] * biz["level"] * periods
            total += earned
            collected.append((data["name"], biz["level"], periods, earned))
            biz["last_collect"] = now.isoformat()

        if total <= 0:
            next_ts = []
            for biz in b["businesses"]:
                last = biz.get("last_collect")
                if last:
                    try:
                        last_dt = datetime.fromisoformat(last)
                        next_ts.append(last_dt + timedelta(minutes=30))
                    except Exception:
                        pass
            txt = "⏰ Ba9i ma 3endekch income. 3awed mn ba3d 30min."
            if next_ts:
                soonest = min(next_ts)
                txt = f"⏰ 3awed mn ba3d <t:{int(soonest.timestamp())}:R>!"
            return await it.response.send_message(txt, ephemeral=True)

        eco["balance"] += total
        _log_tx(b, "business_collect", total, f"{len(collected)} businesses")
        _save_economy()
        save_banking()

        lines = [f"• {n} (Lv{bz}) ×{p} → `{_fmt(e)}` {COIN}" for n, bz, p, e in collected]
        embed = discord.Embed(
            title="💰 Business Collect!",
            description=f"**+{_fmt(total)}** {COIN} dkhlou l-wallet!",
            color=discord.Color.green(),
        )
        embed.add_field(name="📋 Details", value="\n".join(lines[:10]), inline=False)
        await it.response.send_message(embed=embed)

    @biz_group.command(name="upgrade", description="Upgrade business")
    @app_commands.describe(biz_id="ID dyal business")
    async def biz_upgrade(self, it: discord.Interaction, biz_id: str):
        eco = _get_eco(it.guild.id, it.user.id)
        b = _get_bank(it.guild.id, it.user.id)

        biz = next((x for x in b["businesses"] if x["id"] == biz_id.upper()), None)
        if not biz:
            return await it.response.send_message("❌ Business ma kaynch!", ephemeral=True)

        data = BUSINESSES.get(biz["type"])
        if biz["level"] >= data["max_level"]:
            return await it.response.send_message("❌ Max level reached!", ephemeral=True)

        cost = data["upgrade_cost"] * biz["level"]
        if eco["balance"] + eco["bank"] < cost:
            return await it.response.send_message(
                f"❌ Khass `{_fmt(cost)}` {COIN} l upgrade!", ephemeral=True
            )

        if eco["balance"] >= cost:
            eco["balance"] -= cost
        else:
            rem = cost - eco["balance"]
            eco["balance"] = 0
            eco["bank"] -= rem

        biz["level"] += 1
        _log_tx(b, "business_upgrade", -cost, f"{data['name']} → Lv{biz['level']}")
        _save_economy()
        save_banking()

        await it.response.send_message(
            f"✅ **{data['name']}** upgraded l **Lv{biz['level']}**!\n"
            f"💰 Income daba: `{_fmt(data['income'] * biz['level'])}` {COIN} / 30min"
        )

    @biz_group.command(name="sell", description="Bi3 business (50% value)")
    @app_commands.describe(biz_id="ID dyal business")
    async def biz_sell(self, it: discord.Interaction, biz_id: str):
        eco = _get_eco(it.guild.id, it.user.id)
        b = _get_bank(it.guild.id, it.user.id)

        biz = next((x for x in b["businesses"] if x["id"] == biz_id.upper()), None)
        if not biz:
            return await it.response.send_message("❌ Business ma kaynch!", ephemeral=True)

        data = BUSINESSES[biz["type"]]
        val = data["price"] + (data["upgrade_cost"] * (biz["level"] - 1))
        payout = int(val * 0.5)
        eco["balance"] += payout
        b["businesses"].remove(biz)
        _log_tx(b, "business_sell", payout, f"{data['name']}")
        _recalc_credit(b)
        _save_economy()
        save_banking()

        await it.response.send_message(
            f"💸 Bi3ti **{data['name']}** b `{_fmt(payout)}` {COIN} (50% value)"
        )

    # ═══════════════════════════════════════════════════════════
    # ─── /stocks GROUP
    # ═══════════════════════════════════════════════════════════
    stocks_group = app_commands.Group(name="stocks", description="📈 Stock market")

    @stocks_group.command(name="list", description="Chouf l-market")
    async def stocks_list(self, it: discord.Interaction):
        stocks = _market("stocks")
        embed = discord.Embed(
            title="📈 Stock Market",
            description="Prices update kola 5 min.",
            color=discord.Color.green(),
            timestamp=datetime.now(),
        )
        for sym, d in stocks.items():
            embed.add_field(
                name=f"`{sym}` — {d['name']}",
                value=f"💵 `{d['price']:,.2f}` {COIN}",
                inline=True,
            )
        await it.response.send_message(embed=embed)

    @stocks_group.command(name="buy", description="Chri stocks")
    @app_commands.describe(symbol="Symbol (ex: DISC)", shares="Ch7al mn share")
    async def stocks_buy(self, it: discord.Interaction, symbol: str, shares: int):
        symbol = symbol.upper()
        stocks = _market("stocks")
        if symbol not in stocks:
            return await it.response.send_message("❌ Symbol ghalat! Chouf `/stocks list`.", ephemeral=True)
        if shares <= 0:
            return await it.response.send_message("❌ Shares > 0!", ephemeral=True)

        data = stocks[symbol]
        cost = data["price"] * shares
        eco = _get_eco(it.guild.id, it.user.id)

        if eco["balance"] < cost:
            return await it.response.send_message(
                f"❌ Khass `{_fmt(cost)}` {COIN} (3endek `{_fmt(eco['balance'])}`)",
                ephemeral=True,
            )

        b = _get_bank(it.guild.id, it.user.id)
        holding = b["stocks"].get(symbol, {"shares": 0, "avg_price": 0.0})
        new_total = holding["shares"] + shares
        holding["avg_price"] = (
            (holding["avg_price"] * holding["shares"] + data["price"] * shares) / new_total
        )
        holding["shares"] = new_total
        b["stocks"][symbol] = holding
        eco["balance"] -= cost
        _log_tx(b, "stock_buy", -cost, f"{shares}x {symbol} @ {data['price']:.2f}")

        _save_economy()
        save_banking()

        await it.response.send_message(
            f"✅ Chriti `{shares}x` **{symbol}** @ `{data['price']:,.2f}` {COIN}\n"
            f"💵 Cost: `{_fmt(cost)}` {COIN}"
        )

    @stocks_group.command(name="sell", description="Bi3 stocks")
    @app_commands.describe(symbol="Symbol", shares="Ch7al mn share")
    async def stocks_sell(self, it: discord.Interaction, symbol: str, shares: int):
        symbol = symbol.upper()
        stocks = _market("stocks")
        if symbol not in stocks:
            return await it.response.send_message("❌ Symbol ghalat!", ephemeral=True)

        b = _get_bank(it.guild.id, it.user.id)
        eco = _get_eco(it.guild.id, it.user.id)
        holding = b["stocks"].get(symbol)

        if not holding or holding["shares"] < shares:
            return await it.response.send_message("❌ Ma 3endekch shares kafyin!", ephemeral=True)
        if shares <= 0:
            return await it.response.send_message("❌ Shares > 0!", ephemeral=True)

        data = stocks[symbol]
        revenue = data["price"] * shares
        profit = (data["price"] - holding["avg_price"]) * shares

        holding["shares"] -= shares
        if holding["shares"] == 0:
            del b["stocks"][symbol]

        eco["balance"] += revenue
        _log_tx(b, "stock_sell", revenue, f"{shares}x {symbol} @ {data['price']:.2f}")

        _save_economy()
        save_banking()

        emoji = "📈" if profit >= 0 else "📉"
        await it.response.send_message(
            f"{emoji} Bi3ti `{shares}x` **{symbol}** @ `{data['price']:,.2f}` {COIN}\n"
            f"💰 Revenue: `{_fmt(revenue)}` {COIN}\n"
            f"{'💚 Profit' if profit >= 0 else '❤️ Loss'}: `{_fmt(abs(profit))}` {COIN}"
        )

    @stocks_group.command(name="portfolio", description="Chouf stocks dyalk")
    async def stocks_portfolio(self, it: discord.Interaction):
        b = _get_bank(it.guild.id, it.user.id)
        if not b["stocks"]:
            return await it.response.send_message("❌ Ma 3endekch stocks!", ephemeral=True)

        stocks = _market("stocks")
        embed = discord.Embed(title="📊 Stock Portfolio", color=discord.Color.green())
        total_val = 0
        total_cost = 0

        for sym, h in b["stocks"].items():
            if sym not in stocks:
                continue
            price = stocks[sym]["price"]
            val = price * h["shares"]
            cost = h["avg_price"] * h["shares"]
            profit = val - cost
            total_val += val
            total_cost += cost

            emoji = "📈" if profit >= 0 else "📉"
            embed.add_field(
                name=f"{emoji} `{sym}` ×{h['shares']}",
                value=(
                    f"Value: `{_fmt(val)}` {COIN}\n"
                    f"P/L: `{_fmt(profit)}` {COIN} ({profit/cost*100:+.1f}%)"
                    if cost else "N/A"
                ),
                inline=True,
            )

        total_pl = total_val - total_cost
        embed.set_footer(text=f"Total: {_fmt(total_val)} 🪙 • P/L: {_fmt(total_pl)} 🪙")
        await it.response.send_message(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /crypto GROUP
    # ═══════════════════════════════════════════════════════════
    crypto_group = app_commands.Group(name="crypto", description="🪙 Crypto market")

    @crypto_group.command(name="list", description="Chouf crypto market")
    async def crypto_list(self, it: discord.Interaction):
        cryptos = _market("crypto")
        embed = discord.Embed(
            title="🪙 Crypto Market",
            description="⚠️ High volatility! Prices update kola 5 min.",
            color=discord.Color.orange(),
            timestamp=datetime.now(),
        )
        for sym, d in cryptos.items():
            embed.add_field(
                name=f"`{sym}` — {d['name']}",
                value=f"💵 `{d['price']:,.4f}` {COIN}",
                inline=True,
            )
        await it.response.send_message(embed=embed)

    @crypto_group.command(name="buy", description="Chri crypto")
    @app_commands.describe(symbol="Symbol (ex: BTC)", amount="Ch7al (decimal ok)")
    async def crypto_buy(self, it: discord.Interaction, symbol: str, amount: float):
        symbol = symbol.upper()
        cryptos = _market("crypto")
        if symbol not in cryptos:
            return await it.response.send_message("❌ Symbol ghalat!", ephemeral=True)
        if amount <= 0:
            return await it.response.send_message("❌ Amount > 0!", ephemeral=True)

        data = cryptos[symbol]
        cost = data["price"] * amount
        eco = _get_eco(it.guild.id, it.user.id)

        if eco["balance"] < cost:
            return await it.response.send_message(f"❌ Khass `{_fmt(cost)}` {COIN}", ephemeral=True)

        b = _get_bank(it.guild.id, it.user.id)
        holding = b["crypto"].get(symbol, {"amount": 0.0, "avg_price": 0.0})
        new_total = holding["amount"] + amount
        holding["avg_price"] = (
            (holding["avg_price"] * holding["amount"] + data["price"] * amount) / new_total
        )
        holding["amount"] = new_total
        b["crypto"][symbol] = holding
        eco["balance"] -= cost
        _log_tx(b, "crypto_buy", -cost, f"{amount} {symbol} @ {data['price']:.4f}")

        _save_economy()
        save_banking()
        await it.response.send_message(
            f"✅ Chriti `{amount}` **{symbol}** @ `{data['price']:,.4f}` {COIN}\n"
            f"💵 Cost: `{_fmt(cost)}` {COIN}"
        )

    @crypto_group.command(name="sell", description="Bi3 crypto")
    @app_commands.describe(symbol="Symbol", amount="Ch7al (decimal ok)")
    async def crypto_sell(self, it: discord.Interaction, symbol: str, amount: float):
        symbol = symbol.upper()
        cryptos = _market("crypto")
        if symbol not in cryptos:
            return await it.response.send_message("❌ Symbol ghalat!", ephemeral=True)

        b = _get_bank(it.guild.id, it.user.id)
        eco = _get_eco(it.guild.id, it.user.id)
        h = b["crypto"].get(symbol)
        if not h or h["amount"] < amount:
            return await it.response.send_message("❌ Ma 3endekch kafyin!", ephemeral=True)

        data = cryptos[symbol]
        revenue = data["price"] * amount
        profit = (data["price"] - h["avg_price"]) * amount
        h["amount"] -= amount
        if h["amount"] <= 1e-9:
            del b["crypto"][symbol]

        eco["balance"] += revenue
        _log_tx(b, "crypto_sell", revenue, f"{amount} {symbol} @ {data['price']:.4f}")

        _save_economy()
        save_banking()

        emoji = "📈" if profit >= 0 else "📉"
        await it.response.send_message(
            f"{emoji} Bi3ti `{amount}` **{symbol}** @ `{data['price']:,.4f}` {COIN}\n"
            f"💰 Revenue: `{_fmt(revenue)}` {COIN}\n"
            f"{'💚 Profit' if profit >= 0 else '❤️ Loss'}: `{_fmt(abs(profit))}` {COIN}"
        )

    @crypto_group.command(name="portfolio", description="Chouf crypto dyalk")
    async def crypto_portfolio(self, it: discord.Interaction):
        b = _get_bank(it.guild.id, it.user.id)
        if not b["crypto"]:
            return await it.response.send_message("❌ Ma 3endekch crypto!", ephemeral=True)

        cryptos = _market("crypto")
        embed = discord.Embed(title="🪙 Crypto Portfolio", color=discord.Color.orange())
        total_val, total_cost = 0, 0

        for sym, h in b["crypto"].items():
            if sym not in cryptos:
                continue
            price = cryptos[sym]["price"]
            val = price * h["amount"]
            cost = h["avg_price"] * h["amount"]
            profit = val - cost
            total_val += val
            total_cost += cost
            emoji = "📈" if profit >= 0 else "📉"
            embed.add_field(
                name=f"{emoji} `{sym}` ×{h['amount']:.4f}",
                value=f"Value: `{_fmt(val)}` {COIN}\nP/L: `{_fmt(profit)}` {COIN}",
                inline=True,
            )

        pl = total_val - total_cost
        embed.set_footer(text=f"Total: {_fmt(total_val)} 🪙 • P/L: {_fmt(pl)} 🪙")
        await it.response.send_message(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /savings
    # ═══════════════════════════════════════════════════════════
    savings_group = app_commands.Group(name="savings", description="💎 Savings account")

    @savings_group.command(name="info", description="Chouf savings dyalk")
    async def savings_info(self, it: discord.Interaction):
        b = _get_bank(it.guild.id, it.user.id)
        embed = discord.Embed(title="💎 Savings Account", color=discord.Color.blue())
        embed.add_field(name="💰 Balance", value=f"`{_fmt(b['savings'])}` {COIN}", inline=True)
        embed.add_field(name="📈 Rate", value=f"`{SAVINGS_INTEREST*100}%` / 24h", inline=True)

        if b.get("savings_locked_until"):
            try:
                until = datetime.fromisoformat(b["savings_locked_until"])
                if until > datetime.now():
                    embed.add_field(
                        name="🔒 Locked until",
                        value=f"<t:{int(until.timestamp())}:R>",
                        inline=False,
                    )
                else:
                    interest = int(b["savings"] * SAVINGS_INTEREST)
                    embed.add_field(
                        name="✅ Ready to withdraw",
                        value=f"Interest: `{_fmt(interest)}` {COIN}",
                        inline=False,
                    )
            except Exception:
                pass
        await it.response.send_message(embed=embed)

    @savings_group.command(name="deposit", description="Zid flous f savings (locked 24h)")
    @app_commands.describe(amount="Ch7al")
    async def savings_deposit(self, it: discord.Interaction, amount: int):
        if amount <= 0:
            return await it.response.send_message("❌ Amount > 0!", ephemeral=True)

        eco = _get_eco(it.guild.id, it.user.id)
        b = _get_bank(it.guild.id, it.user.id)

        if b.get("savings_locked_until"):
            try:
                if datetime.fromisoformat(b["savings_locked_until"]) > datetime.now():
                    return await it.response.send_message("❌ Savings mzl locked!", ephemeral=True)
            except Exception:
                pass

        if eco["balance"] < amount:
            return await it.response.send_message("❌ Ma 3endekch flous kafyin!", ephemeral=True)

        eco["balance"] -= amount
        b["savings"] += amount
        b["savings_locked_until"] = (datetime.now() + timedelta(hours=SAVINGS_LOCK_HOURS)).isoformat()
        _log_tx(b, "savings_deposit", -amount, "Savings deposit")
        _save_economy()
        save_banking()

        await it.response.send_message(
            f"💎 Zidt `{_fmt(amount)}` {COIN} f savings!\n"
            f"🔒 Locked l 24h — interest: `{SAVINGS_INTEREST*100}%`"
        )

    @savings_group.command(name="withdraw", description="Hyed flous mn savings (+ interest)")
    async def savings_withdraw(self, it: discord.Interaction):
        eco = _get_eco(it.guild.id, it.user.id)
        b = _get_bank(it.guild.id, it.user.id)

        if b["savings"] <= 0:
            return await it.response.send_message("❌ Savings khawi!", ephemeral=True)

        if b.get("savings_locked_until"):
            try:
                until = datetime.fromisoformat(b["savings_locked_until"])
                if until > datetime.now():
                    return await it.response.send_message(
                        f"🔒 Locked until <t:{int(until.timestamp())}:R>",
                        ephemeral=True,
                    )
            except Exception:
                pass

        interest = int(b["savings"] * SAVINGS_INTEREST)
        total = b["savings"] + interest
        eco["balance"] += total
        b["savings"] = 0
        b["savings_locked_until"] = None
        _log_tx(b, "savings_withdraw", total, f"Withdrew + interest {interest}")
        _save_economy()
        save_banking()

        await it.response.send_message(
            f"💎 Hyedti `{_fmt(total)}` {COIN}!\n"
            f"💰 Interest: `{_fmt(interest)}` {COIN}"
        )

    # ═══════════════════════════════════════════════════════════
    # ─── /interest
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="interest", description="💰 Jme3 bank interest dyalk")
    async def interest_claim(self, it: discord.Interaction):
        eco = _get_eco(it.guild.id, it.user.id)
        b = _get_bank(it.guild.id, it.user.id)

        if eco["bank"] <= 0:
            return await it.response.send_message("❌ Bank khawi!", ephemeral=True)

        if b.get("last_interest_claim"):
            try:
                last = datetime.fromisoformat(b["last_interest_claim"])
                if datetime.now() - last < timedelta(hours=24):
                    rem = timedelta(hours=24) - (datetime.now() - last)
                    return await it.response.send_message(
                        f"⏰ 3awed mn ba3d `{rem.seconds // 3600}h {(rem.seconds % 3600) // 60}m`!",
                        ephemeral=True,
                    )
            except Exception:
                pass

        amount = int(eco["bank"] * BANK_INTEREST_RATE * 24)
        if amount < 1:
            return await it.response.send_message("❌ Bank balance sghira bezzaf!", ephemeral=True)

        eco["bank"] += amount
        b["last_interest_claim"] = datetime.now().isoformat()
        _log_tx(b, "interest_claim", amount, "Daily interest")
        _save_economy()
        save_banking()

        await it.response.send_message(
            f"💰 **+{_fmt(amount)}** {COIN} interest!\n"
            f"🏦 Bank: `{_fmt(eco['bank'])}` {COIN}"
        )

    # ═══════════════════════════════════════════════════════════
    # ─── /transactions
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="transactions", description="📜 History dyal transactions")
    async def transactions(self, it: discord.Interaction):
        b = _get_bank(it.guild.id, it.user.id)
        if not b["transactions"]:
            return await it.response.send_message("❌ Ma kaynch transactions!", ephemeral=True)

        embed = discord.Embed(title="📜 Transactions (last 15)", color=discord.Color.blurple())
        for tx in reversed(b["transactions"][-15:]):
            try:
                ts = int(datetime.fromisoformat(tx["time"]).timestamp())
            except Exception:
                ts = 0
            amt = tx["amount"]
            emoji = "💚" if amt >= 0 else "❤️"
            embed.add_field(
                name=f"{emoji} `{tx['type']}` — `{_fmt(abs(amt))}` {COIN}",
                value=f"{tx.get('note', '')} • <t:{ts}:R>",
                inline=False,
            )
        await it.response.send_message(embed=embed, ephemeral=True)

    # ═══════════════════════════════════════════════════════════
    # ─── /auction
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="auction", description="🔨 Bda auction")
    @app_commands.describe(
        item="Chno kaytbi3",
        starting_bid="Bid dyal l-bidaya",
        duration_minutes="Ch7al dyal minutes",
    )
    async def auction(self, it: discord.Interaction, item: str, starting_bid: int, duration_minutes: int = 5):
        if starting_bid < 10:
            return await it.response.send_message("❌ Minimum bid: `10`", ephemeral=True)
        if duration_minutes < 1 or duration_minutes > 60:
            return await it.response.send_message("❌ Duration: 1-60 min", ephemeral=True)

        view = AuctionView(it.user.id, item, starting_bid, duration_minutes)
        embed = view.build_embed()
        await it.response.send_message(embed=embed, view=view)
        msg = await it.original_response()
        view.message = msg
        view.start()

    # ═══════════════════════════════════════════════════════════
    # ─── /pool
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="pool", description="🎲 Bda betting pool")
    @app_commands.describe(
        question="Soual (ex: 'Chkoun ghadi yrb7?')",
        options="Options separated by ' | ' (ex: 'A | B | C')",
    )
    async def pool(self, it: discord.Interaction, question: str, options: str):
        opts = [o.strip() for o in options.split("|") if o.strip()]
        if len(opts) < 2 or len(opts) > 5:
            return await it.response.send_message("❌ 2-5 options khass!", ephemeral=True)

        view = PoolView(it.user.id, question, opts)
        embed = view.build_embed()
        await it.response.send_message(embed=embed, view=view)
        msg = await it.original_response()
        view.message = msg

    # ═══════════════════════════════════════════════════════════
    # ─── PREFIX COMMANDS
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="bank")
    async def bank_prefix(self, ctx: commands.Context, member: discord.Member = None):
        """&bank [@user]"""
        member = member or ctx.author
        eco = _get_eco(ctx.guild.id, member.id)
        b = _get_bank(ctx.guild.id, member.id)
        nw = _net_worth(eco, b)
        active = [l for l in b["loans"] if l["paid"] < l["amount_due"]]

        embed = discord.Embed(
            title=f"🏦 Bank — {member.display_name}",
            color=discord.Color.gold(),
            timestamp=datetime.now(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👛 Wallet", value=f"`{_fmt(eco['balance'])}` {COIN}", inline=True)
        embed.add_field(name="🏦 Bank", value=f"`{_fmt(eco['bank'])}` {COIN}", inline=True)
        embed.add_field(name="💎 Savings", value=f"`{_fmt(b['savings'])}` {COIN}", inline=True)
        embed.add_field(name="📊 Net Worth", value=f"`{_fmt(nw)}` {COIN}", inline=True)
        embed.add_field(name="🎖️ Credit", value=f"`{b['credit_score']}`", inline=True)
        embed.add_field(name="📉 Loans", value=f"`{len(active)}`", inline=True)
        if b["businesses"]:
            total_income = sum(BUSINESSES[bz["type"]]["income"] * bz["level"] for bz in b["businesses"])
            embed.add_field(
                name=f"🏢 Businesses ({len(b['businesses'])})",
                value=f"Income: `{_fmt(total_income)}` {COIN} / 30min",
                inline=False,
            )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── &loan (FIXED — kayqbel kol formats)
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="loan")
    async def loan_prefix(self, ctx: commands.Context, *args):
        """
        `&loan <amount>` — Khoud loan
        `&loan take <amount>` — Khoud loan
        `&loan pay <id|all> <amount>` — Khalles
        `&loan info` — Chouf loans
        """
        if not args:
            return await ctx.send(
                "❌ **Usage:**\n"
                "• `&loan <amount>` — Khoud loan\n"
                "• `&loan take <amount>` — Khoud loan\n"
                "• `&loan pay <id|all> <amount>` — Khalles\n"
                "• `&loan info` — Info"
            )

        sub = args[0].lower()
        eco = _get_eco(ctx.guild.id, ctx.author.id)
        b = _get_bank(ctx.guild.id, ctx.author.id)

        # ─── INFO
        if sub == "info":
            active = [l for l in b["loans"] if l["paid"] < l["amount_due"]]
            paid = [l for l in b["loans"] if l["paid"] >= l["amount_due"]]
            embed = discord.Embed(title="💰 Loans", color=discord.Color.gold())
            embed.add_field(name="🎖️ Credit", value=f"`{b['credit_score']}`", inline=True)
            embed.add_field(name="✅ Paid", value=f"`{len(paid)}`", inline=True)
            embed.add_field(name="⚠️ Active", value=f"`{len(active)}`", inline=True)
            if active:
                lines = []
                for l in active[:5]:
                    try:
                        ts = int(datetime.fromisoformat(l["due_at"]).timestamp())
                    except Exception:
                        ts = 0
                    rem = l["amount_due"] - l["paid"]
                    lines.append(f"**`{l['id']}`** — `{_fmt(rem)}` {COIN} due <t:{ts}:R>")
                embed.add_field(name="⚠️ Active Loans", value="\n".join(lines), inline=False)
            return await ctx.send(embed=embed)

        # ─── PAY
        if sub == "pay":
            if len(args) < 3:
                return await ctx.send("❌ Usage: `&loan pay <id|all> <amount>`")
            loan_id = args[1]
            try:
                amount = int(args[2])
            except ValueError:
                return await ctx.send("❌ Amount khass ykoun ra9m!")
            if amount <= 0:
                return await ctx.send("❌ Amount khass > 0!")

            # ─── Pay all
            if loan_id.lower() == "all":
                loans = [l for l in b["loans"] if l["paid"] < l["amount_due"]]
                if not loans:
                    return await ctx.send("❌ Ma 3endekch loans!")
                if amount > eco["balance"]:
                    return await ctx.send("❌ Ma 3endekch flous kafyin!")
                paid_total = 0
                for l in loans:
                    rem = l["amount_due"] - l["paid"]
                    pay = min(amount - paid_total, rem)
                    if pay <= 0:
                        break
                    l["paid"] += pay
                    paid_total += pay
                    if l["paid"] >= l["amount_due"]:
                        b["total_loans_paid"] += 1
                eco["balance"] -= paid_total
                _log_tx(b, "loan_pay", -paid_total, "Paid all")
                _recalc_credit(b)
                _save_economy()
                save_banking()
                return await ctx.send(f"✅ Khallesti `{_fmt(paid_total)}` {COIN}!\n🎖️ Credit: `{b['credit_score']}`")

            # ─── Pay single
            loan = next((l for l in b["loans"] if l["id"] == loan_id.upper()), None)
            if not loan:
                return await ctx.send(f"❌ Loan `{loan_id}` ma kaynch!")
            if loan["paid"] >= loan["amount_due"]:
                return await ctx.send("❌ Deja mkhelles!")
            rem = loan["amount_due"] - loan["paid"]
            if amount > eco["balance"]:
                return await ctx.send("❌ Ma 3endekch flous!")
            pay = min(amount, rem)
            loan["paid"] += pay
            eco["balance"] -= pay
            _log_tx(b, "loan_pay", -pay, f"Loan {loan['id']}")
            if loan["paid"] >= loan["amount_due"]:
                b["total_loans_paid"] += 1
            _recalc_credit(b)
            _save_economy()
            save_banking()
            return await ctx.send(f"✅ Khallesti `{_fmt(pay)}` {COIN}!\n💰 B9a: `{_fmt(loan['amount_due'] - loan['paid'])}` {COIN}")

        # ─── TAKE (or direct amount)
        try:
            if sub == "take":
                if len(args) < 2:
                    return await ctx.send("❌ Usage: `&loan take <amount>`")
                amount = int(args[1])
            else:
                amount = int(sub)
        except ValueError:
            return await ctx.send(
                "❌ **Usage:**\n"
                "• `&loan <amount>`\n"
                "• `&loan take <amount>`\n"
                "• `&loan pay <id|all> <amount>`\n"
                "• `&loan info`"
            )

        if amount < 100:
            return await ctx.send("❌ Minimum: `100`")

        _recalc_credit(b)
        max_amt = int(_max_loan(eco, b))
        if amount > max_amt:
            return await ctx.send(
                f"❌ Max loan dyalek: `{_fmt(max_amt)}` {COIN}\n"
                f"🎖️ Credit: `{b['credit_score']}`"
            )

        interest = int(amount * LOAN_BASE_INTEREST)
        due = amount + interest
        lid = f"L{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now()
        b["loans"].append({
            "id": lid, "principal": amount, "interest": interest,
            "amount_due": due, "paid": 0, "taken_at": now.isoformat(),
            "due_at": (now + timedelta(days=LOAN_TERM_DAYS)).isoformat(),
            "defaulted": False,
        })
        b["total_loans_taken"] += 1
        eco["balance"] += amount
        _log_tx(b, "loan_take", amount, f"Loan {lid}")
        _recalc_credit(b)
        _save_economy()
        save_banking()
        await ctx.send(
            f"💰 **Loan Approved!**\n"
            f"🆔 `{lid}` — Amount: `{_fmt(amount)}` {COIN}\n"
            f"📈 Interest: `{_fmt(interest)}` — Total: `{_fmt(due)}` {COIN}\n"
            f"⏰ Due: <t:{int((now + timedelta(days=LOAN_TERM_DAYS)).timestamp())}:R>"
        )

    # ─── Keep payloan as alias
    @commands.command(name="payloan")
    async def payloan_prefix(self, ctx: commands.Context, loan_id: str, amount: int):
        """&payloan <id|all> <amount> — Alias dyal &loan pay"""
        await self.loan_prefix(ctx, "pay", loan_id, str(amount))

    @commands.command(name="business")
    async def business_prefix(self, ctx: commands.Context, action: str = "list", arg: str = None, arg2: int = None):
        """&business list | buy <type> | collect | upgrade <id> | sell <id>"""
        action = action.lower()
        eco = _get_eco(ctx.guild.id, ctx.author.id)
        b = _get_bank(ctx.guild.id, ctx.author.id)

        if action == "list":
            embed = discord.Embed(title="🏢 Businesses", color=discord.Color.blurple())
            for key, data in BUSINESSES.items():
                embed.add_field(
                    name=f"{data['name']} — `{key}`",
                    value=(
                        f"💵 `{_fmt(data['price'])}` {COIN} • "
                        f"💰 `{_fmt(data['income'])}` / 30min • "
                        f"🎖️ `{data['min_credit']}`"
                    ),
                    inline=False,
                )
            return await ctx.send(embed=embed)

        if action == "buy" and arg:
            biz = BUSINESSES.get(arg.lower())
            if not biz:
                return await ctx.send("❌ Business ma kaynch!")
            if eco["balance"] + eco["bank"] < biz["price"]:
                return await ctx.send(f"❌ Khass `{_fmt(biz['price'])}` {COIN}")
            if b["credit_score"] < biz["min_credit"]:
                return await ctx.send(f"❌ Credit khass `{biz['min_credit']}`")
            cost = biz["price"]
            if eco["balance"] >= cost:
                eco["balance"] -= cost
            else:
                rem = cost - eco["balance"]
                eco["balance"] = 0
                eco["bank"] -= rem
            biz_id = f"B{uuid.uuid4().hex[:6].upper()}"
            b["businesses"].append({
                "id": biz_id, "type": arg.lower(), "level": 1,
                "bought_at": datetime.now().isoformat(), "last_collect": None,
            })
            _log_tx(b, "business_buy", -cost, f"{biz['name']}")
            _recalc_credit(b)
            _save_economy()
            save_banking()
            return await ctx.send(f"✅ **{biz['name']}** tsayeb! ID: `{biz_id}`")

        if action == "collect":
            if not b["businesses"]:
                return await ctx.send("❌ Ma 3endekch businesses!")
            now = datetime.now()
            total = 0
            for biz in b["businesses"]:
                data = BUSINESSES.get(biz["type"])
                if not data:
                    continue
                last = biz.get("last_collect")
                last_dt = datetime.fromisoformat(last) if last else now - timedelta(minutes=30)
                periods = int((now - last_dt).total_seconds() / 60 // 30)
                if periods <= 0:
                    continue
                earned = data["income"] * biz["level"] * periods
                total += earned
                biz["last_collect"] = now.isoformat()
            if total <= 0:
                return await ctx.send("⏰ Ba9i ma 3endekch income!")
            eco["balance"] += total
            _log_tx(b, "business_collect", total, "")
            _save_economy()
            save_banking()
            return await ctx.send(f"💰 **+{_fmt(total)}** {COIN}!")

        if action == "upgrade" and arg:
            biz = next((x for x in b["businesses"] if x["id"] == arg.upper()), None)
            if not biz:
                return await ctx.send("❌ Business ma kaynch!")
            data = BUSINESSES[biz["type"]]
            if biz["level"] >= data["max_level"]:
                return await ctx.send("❌ Max level!")
            cost = data["upgrade_cost"] * biz["level"]
            if eco["balance"] + eco["bank"] < cost:
                return await ctx.send(f"❌ Khass `{_fmt(cost)}` {COIN}")
            if eco["balance"] >= cost:
                eco["balance"] -= cost
            else:
                rem = cost - eco["balance"]
                eco["balance"] = 0
                eco["bank"] -= rem
            biz["level"] += 1
            _log_tx(b, "business_upgrade", -cost, "")
            _save_economy()
            save_banking()
            return await ctx.send(f"✅ Upgraded l **Lv{biz['level']}**!")

        if action == "sell" and arg:
            biz = next((x for x in b["businesses"] if x["id"] == arg.upper()), None)
            if not biz:
                return await ctx.send("❌ Business ma kaynch!")
            data = BUSINESSES[biz["type"]]
            val = data["price"] + (data["upgrade_cost"] * (biz["level"] - 1))
            payout = int(val * 0.5)
            eco["balance"] += payout
            b["businesses"].remove(biz)
            _log_tx(b, "business_sell", payout, f"{data['name']}")
            _recalc_credit(b)
            _save_economy()
            save_banking()
            return await ctx.send(f"💸 Bi3ti **{data['name']}** b `{_fmt(payout)}` {COIN}")

        await ctx.send("❌ Usage: `&business list|buy <type>|collect|upgrade <id>|sell <id>`")

    @commands.command(name="stocks")
    async def stocks_prefix(self, ctx: commands.Context, action: str = "list"):
        """&stocks list|portfolio"""
        action = action.lower()
        if action == "list":
            stocks = _market("stocks")
            embed = discord.Embed(title="📈 Stock Market", color=discord.Color.green())
            for sym, d in stocks.items():
                embed.add_field(name=f"`{sym}` — {d['name']}",
                                value=f"`{d['price']:,.2f}` {COIN}", inline=True)
            return await ctx.send(embed=embed)
        if action == "portfolio":
            b = _get_bank(ctx.guild.id, ctx.author.id)
            if not b["stocks"]:
                return await ctx.send("❌ Ma 3endekch stocks!")
            stocks = _market("stocks")
            embed = discord.Embed(title="📊 Portfolio", color=discord.Color.green())
            for sym, h in b["stocks"].items():
                if sym not in stocks:
                    continue
                val = stocks[sym]["price"] * h["shares"]
                embed.add_field(name=f"`{sym}` ×{h['shares']}",
                                value=f"`{_fmt(val)}` {COIN}", inline=True)
            return await ctx.send(embed=embed)
        await ctx.send("❌ Usage: `&stocks list|portfolio`")

    @commands.command(name="crypto")
    async def crypto_prefix(self, ctx: commands.Context, action: str = "list"):
        """&crypto list|portfolio"""
        action = action.lower()
        if action == "list":
            cryptos = _market("crypto")
            embed = discord.Embed(title="🪙 Crypto Market", color=discord.Color.orange())
            for sym, d in cryptos.items():
                embed.add_field(name=f"`{sym}` — {d['name']}",
                                value=f"`{d['price']:,.4f}` {COIN}", inline=True)
            return await ctx.send(embed=embed)
        if action == "portfolio":
            b = _get_bank(ctx.guild.id, ctx.author.id)
            if not b["crypto"]:
                return await ctx.send("❌ Ma 3endekch crypto!")
            cryptos = _market("crypto")
            embed = discord.Embed(title="🪙 Portfolio", color=discord.Color.orange())
            for sym, h in b["crypto"].items():
                if sym not in cryptos:
                    continue
                val = cryptos[sym]["price"] * h["amount"]
                embed.add_field(name=f"`{sym}` ×{h['amount']:.4f}",
                                value=f"`{_fmt(val)}` {COIN}", inline=True)
            return await ctx.send(embed=embed)
        await ctx.send("❌ Usage: `&crypto list|portfolio`")

    @commands.command(name="interest")
    async def interest_prefix(self, ctx: commands.Context):
        """&interest — Jme3 bank interest"""
        eco = _get_eco(ctx.guild.id, ctx.author.id)
        b = _get_bank(ctx.guild.id, ctx.author.id)
        if eco["bank"] <= 0:
            return await ctx.send("❌ Bank khawi!")
        if b.get("last_interest_claim"):
            try:
                last = datetime.fromisoformat(b["last_interest_claim"])
                if datetime.now() - last < timedelta(hours=24):
                    rem = timedelta(hours=24) - (datetime.now() - last)
                    return await ctx.send(f"⏰ 3awed mn ba3d `{rem.seconds // 3600}h {(rem.seconds % 3600) // 60}m`!")
            except Exception:
                pass
        amount = int(eco["bank"] * BANK_INTEREST_RATE * 24)
        if amount < 1:
            return await ctx.send("❌ Bank sghir bezzaf!")
        eco["bank"] += amount
        b["last_interest_claim"] = datetime.now().isoformat()
        _save_economy()
        save_banking()
        await ctx.send(f"💰 **+{_fmt(amount)}** {COIN} interest!")

    @commands.command(name="tx")
    async def tx_prefix(self, ctx: commands.Context):
        """&tx — Transactions"""
        b = _get_bank(ctx.guild.id, ctx.author.id)
        if not b["transactions"]:
            return await ctx.send("❌ Ma kaynch transactions!")
        embed = discord.Embed(title="📜 Transactions (last 10)", color=discord.Color.blurple())
        for tx in reversed(b["transactions"][-10:]):
            try:
                ts = int(datetime.fromisoformat(tx["time"]).timestamp())
            except Exception:
                ts = 0
            amt = tx["amount"]
            emoji = "💚" if amt >= 0 else "❤️"
            embed.add_field(
                name=f"{emoji} `{tx['type']}` — `{_fmt(abs(amt))}` {COIN}",
                value=f"<t:{ts}:R>",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command(name="savings")
    async def savings_prefix(self, ctx: commands.Context, action: str = "info", amount: int = None):
        """&savings info|deposit <amt>|withdraw"""
        action = action.lower()
        eco = _get_eco(ctx.guild.id, ctx.author.id)
        b = _get_bank(ctx.guild.id, ctx.author.id)

        if action == "info":
            embed = discord.Embed(title="💎 Savings", color=discord.Color.blue())
            embed.add_field(name="💰 Balance", value=f"`{_fmt(b['savings'])}` {COIN}", inline=True)
            embed.add_field(name="📈 Rate", value=f"`{SAVINGS_INTEREST*100}%` / 24h", inline=True)
            if b.get("savings_locked_until"):
                try:
                    until = datetime.fromisoformat(b["savings_locked_until"])
                    if until > datetime.now():
                        embed.add_field(name="🔒 Locked", value=f"<t:{int(until.timestamp())}:R>", inline=False)
                except Exception:
                    pass
            return await ctx.send(embed=embed)

        if action == "deposit":
            if amount is None or amount <= 0:
                return await ctx.send("❌ Usage: `&savings deposit <amount>`")
            if eco["balance"] < amount:
                return await ctx.send("❌ Ma 3endekch flous!")
            eco["balance"] -= amount
            b["savings"] += amount
            b["savings_locked_until"] = (datetime.now() + timedelta(hours=SAVINGS_LOCK_HOURS)).isoformat()
            _save_economy()
            save_banking()
            return await ctx.send(f"💎 Zidt `{_fmt(amount)}` {COIN}!")

        if action == "withdraw":
            if b["savings"] <= 0:
                return await ctx.send("❌ Savings khawi!")
            if b.get("savings_locked_until"):
                try:
                    until = datetime.fromisoformat(b["savings_locked_until"])
                    if until > datetime.now():
                        return await ctx.send(f"🔒 Locked until <t:{int(until.timestamp())}:R>")
                except Exception:
                    pass
            interest = int(b["savings"] * SAVINGS_INTEREST)
            total = b["savings"] + interest
            eco["balance"] += total
            b["savings"] = 0
            b["savings_locked_until"] = None
            _save_economy()
            save_banking()
            return await ctx.send(f"💎 Hyedti `{_fmt(total)}` {COIN}! (interest: `{_fmt(interest)}`)")

        await ctx.send("❌ Usage: `&savings info|deposit <amt>|withdraw`")


# ═══════════════════════════════════════════════════════════════════
# ─── AUCTION VIEW
# ═══════════════════════════════════════════════════════════════════
class AuctionView(discord.ui.View):
    def __init__(self, host_id: int, item: str, starting_bid: int, duration_min: int):
        super().__init__(timeout=None)
        self.host_id = host_id
        self.item = item
        self.current_bid = starting_bid
        self.current_bidder = None
        self.ends_at = datetime.now() + timedelta(minutes=duration_min)
        self.message = None
        self.ended = False
        self._task = None

    def build_embed(self, result: str = None, color=None):
        if self.ended:
            c = color or discord.Color.dark_gray()
            t = "🔨 Auction Ended"
        else:
            c = color or discord.Color.gold()
            t = "🔨 Auction Live"

        embed = discord.Embed(title=t, color=c)
        embed.add_field(name="📦 Item", value=self.item, inline=False)
        embed.add_field(name="💰 Current Bid", value=f"`{_fmt(self.current_bid)}` {COIN}", inline=True)
        embed.add_field(
            name="👤 Bidder",
            value=f"<@{self.current_bidder}>" if self.current_bidder else "*ta 7ed*",
            inline=True,
        )
        if not self.ended:
            embed.add_field(
                name="⏰ Ends",
                value=f"<t:{int(self.ends_at.timestamp())}:R>",
                inline=False,
            )
        if result:
            embed.add_field(name="Result", value=result, inline=False)
        embed.set_footer(text=f"Host: <@{self.host_id}>")
        return embed

    def start(self):
        self._task = asyncio.create_task(self._timer())

    async def _timer(self):
        while datetime.now() < self.ends_at:
            await asyncio.sleep(2)
        await self._end()

    async def _end(self):
        if self.ended:
            return
        self.ended = True

        if self.current_bidder:
            gid = self.message.guild.id
            eco = _get_eco(gid, self.current_bidder)
            if eco["balance"] >= self.current_bid:
                eco["balance"] -= self.current_bid
                host_eco = _get_eco(gid, self.host_id)
                host_eco["balance"] += self.current_bid
                _save_economy()
                result = f"✅ <@{self.current_bidder}> rb7 b `{_fmt(self.current_bid)}` {COIN}!"
                color = discord.Color.green()
            else:
                result = "❌ Winner ma 3endouch flous!"
                color = discord.Color.red()
        else:
            result = "😢 Ma kaynch bids!"
            color = discord.Color.red()

        for c in self.children:
            c.disabled = True
        try:
            await self.message.edit(embed=self.build_embed(result, color), view=self)
        except Exception:
            pass
        self.stop()

    @discord.ui.button(label="Bid", emoji="💰", style=discord.ButtonStyle.success)
    async def bid_btn(self, it: discord.Interaction, b: discord.ui.Button):
        if self.ended:
            return await it.response.send_message("❌ Auction khlat!", ephemeral=True)
        await it.response.send_modal(AuctionBidModal(self))


class AuctionBidModal(discord.ui.Modal, title="💰 Bid"):
    amount = discord.ui.TextInput(label="Bid amount", max_length=12)

    def __init__(self, view: AuctionView):
        super().__init__()
        self.view = view

    async def on_submit(self, it: discord.Interaction):
        try:
            amt = int(self.amount.value)
        except ValueError:
            return await it.response.send_message("❌ Ra9m ghalat!", ephemeral=True)

        if amt <= self.view.current_bid:
            return await it.response.send_message(
                f"❌ Bid khass > `{_fmt(self.view.current_bid)}`!", ephemeral=True
            )
        if it.user.id == self.view.host_id:
            return await it.response.send_message("❌ Ma tqderch tbidi f auction dyalek!", ephemeral=True)

        eco = _get_eco(it.guild.id, it.user.id)
        if eco["balance"] < amt:
            return await it.response.send_message("❌ Ma 3endekch flous kafyin!", ephemeral=True)

        self.view.current_bid = amt
        self.view.current_bidder = it.user.id
        if (self.view.ends_at - datetime.now()).total_seconds() < 30:
            self.view.ends_at = datetime.now() + timedelta(seconds=30)

        try:
            await self.view.message.edit(embed=self.view.build_embed(), view=self.view)
        except Exception:
            pass

        await it.response.send_message(f"✅ Bid `{_fmt(amt)}` {COIN}!", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════
# ─── BETTING POOL VIEW
# ═══════════════════════════════════════════════════════════════════
class PoolView(discord.ui.View):
    def __init__(self, host_id: int, question: str, options: list):
        super().__init__(timeout=None)
        self.host_id = host_id
        self.question = question
        self.options = options
        self.bets = {i: [] for i in range(len(options))}
        self.total_pool = 0
        self.message = None
        self.closed = False
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        for i, opt in enumerate(self.options):
            btn = discord.ui.Button(
                label=opt[:80],
                style=discord.ButtonStyle.primary,
                row=0,
                custom_id=f"pool:bet:{i}",
            )
            btn.callback = self._make_cb(i)
            self.add_item(btn)

        close_btn = discord.ui.Button(
            label="Close", emoji="🔒", style=discord.ButtonStyle.danger,
            row=1, custom_id="pool:close",
        )
        close_btn.callback = self._close
        self.add_item(close_btn)

    def _make_cb(self, idx):
        async def cb(it):
            if self.closed:
                return await it.response.send_message("❌ Pool msdouda!", ephemeral=True)
            await it.response.send_modal(PoolBetModal(self, idx))
        return cb

    def build_embed(self, result: str = None, color=None):
        embed = discord.Embed(
            title="🎲 Betting Pool",
            description=f"**{self.question}**",
            color=color or discord.Color.blurple(),
        )
        total_bets = sum(len(v) for v in self.bets.values())
        embed.add_field(name="💰 Total Pool", value=f"`{_fmt(self.total_pool)}` {COIN}", inline=True)
        embed.add_field(name="🎯 Total Bets", value=f"`{total_bets}`", inline=True)

        for i, opt in enumerate(self.options):
            bets = self.bets[i]
            amt = sum(b[1] for b in bets)
            pct = (amt / self.total_pool * 100) if self.total_pool > 0 else 0
            embed.add_field(
                name=f"{i+1}️⃣ {opt}",
                value=f"`{_fmt(amt)}` {COIN} ({pct:.1f}%) • {len(bets)} bets",
                inline=False,
            )

        if result:
            embed.add_field(name="🏆 Result", value=result, inline=False)
        if not self.closed:
            embed.set_footer(text=f"Host: <@{self.host_id}> • Click option bash tbidi")
        return embed

    async def _close(self, it):
        if it.user.id != self.host_id:
            return await it.response.send_message("❌ Ghir host!", ephemeral=True)
        if self.closed:
            return await it.response.send_message("❌ Deja msdouda!", ephemeral=True)
        self.closed = True

        if self.total_pool == 0:
            for c in self.children:
                c.disabled = True
            try:
                await self.message.edit(embed=self.build_embed("😢 Ma kaynch bets!", discord.Color.red()), view=self)
            except Exception:
                pass
            return

        winner_idx = max(self.bets.keys(), key=lambda i: sum(b[1] for b in self.bets[i]))
        winners = self.bets[winner_idx]

        if not winners:
            for c in self.children:
                c.disabled = True
            try:
                await self.message.edit(embed=self.build_embed("😢 Ma kaynch winners!", discord.Color.red()), view=self)
            except Exception:
                pass
            return

        winner_total = sum(b[1] for b in winners)
        gid = self.message.guild.id

        for uid, amt in winners:
            share = int(self.total_pool * (amt / winner_total))
            eco = _get_eco(gid, uid)
            eco["balance"] += share

        _save_economy()

        for c in self.children:
            c.disabled = True

        result_txt = (
            f"🏆 **{self.options[winner_idx]}** wins!\n"
            f"💰 Pool: `{_fmt(self.total_pool)}` {COIN} distributed to {len(winners)} winners"
        )
        try:
            await self.message.edit(embed=self.build_embed(result_txt, discord.Color.green()), view=self)
        except Exception:
            pass
        await it.response.send_message("✅ Pool resolved!", ephemeral=True)


class PoolBetModal(discord.ui.Modal, title="🎲 Place Bet"):
    amount = discord.ui.TextInput(label="Amount", max_length=12)

    def __init__(self, view: PoolView, opt_idx: int):
        super().__init__()
        self.view = view
        self.opt_idx = opt_idx
        self.title = f"Bet on: {view.options[opt_idx][:40]}"

    async def on_submit(self, it: discord.Interaction):
        if self.view.closed:
            return await it.response.send_message("❌ Pool msdouda!", ephemeral=True)
        try:
            amt = int(self.amount.value)
        except ValueError:
            return await it.response.send_message("❌ Ra9m ghalat!", ephemeral=True)
        if amt < 10:
            return await it.response.send_message("❌ Minimum bet: `10`", ephemeral=True)

        eco = _get_eco(it.guild.id, it.user.id)
        if eco["balance"] < amt:
            return await it.response.send_message("❌ Ma 3endekch flous!", ephemeral=True)

        eco["balance"] -= amt
        self.view.bets[self.opt_idx].append((it.user.id, amt))
        self.view.total_pool += amt
        _save_economy()

        try:
            await self.view.message.edit(embed=self.view.build_embed(), view=self.view)
        except Exception:
            pass
        await it.response.send_message(
            f"✅ Bidti `{_fmt(amt)}` {COIN} 3la **{self.view.options[self.opt_idx]}**!",
            ephemeral=True,
        )


# ═══════════════════════════════════════════════════════════════════
# ─── SETUP
# ═══════════════════════════════════════════════════════════════════
async def setup(bot):
    await bot.add_cog(Banking(bot))