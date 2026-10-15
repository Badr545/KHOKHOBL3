# cogs/economy.py
# =====================================================================
# ─── ECONOMY — Balance, Daily, Work (10s), Rob, Dep, With
# ─── + Reset commands (role-restricted + self-reset)
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timedelta

from data_manager import ECONOMY, save_economy as _save_economy


WORK_RESPONSES = [
    "Khdmti f maktab w rb7ti",
    "Sewwebti pizza w rb7ti",
    "Selle7ti sayyara w rb7ti",
    "Ktebti code w rb7ti",
    "Dert design w rb7ti",
]

ROB_FAIL = [
    "L-policier chafek w 3tak fine",
    "L-victime 3endou bodyguard",
    "Tla3ti f camera",
    "Dert 7s w tqbadti",
]

WORK_COOLDOWN = timedelta(seconds=10)

# ─── Role ID li 3endha l-7a9 b reset commands (Copy ID mn Discord) ───
# ─── Role IDs li 3endhom l-7a9 b reset commands (Copy IDs mn Discord) ───
ADMIN_RESET_ROLE_IDS = [
    "1370937530459099246",#founder
    "1553762340653244497",#casino owner
    # ⬅️ Zid ch7al ma bghiti mn ID hna (kol wa7ed f line)
]


def has_reset_role(member: discord.Member) -> bool:
    """Check wach l-member 3endou wa7ed mn roles dyal reset (wla admin)."""
    if member.guild_permissions.administrator:
        return True
    member_role_ids = {str(r.id) for r in member.roles}
    return any(rid in member_role_ids for rid in ADMIN_RESET_ROLE_IDS)


