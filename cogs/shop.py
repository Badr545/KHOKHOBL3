# cogs/shop.py
# =====================================================================
# ─── SHOP — Chri roles b flousek + Income system (&collect)
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import json
import os

from data_manager import ECONOMY, save_economy as _save_economy


SHOP_FILE = "data/shop.json"
COLLECT_COOLDOWN = timedelta(minutes=30)

# ─── SHOP_ITEMS — mutable dict (ta3refha secret_admin)
#     {key: {name, price, role, desc, income}}
SHOP_ITEMS: dict = {}

# ─── ROLES_INCOME — Roles li kay3tiw income WALAKIN ma kaynin fl shop ───
#     {role_id (str): income}
#     ⚠️ role_id machi name — Copy ID mn Discord
ROLES_INCOME: dict = {
    "1370937530459099246": 10000000000,#founder
    "1550652279013638245": 200000,#casino manager
}


# ═══════════════════════════════════════════════════════════════════
# ─── PERSISTENCE (mutate in place — bach references yb9aw s7a7)
# ═══════════════════════════════════════════════════════════════════
def _load_shop():
    data = {}
    if os.path.exists(SHOP_FILE):
        try:
            with open(SHOP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠️ Load shop failed: {e}")
            data = {}
    SHOP_ITEMS.clear()
    SHOP_ITEMS.update(data)
    print(f"✅ Loaded shop: {len(SHOP_ITEMS)} items")


def _save_shop():
    os.makedirs("data", exist_ok=True)
    try:
        with open(SHOP_FILE, "w", encoding="utf-8") as f:
            json.dump(SHOP_ITEMS, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Save shop failed: {e}")


# ─── Public API l secret_admin ───
def get_shop_items() -> dict:
    return SHOP_ITEMS


def add_shop_item(key: str, data: dict) -> bool:
    key = key.strip().lower()
    if not key:
        return False
    SHOP_ITEMS[key] = data
    _save_shop()
    return True


def remove_shop_item(key: str) -> bool:
    key = key.strip().lower()
    if key in SHOP_ITEMS:
        SHOP_ITEMS.pop(key)
        _save_shop()
        return True
    return False


def update_shop_item(key: str, field: str, value) -> bool:
    key = key.strip().lower()
    if key not in SHOP_ITEMS:
        return False
    SHOP_ITEMS[key][field] = value
    _save_shop()
    return True


_load_shop()


# ═══════════════════════════════════════════════════════════════════
# ─── COG
# ═══════════════════════════════════════════════════════════════════
class Shop(commands.Cog):
    """Shop: chri roles + income via &collect (30min)"""

    def __init__(self, bot):
        self.bot = bot

    def _get_user(self, guild_id: int, user_id: int) -> dict:
        ECONOMY.setdefault(guild_id, {}).setdefault(user_id, {
            "balance": 0, "bank": 0, "inventory": [],
            "last_collect": None,
        })
        return ECONOMY[guild_id][user_id]

    def _get_user_income_items(self, member: discord.Member) -> list:
        """List of (key, item) — roles li 3end user (shop + bonus)."""
        owned = []
        member_roles = {r.name for r in member.roles}
        member_role_ids = {str(r.id) for r in member.roles}

        # ── Shop roles ──
        for key, item in SHOP_ITEMS.items():
            role_name = item.get("role")
            if role_name and role_name in member_roles:
                owned.append((key, item))

        # ── Bonus roles (income only — machi fl shop) ──
        for role_id, income in ROLES_INCOME.items():
            if role_id in member_role_ids:
                role = discord.utils.get(member.roles, id=int(role_id))
                name = role.name if role else f"Role {role_id}"
                owned.append((f"bonus_{role_id}", {
                    "name": f"⭐ {name}",
                    "income": income,
                    "price": 0,
                    "role": name,
                    "desc": "Bonus role (income only)",
                }))

        return owned

    def _build_shop_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🛒 **Shop**",
            description=(
                "Chri b `/buy <key>` wla `&buy <key>`\n"
                "💰 Kol role kat3tik **income** kola **30min** b `/collect` wla `&collect`"
            ),
            color=discord.Color.gold(),
        )
        roles = []
        colors = []
        for key, item in SHOP_ITEMS.items():
            income = item.get("income", 0)
            income_line = f"\n> 💰 Income: `{income:,}` 🪙 / 30min" if income > 0 else ""
            line = (
                f"{item['name']} — `{item['price']:,}` 🪙\n"
                f"> {item.get('desc', '')}{income_line}\n"
                f"> Key: `{key}`"
            )
            if "color" in key.lower():
                colors.append(line)
            else:
                roles.append(line)

        if roles:
            embed.add_field(name="👑 **Roles**", value="\n\n".join(roles[:8]), inline=False)
        if colors:
            embed.add_field(name="🎨 **Colors**", value="\n\n".join(colors[:8]), inline=False)

        if not roles and not colors and not ROLES_INCOME:
            embed.description = "❌ Shop khawi! @⚜️ Community Manager zid items mn panel."
        embed.set_footer(text="Powered by Khokho Bl3 Bot")
        return embed

    # ═══════════════════════════════════════════════════════════
    # ─── /shop
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="shop", description="Chouf l-shop")
    async def shop(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self._build_shop_embed())

    # ═══════════════════════════════════════════════════════════
    # ─── /buy
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="buy", description="Chri mn shop")
    @app_commands.describe(item_key="Key dyal item (chouf /shop)")
    async def buy(self, interaction: discord.Interaction, item_key: str):
        item = SHOP_ITEMS.get(item_key.lower())
        if not item:
            return await interaction.response.send_message(
                "❌ Item ma kaynch! Chouf `/shop`.", ephemeral=True,
            )

        data = self._get_user(interaction.guild.id, interaction.user.id)

        if data["balance"] < item["price"]:
            return await interaction.response.send_message(
                f"❌ Khass `{item['price']:,}` 🪙, 3endek ghir `{data['balance']:,}` 🪙",
                ephemeral=True,
            )

        role_name = item.get("role")
        if role_name:
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if role and role in interaction.user.roles:
                return await interaction.response.send_message(
                    f"⚠️ Deja 3endek **{item['name']}**!", ephemeral=True,
                )

        await interaction.response.defer()

        data["balance"] -= item["price"]

        if role_name:
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if role is None:
                try:
                    role = await interaction.guild.create_role(
                        name=role_name,
                        reason=f"Shop purchase by {interaction.user.name}",
                    )
                except discord.Forbidden:
                    data["balance"] += item["price"]
                    _save_economy()
                    return await interaction.followup.send("❌ Ma qdertch nsayeb role!", ephemeral=True)

            try:
                await interaction.user.add_roles(role, reason=f"Shop: {item['name']}")
            except discord.Forbidden:
                data["balance"] += item["price"]
                _save_economy()
                return await interaction.followup.send("❌ Ma qdertch n3tik role!", ephemeral=True)

        _save_economy()

        embed = discord.Embed(
            title="✅ **Purchase Success!**",
            description=f"Chriti **{item['name']}** b `{item['price']:,}` 🪙!",
            color=discord.Color.green(),
        )
        if item.get("income", 0) > 0:
            embed.add_field(
                name="💰 Income",
                value=f"`{item['income']:,}` 🪙 kola 30min\nSt3mel `/collect` wla `&collect`",
                inline=False,
            )
        embed.set_footer(text=f"Balance daba: {data['balance']:,} 🪙")
        await interaction.followup.send(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /collect
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="collect", description="Jme3 income mn roles dyalk (kola 30min)")
    async def collect(self, interaction: discord.Interaction):
        data = self._get_user(interaction.guild.id, interaction.user.id)
        now = datetime.now()

        if data.get("last_collect"):
            try:
                last = datetime.fromisoformat(data["last_collect"])
                if now - last < COLLECT_COOLDOWN:
                    remaining = COLLECT_COOLDOWN - (now - last)
                    m = remaining.seconds // 60
                    s = remaining.seconds % 60
                    return await interaction.response.send_message(
                        f"⏰ 3awed mn ba3d `{m}m {s}s`!", ephemeral=True,
                    )
            except Exception:
                pass

        owned = self._get_user_income_items(interaction.user)
        if not owned:
            return await interaction.response.send_message(
                "❌ Ma 3endekch roles li kay3tiw income!\nChouf `/shop`.",
                ephemeral=True,
            )

        total = sum(item.get("income", 0) for _, item in owned)
        if total <= 0:
            return await interaction.response.send_message(
                "❌ Roles dyalk ma kay3tiwch income (0 🪙).", ephemeral=True,
            )

        data["balance"] = data.get("balance", 0) + total
        data["last_collect"] = now.isoformat()
        _save_economy()

        roles_lines = "\n".join(
            f"• {item['name']} → `{item.get('income', 0):,}` 🪙" for _, item in owned
        )
        embed = discord.Embed(
            title="💰 Collect!",
            description=f"**+{total:,}** 🪙 dkhlou l-wallet!",
            color=discord.Color.green(),
        )
        embed.add_field(name="📋 Roles", value=roles_lines, inline=False)
        embed.set_footer(text=f"Balance: {data['balance']:,} 🪙 • 3awed mn ba3d 30min")
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── PREFIX
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="shop")
    async def shop_prefix(self, ctx: commands.Context):
        """&shop"""
        await ctx.send(embed=self._build_shop_embed())

    @commands.command(name="buy")
    async def buy_prefix(self, ctx: commands.Context, item_key: str):
        """&buy <key>"""
        item = SHOP_ITEMS.get(item_key.lower())
        if not item:
            return await ctx.send("❌ Item ma kaynch! Chouf `&shop`.")
        data = self._get_user(ctx.guild.id, ctx.author.id)
        if data["balance"] < item["price"]:
            return await ctx.send(f"❌ Khass `{item['price']:,}` 🪙!")

        role_name = item.get("role")
        if role_name:
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role and role in ctx.author.roles:
                return await ctx.send(f"⚠️ Deja 3endek **{item['name']}**!")

        data["balance"] -= item["price"]
        if role_name:
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role is None:
                try:
                    role = await ctx.guild.create_role(name=role_name)
                except discord.Forbidden:
                    data["balance"] += item["price"]
                    return await ctx.send("❌ Ma 3ndich permission!")
            try:
                await ctx.author.add_roles(role, reason=f"Shop: {item['name']}")
            except discord.Forbidden:
                data["balance"] += item["price"]
                return await ctx.send("❌ Ma 3ndich permission!")
        _save_economy()

        msg = f"✅ Chriti **{item['name']}**! Balance: `{data['balance']:,}` 🪙"
        if item.get("income", 0) > 0:
            msg += f"\n💰 Income: `{item['income']:,}` 🪙 / 30min — St3mel `&collect`"
        await ctx.send(msg)

    @commands.command(name="collect")
    async def collect_prefix(self, ctx: commands.Context):
        """&collect — Jme3 income mn roles (kola 30min)"""
        data = self._get_user(ctx.guild.id, ctx.author.id)
        now = datetime.now()

        if data.get("last_collect"):
            try:
                last = datetime.fromisoformat(data["last_collect"])
                if now - last < COLLECT_COOLDOWN:
                    remaining = COLLECT_COOLDOWN - (now - last)
                    m = remaining.seconds // 60
                    s = remaining.seconds % 60
                    return await ctx.send(f"⏰ 3awed mn ba3d `{m}m {s}s`!")
            except Exception:
                pass

        owned = self._get_user_income_items(ctx.author)
        if not owned:
            return await ctx.send("❌ Ma 3endekch roles li kay3tiw income!\nChouf `&shop`.")

        total = sum(item.get("income", 0) for _, item in owned)
        if total <= 0:
            return await ctx.send("❌ Ma kaynch income!")

        data["balance"] = data.get("balance", 0) + total
        data["last_collect"] = now.isoformat()
        _save_economy()

        roles_lines = "\n".join(
            f"• {item['name']} → `{item.get('income', 0):,}` 🪙" for _, item in owned
        )
        embed = discord.Embed(
            title="💰 Collect!",
            description=f"**+{total:,}** 🪙!",
            color=discord.Color.green(),
        )
        embed.add_field(name="📋 Roles", value=roles_lines, inline=False)
        embed.set_footer(text=f"Balance: {data['balance']:,} 🪙")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Shop(bot))