class Economy(commands.Cog):
    """Economy"""

    def __init__(self, bot):
        self.bot = bot

    def _get_user(self, guild_id: int, user_id: int) -> dict:
        ECONOMY.setdefault(guild_id, {}).setdefault(user_id, {
            "balance": 0, "bank": 0,
            "last_daily": None, "last_work": None, "last_rob": None,
            "inventory": [],
        })
        return ECONOMY[guild_id][user_id]

    # ═══════════════════════════════════════════════════════════
    # ─── SLASH COMMANDS
    # ═══════════════════════════════════════════════════════════

    @app_commands.command(name="balance", description="Chouf l-balance dyalek")
    @app_commands.describe(member="L-user")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user
        data = self._get_user(interaction.guild.id, member.id)
        embed = discord.Embed(title=f"💰 Balance — {member.name}", color=discord.Color.gold())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👛 Wallet", value=f"`{data['balance']:,}` 🪙", inline=True)
        embed.add_field(name="🏦 Bank", value=f"`{data['bank']:,}` 🪙", inline=True)
        embed.add_field(name="💎 Total", value=f"`{data['balance'] + data['bank']:,}` 🪙", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Jib l-rati dyalk l-yawmi")
    async def daily(self, interaction: discord.Interaction):
        data = self._get_user(interaction.guild.id, interaction.user.id)
        now = datetime.now()
        if data["last_daily"]:
            last = datetime.fromisoformat(data["last_daily"])
            diff = now - last
            if diff < timedelta(hours=24):
                remaining = timedelta(hours=24) - diff
                h = remaining.seconds // 3600
                m = (remaining.seconds % 3600) // 60
                return await interaction.response.send_message(f"⏰ 3awed mn ba3d `{h}h {m}m`!", ephemeral=True)
        amount = random.randint(500, 1500)
        data["balance"] += amount
        data["last_daily"] = now.isoformat()
        _save_economy()
        embed = discord.Embed(title="🎁 Daily Reward!", description=f"**+{amount:,}** 🪙 dkhlou l-wallet!", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="work", description="Khdm w jib flous (10s cooldown)")
    async def work(self, interaction: discord.Interaction):
        data = self._get_user(interaction.guild.id, interaction.user.id)
        now = datetime.now()
        if data["last_work"]:
            last = datetime.fromisoformat(data["last_work"])
            if now - last < WORK_COOLDOWN:
                remaining = int((WORK_COOLDOWN - (now - last)).total_seconds())
                return await interaction.response.send_message(f"⏰ 3awed mn ba3d `{remaining}s`!", ephemeral=True)
        amount = random.randint(100, 400)
        data["balance"] += amount
        data["last_work"] = now.isoformat()
        _save_economy()
        await interaction.response.send_message(f"💼 {random.choice(WORK_RESPONSES)} **{amount:,}** 🪙!")

    @app_commands.command(name="rob", description="Srq chi wa7ed")
    @app_commands.describe(member="L-victime")
    async def rob(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ Ma tqderch tsrq rasek!", ephemeral=True)
        if member.bot:
            return await interaction.response.send_message("❌ Ma tqderch tsrq bot!", ephemeral=True)
        robber = self._get_user(interaction.guild.id, interaction.user.id)
        victim = self._get_user(interaction.guild.id, member.id)
        now = datetime.now()
        if robber["last_rob"]:
            last = datetime.fromisoformat(robber["last_rob"])
            if now - last < timedelta(hours=2):
                m = int((timedelta(hours=2) - (now - last)).total_seconds() // 60)
                return await interaction.response.send_message(f"⏰ 3awed mn ba3d `{m}m`!", ephemeral=True)
        if victim["balance"] < 100:
            return await interaction.response.send_message(f"❌ {member.mention} ma 3endouch flous!", ephemeral=True)
        robber["last_rob"] = now.isoformat()
        success = random.random() < 0.4
        if success:
            amount = random.randint(50, min(500, victim["balance"]))
            victim["balance"] -= amount
            robber["balance"] += amount
            embed = discord.Embed(title="🥷 Rob Success!", description=f"Srqti **{amount:,}** 🪙 mn {member.mention}!", color=discord.Color.green())
        else:
            fine = min(200, robber["balance"])
            robber["balance"] -= fine
            embed = discord.Embed(title="🚨 Rob Failed!", description=f"{random.choice(ROB_FAIL)}\n**Fine:** `{fine}` 🪙", color=discord.Color.red())
        _save_economy()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pay", description="Sift flous l chi wa7ed")
    @app_commands.describe(member="L-user", amount="Ch7al")
    async def pay(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if member.bot:
            return await interaction.response.send_message("❌ Ma tqderch tsift l bot!", ephemeral=True)
        if amount <= 0:
            return await interaction.response.send_message("❌ Amount khass > 0!", ephemeral=True)
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ Ma tqderch tsift l rasek!", ephemeral=True)
        sender = self._get_user(interaction.guild.id, interaction.user.id)
        receiver = self._get_user(interaction.guild.id, member.id)
        if sender["balance"] < amount:
            return await interaction.response.send_message("❌ Ma 3endkch flous kafyin!", ephemeral=True)
        sender["balance"] -= amount
        receiver["balance"] += amount
        _save_economy()
        await interaction.response.send_message(f"✅ Siftti **{amount:,}** 🪙 l {member.mention}!")

    @app_commands.command(name="gamble", description="Qamr flousek")
    @app_commands.describe(amount="Ch7al bghiti tqamr")
    async def gamble(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            return await interaction.response.send_message("❌ Amount khass > 0!", ephemeral=True)
        data = self._get_user(interaction.guild.id, interaction.user.id)
        if data["balance"] < amount:
            return await interaction.response.send_message("❌ Ma 3endkch flous kafyin!", ephemeral=True)
        if random.random() < 0.5:
            data["balance"] += amount
            await interaction.response.send_message(f"🎉 **Rb7ti!** +`{amount:,}` 🪙")
        else:
            data["balance"] -= amount
            await interaction.response.send_message(f"😢 **Khserti!** -`{amount:,}` 🪙")
        _save_economy()

    @app_commands.command(name="leaderboard", description="Top 10 flous")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_data = ECONOMY.get(interaction.guild.id, {})
        if not guild_data:
            return await interaction.response.send_message("❌ Ma kaynch data!", ephemeral=True)
        sorted_users = sorted(guild_data.items(), key=lambda x: x[1]["balance"] + x[1]["bank"], reverse=True)[:10]
        embed = discord.Embed(title="🏆 Leaderboard — Top 10", color=discord.Color.gold())
        medals = ["🥇", "🥈", "🥉"]
        for i, (user_id, data) in enumerate(sorted_users):
            try:
                user = await self.bot.fetch_user(user_id)
                name = user.name
            except Exception:
                name = f"User {user_id}"
            total = data["balance"] + data["bank"]
            prefix = medals[i] if i < 3 else f"`#{i+1}`"
            embed.add_field(name=f"{prefix} {name}", value=f"`{total:,}` 🪙", inline=False)
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── RESET COMMANDS (role-restricted) — SLASH
    # ═══════════════════════════════════════════════════════════

    @app_commands.command(name="resetmoney", description="[ADMIN] Reset flous dyal user wa7ed")
    @app_commands.describe(member="L-user li bghiti treset flousou")
    async def resetmoney(self, interaction: discord.Interaction, member: discord.Member):
        if not has_reset_role(interaction.user):
            return await interaction.response.send_message(
                "❌ Ma 3endekch l-7a9 b had commande!", ephemeral=True,
            )
        data = self._get_user(interaction.guild.id, member.id)
        old_bal = data.get("balance", 0)
        old_bank = data.get("bank", 0)
        data["balance"] = 0
        data["bank"] = 0
        _save_economy()

        embed = discord.Embed(
            title="♻️ Reset Money",
            description=f"Flous dyal {member.mention} tms7ou!",
            color=discord.Color.red(),
        )
        embed.add_field(
            name="📉 Qbel",
            value=f"👛 `{old_bal:,}` | 🏦 `{old_bank:,}`",
            inline=False,
        )
        embed.add_field(name="📈 Daba", value="👛 `0` | 🏦 `0`", inline=False)
        embed.set_footer(text=f"Par {interaction.user.name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="resetcasino", description="[ADMIN] Reset flous dyal GA3 l-users f serveur")
    async def resetcasino(self, interaction: discord.Interaction):
        if not has_reset_role(interaction.user):
            return await interaction.response.send_message(
                "❌ Ma 3endekch l-7a9 b had commande!", ephemeral=True,
            )

        await interaction.response.defer()

        guild_data = ECONOMY.get(interaction.guild.id, {})
        count = 0
        total_wiped = 0
        for user_id, data in guild_data.items():
            total_wiped += data.get("balance", 0) + data.get("bank", 0)
            data["balance"] = 0
            data["bank"] = 0
            data["last_daily"] = None
            data["last_work"] = None
            data["last_rob"] = None
            data["last_collect"] = None
            count += 1
        _save_economy()

        embed = discord.Embed(
            title="💥 Casino Reset!",
            description="**Ga3 l-flous f had serveur tms7ou!**",
            color=discord.Color.dark_red(),
        )
        embed.add_field(name="👥 Users", value=f"`{count:,}`", inline=True)
        embed.add_field(name="🗑️ Total m7i", value=f"`{total_wiped:,}` 🪙", inline=True)
        embed.set_footer(text=f"Par {interaction.user.name}")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="resetme", description="Reset flousek nta (wallet + bank)")
    async def resetme(self, interaction: discord.Interaction):
        data = self._get_user(interaction.guild.id, interaction.user.id)
        old_bal = data.get("balance", 0)
        old_bank = data.get("bank", 0)

        if old_bal == 0 and old_bank == 0:
            return await interaction.response.send_message(
                "❌ Ma 3endekch flous bach tresethom!", ephemeral=True,
            )

        data["balance"] = 0
        data["bank"] = 0
        _save_economy()

        embed = discord.Embed(
            title="♻️ Reset dyalek",
            description=f"Flousek tms7ou, {interaction.user.mention}!",
            color=discord.Color.orange(),
        )
        embed.add_field(name="📉 Qbel", value=f"👛 `{old_bal:,}` | 🏦 `{old_bank:,}`", inline=False)
        embed.add_field(name="📈 Daba", value="👛 `0` | 🏦 `0`", inline=False)
        embed.set_footer(text="Kolchi 9ader yst3ml had commande")
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── PREFIX COMMANDS
    # ═══════════════════════════════════════════════════════════

    @commands.command(name="balance")
    async def balance_prefix(self, ctx: commands.Context, member: discord.Member = None):
        """&balance [@user]"""
        if member is None:
            member = ctx.author
        data = self._get_user(ctx.guild.id, member.id)
        total = data["balance"] + data["bank"]
        await ctx.send(
            f"💰 **{member.name}**\n"
            f"👛 Wallet: `{data['balance']:,}` 🪙\n"
            f"🏦 Bank: `{data['bank']:,}` 🪙\n"
            f"💎 Total: `{total:,}` 🪙"
        )

    @commands.command(name="coins")
    async def coins_prefix(self, ctx: commands.Context, member: discord.Member = None):
        """&coins [@user] — Alias dyal balance"""
        if member is None:
            member = ctx.author
        data = self._get_user(ctx.guild.id, member.id)
        total = data["balance"] + data["bank"]
        await ctx.send(
            f"💰 **{member.name}**\n"
            f"👛 Wallet: `{data['balance']:,}` 🪙\n"
            f"🏦 Bank: `{data['bank']:,}` 🪙\n"
            f"💎 Total: `{total:,}` 🪙"
        )

    @commands.command(name="daily")
    async def daily_prefix(self, ctx: commands.Context):
        """&daily"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        now = datetime.now()
        if data["last_daily"]:
            last = datetime.fromisoformat(data["last_daily"])
            if now - last < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last)
                h = remaining.seconds // 3600
                m = (remaining.seconds % 3600) // 60
                return await ctx.send(f"⏰ 3awed mn ba3d `{h}h {m}m`!")
        amount = random.randint(500, 1500)
        data["balance"] += amount
        data["last_daily"] = now.isoformat()
        _save_economy()
        await ctx.send(f"🎁 **+{amount:,}** 🪙!")

    @commands.command(name="work")
    async def work_prefix(self, ctx: commands.Context):
        """&work — Khdm w jib flous (10s cooldown)"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        now = datetime.now()
        if data["last_work"]:
            last = datetime.fromisoformat(data["last_work"])
            if now - last < WORK_COOLDOWN:
                remaining = int((WORK_COOLDOWN - (now - last)).total_seconds())
                return await ctx.send(f"⏰ 3awed mn ba3d `{remaining}s`!")
        amount = random.randint(100, 400)
        data["balance"] += amount
        data["last_work"] = now.isoformat()
        _save_economy()
        await ctx.send(f"💼 {random.choice(WORK_RESPONSES)} **{amount:,}** 🪙!")

    @commands.command(name="rob")
    async def rob_prefix(self, ctx: commands.Context, member: discord.Member):
        """&rob @user"""
        if member.id == ctx.author.id:
            return await ctx.send("❌ Ma tqderch tsrq rasek!")
        if member.bot:
            return await ctx.send("❌ Ma tqderch tsrq bot!")
        robber = self._get_user(ctx.guild.id, ctx.author.id)
        victim = self._get_user(ctx.guild.id, member.id)
        now = datetime.now()
        if robber["last_rob"]:
            last = datetime.fromisoformat(robber["last_rob"])
            if now - last < timedelta(hours=2):
                m = int((timedelta(hours=2) - (now - last)).total_seconds() // 60)
                return await ctx.send(f"⏰ 3awed mn ba3d `{m}m`!")
        if victim["balance"] < 100:
            return await ctx.send(f"❌ {member.mention} ma 3endouch flous f wallet!")
        robber["last_rob"] = now.isoformat()
        success = random.random() < 0.4
        if success:
            amount = random.randint(50, min(500, victim["balance"]))
            victim["balance"] -= amount
            robber["balance"] += amount
            await ctx.send(f"🥷 **Rob Success!** Srqti `{amount:,}` 🪙 mn {member.mention}!")
        else:
            fine = min(200, robber["balance"])
            robber["balance"] -= fine
            await ctx.send(f"🚨 **Rob Failed!** {random.choice(ROB_FAIL)}\n**Fine:** `{fine}` 🪙")
        _save_economy()

    @commands.command(name="pay")
    async def pay_prefix(self, ctx: commands.Context, member: discord.Member, amount: int):
        """&pay @user <amount>"""
        if member.bot:
            return await ctx.send("❌ Ma tqderch tsift l bot!")
        if amount <= 0:
            return await ctx.send("❌ Amount khass > 0!")
        if member.id == ctx.author.id:
            return await ctx.send("❌ Ma tqderch tsift l rasek!")
        sender = self._get_user(ctx.guild.id, ctx.author.id)
        receiver = self._get_user(ctx.guild.id, member.id)
        if sender["balance"] < amount:
            return await ctx.send("❌ Ma 3endkch flous kafyin f wallet!")
        sender["balance"] -= amount
        receiver["balance"] += amount
        _save_economy()
        await ctx.send(f"✅ Siftti **{amount:,}** 🪙 l {member.mention}!")

    @commands.command(name="dep")
    async def dep_prefix(self, ctx: commands.Context, amount: str):
        """&dep <amount|all>"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        if amount.lower() == "all":
            amt = data["balance"]
        else:
            try:
                amt = int(amount)
            except ValueError:
                return await ctx.send("❌ Kteb ra9m wla `all`!")
        if amt <= 0:
            return await ctx.send("❌ Amount khass > 0!")
        if data["balance"] < amt:
            return await ctx.send(f"❌ Ma 3endkch `{amt:,}` 🪙 f wallet!")
        data["balance"] -= amt
        data["bank"] += amt
        _save_economy()
        await ctx.send(
            f"🏦 **Deposited** `{amt:,}` 🪙\n"
            f"👛 Wallet: `{data['balance']:,}` | 🏦 Bank: `{data['bank']:,}`"
        )

    @commands.command(name="with")
    async def with_prefix(self, ctx: commands.Context, amount: str):
        """&with <amount|all>"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        if amount.lower() == "all":
            amt = data["bank"]
        else:
            try:
                amt = int(amount)
            except ValueError:
                return await ctx.send("❌ Kteb ra9m wla `all`!")
        if amt <= 0:
            return await ctx.send("❌ Amount khass > 0!")
        if data["bank"] < amt:
            return await ctx.send(f"❌ Ma 3endkch `{amt:,}` 🪙 f bank!")
        data["bank"] -= amt
        data["balance"] += amt
        _save_economy()
        await ctx.send(
            f"👛 **Withdrew** `{amt:,}` 🪙\n"
            f"👛 Wallet: `{data['balance']:,}` | 🏦 Bank: `{data['bank']:,}`"
        )

    @commands.command(name="lb")
    async def lb_prefix(self, ctx: commands.Context):
        """&lb"""
        guild_data = ECONOMY.get(ctx.guild.id, {})
        if not guild_data:
            return await ctx.send("❌ Ma kaynch data!")
        sorted_users = sorted(
            guild_data.items(),
            key=lambda x: x[1].get("balance", 0) + x[1].get("bank", 0),
            reverse=True,
        )[:10]
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (user_id, data) in enumerate(sorted_users):
            try:
                user = await self.bot.fetch_user(user_id)
                name = user.name
            except Exception:
                name = f"User {user_id}"
            total = data.get("balance", 0) + data.get("bank", 0)
            prefix = medals[i] if i < 3 else f"#{i+1}"
            lines.append(f"{prefix} **{name}** — `{total:,}` 🪙")
        await ctx.send("🏆 **Top 10 Coins:**\n" + "\n".join(lines))

    # ═══════════════════════════════════════════════════════════
    # ─── RESET COMMANDS — PREFIX
    # ═══════════════════════════════════════════════════════════

    @commands.command(name="resetmoney")
    async def resetmoney_prefix(self, ctx: commands.Context, member: discord.Member):
        """&resetmoney @user — [ADMIN] Reset flous dyal user"""
        if not has_reset_role(ctx.author):
            return await ctx.send("❌ Ma 3endekch l-7a9 b had commande!")
        data = self._get_user(ctx.guild.id, member.id)
        old_bal = data.get("balance", 0)
        old_bank = data.get("bank", 0)
        data["balance"] = 0
        data["bank"] = 0
        _save_economy()

        embed = discord.Embed(
            title="♻️ Reset Money",
            description=f"Flous dyal {member.mention} tms7ou!",
            color=discord.Color.red(),
        )
        embed.add_field(name="📉 Qbel", value=f"👛 `{old_bal:,}` | 🏦 `{old_bank:,}`", inline=False)
        embed.add_field(name="📈 Daba", value="👛 `0` | 🏦 `0`", inline=False)
        embed.set_footer(text=f"Par {ctx.author.name}")
        await ctx.send(embed=embed)

    @commands.command(name="resetcasino")
    async def resetcasino_prefix(self, ctx: commands.Context):
        """&resetcasino — [ADMIN] Reset flous dyal GA3 l-users"""
        if not has_reset_role(ctx.author):
            return await ctx.send("❌ Ma 3endekch l-7a9 b had commande!")

        guild_data = ECONOMY.get(ctx.guild.id, {})
        count = 0
        total_wiped = 0
        for user_id, data in guild_data.items():
            total_wiped += data.get("balance", 0) + data.get("bank", 0)
            data["balance"] = 0
            data["bank"] = 0
            data["last_daily"] = None
            data["last_work"] = None
            data["last_rob"] = None
            data["last_collect"] = None
            count += 1
        _save_economy()

        embed = discord.Embed(
            title="💥 Casino Reset!",
            description="**Ga3 l-flous f had serveur tms7ou!**",
            color=discord.Color.dark_red(),
        )
        embed.add_field(name="👥 Users", value=f"`{count:,}`", inline=True)
        embed.add_field(name="🗑️ Total m7i", value=f"`{total_wiped:,}` 🪙", inline=True)
        embed.set_footer(text=f"Par {ctx.author.name}")
        await ctx.send(embed=embed)

    @commands.command(name="resetme")
    async def resetme_prefix(self, ctx: commands.Context):
        """&resetme — Reset flousek nta (kolchi 9ader yst3mlha)"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        old_bal = data.get("balance", 0)
        old_bank = data.get("bank", 0)

        if old_bal == 0 and old_bank == 0:
            return await ctx.send("❌ Ma 3endekch flous bach tresethom!")

        data["balance"] = 0
        data["bank"] = 0
        _save_economy()

        embed = discord.Embed(
            title="♻️ Reset dyalek",
            description=f"Flousek tms7ou, {ctx.author.mention}!",
            color=discord.Color.orange(),
        )
        embed.add_field(name="📉 Qbel", value=f"👛 `{old_bal:,}` | 🏦 `{old_bank:,}`", inline=False)
        embed.add_field(name="📈 Daba", value="👛 `0` | 🏦 `0`", inline=False)
        embed.set_footer(text="Kolchi 9ader yst3ml had commande")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))