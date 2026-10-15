# cogs/premium.py
# =====================================================================
# ─── PREMIUM + LICENSE SYSTEM — Sellable tiers
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import secrets
import uuid
from datetime import datetime, timedelta

DATA_FILE = "data/premium.json"


def _load():
    if not os.path.exists(DATA_FILE):
        return {"guilds": {}, "codes": {}, "logs": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        raw["guilds"] = {int(g): v for g, v in raw.get("guilds", {}).items()}
        return raw
    except Exception:
        return {"guilds": {}, "codes": {}, "logs": []}


def _save(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


PREMIUM = _load()


TIERS = {
    "free": {
        "name": "🆓 Free",
        "color": 0x95A5A6,
        "limits": {
            "gambling_max": 10_000,
            "daily_xp_mult": 1.0,
            "custom_embeds": False,
            "priority_support": False,
            "businesses_max": 1,
            "stocks_max_shares": 100,
        },
    },
    "pro": {
        "name": "⭐ Pro",
        "color": 0x3498DB,
        "limits": {
            "gambling_max": 100_000,
            "daily_xp_mult": 1.5,
            "custom_embeds": True,
            "priority_support": True,
            "businesses_max": 3,
            "stocks_max_shares": 1000,
        },
    },
    "premium": {
        "name": "👑 Premium",
        "color": 0xF1C40F,
        "limits": {
            "gambling_max": -1,  # unlimited
            "daily_xp_mult": 3.0,
            "custom_embeds": True,
            "priority_support": True,
            "businesses_max": 10,
            "stocks_max_shares": -1,
        },
    },
    "lifetime": {
        "name": "💎 Lifetime",
        "color": 0xE91E63,
        "limits": {
            "gambling_max": -1,
            "daily_xp_mult": 5.0,
            "custom_embeds": True,
            "priority_support": True,
            "businesses_max": -1,
            "stocks_max_shares": -1,
        },
    },
}


def get_tier(guild_id: int) -> str:
    """Rje3 tier ism dyal guild."""
    data = PREMIUM["guilds"].get(guild_id, {})
    tier = data.get("tier", "free")
    expires = data.get("expires_at")
    if expires and tier != "lifetime":
        try:
            if datetime.fromisoformat(expires) < datetime.now():
                data["tier"] = "free"
                _save(PREMIUM)
                return "free"
        except Exception:
            pass
    return tier


def get_limits(guild_id: int) -> dict:
    tier = get_tier(guild_id)
    return TIERS[tier]["limits"]


def is_premium(guild_id: int) -> bool:
    return get_tier(guild_id) != "free"


def _log(action: str, actor: str, note: str = ""):
    PREMIUM["logs"].append({
        "action": action, "actor": actor, "note": note,
        "time": datetime.now().isoformat(),
    })
    PREMIUM["logs"] = PREMIUM["logs"][-200:]


class Premium(commands.Cog):
    """Premium + License system"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════════════════════════
    # ─── /premium — Info
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="premium", description="💎 Premium info dyal had server")
    async def premium_info(self, it: discord.Interaction):
        tier = get_tier(it.guild.id)
        t = TIERS[tier]
        data = PREMIUM["guilds"].get(it.guild.id, {})

        embed = discord.Embed(
            title=f"💎 Premium Status",
            description=f"**Tier:** {t['name']}",
            color=discord.Color(t["color"]),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="🏠 Server", value=it.guild.name, inline=False)

        if data.get("expires_at"):
            try:
                exp = datetime.fromisoformat(data["expires_at"])
                if tier == "lifetime":
                    embed.add_field(name="♾️ Expires", value="**Lifetime**", inline=True)
                else:
                    embed.add_field(name="📅 Expires", value=f"<t:{int(exp.timestamp())}:R>", inline=True)
            except Exception:
                pass

        lim = t["limits"]
        embed.add_field(name="🎰 Gambling Max", value=f"`{lim['gambling_max']:,}`" if lim["gambling_max"] > 0 else "**∞**", inline=True)
        embed.add_field(name="⭐ XP Multiplier", value=f"`{lim['daily_xp_mult']}x`", inline=True)
        embed.add_field(name="🏢 Businesses Max", value=f"`{lim['businesses_max']}`" if lim["businesses_max"] > 0 else "**∞**", inline=True)
        embed.add_field(name="🎨 Custom Embeds", value=f"`{lim['custom_embeds']}`", inline=True)
        embed.add_field(name="🚀 Priority Support", value=f"`{lim['priority_support']}`", inline=True)
        embed.add_field(name="📈 Max Shares", value=f"`{lim['stocks_max_shares']}`" if lim["stocks_max_shares"] > 0 else "**∞**", inline=True)

        embed.set_footer(text="Redeem code: /premium_redeem <code>")
        await it.response.send_message(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /premium_redeem — Redeem code
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="premium_redeem", description="🎟️ Redeem premium code")
    @app_commands.describe(code="Code dyalek")
    async def premium_redeem(self, it: discord.Interaction, code: str):
        code = code.upper().strip()
        cdata = PREMIUM["codes"].get(code)
        if not cdata:
            return await it.response.send_message("❌ Code ghalat!", ephemeral=True)
        if cdata.get("used_by"):
            return await it.response.send_message("❌ Code deja mst3ml!", ephemeral=True)

        tier = cdata["tier"]
        duration_days = cdata.get("duration_days", 30)

        gdata = PREMIUM["guilds"].setdefault(it.guild.id, {})
        if duration_days == 0:  # lifetime
            gdata["tier"] = tier
            gdata["expires_at"] = None
            gdata["lifetime"] = True
        else:
            now = datetime.now()
            # Extend ila deja premium
            current_exp = gdata.get("expires_at")
            if current_exp:
                try:
                    cur = datetime.fromisoformat(current_exp)
                    if cur > now:
                        now = cur
                except Exception:
                    pass
            gdata["tier"] = tier
            gdata["expires_at"] = (now + timedelta(days=duration_days)).isoformat()

        gdata["redeemed_by"] = it.user.id
        gdata["redeemed_at"] = datetime.now().isoformat()

        cdata["used_by"] = it.user.id
        cdata["used_at"] = datetime.now().isoformat()
        cdata["used_in"] = it.guild.id

        _save(PREMIUM)
        _log("redeem", f"{it.user} ({it.user.id})", f"{code} → {tier} ({duration_days}d)")

        embed = discord.Embed(
            title="🎉 Premium Activated!",
            description=f"**Tier:** {TIERS[tier]['name']}\n"
                        f"**Duration:** {'∞ Lifetime' if duration_days == 0 else f'{duration_days} days'}",
            color=discord.Color(tier and TIERS[tier]["color"] or 0xF1C40F),
        )
        await it.response.send_message(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── ADMIN: Generate code
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="gencode")
    @commands.is_owner()
    async def gen_code(self, ctx: commands.Context, tier: str, days: int = 30, count: int = 1):
        """`&gencode <free|pro|premium|lifetime> <days> [count]` — Owner only"""
        tier = tier.lower()
        if tier not in TIERS or tier == "free":
            return await ctx.send(f"❌ Tier: `pro` / `premium` / `lifetime`")
        if days < 0 or days > 3650:
            return await ctx.send("❌ Days: 0-3650 (0 = lifetime)")
        if count < 1 or count > 20:
            return await ctx.send("❌ Count: 1-20")

        codes = []
        for _ in range(count):
            code = f"KHK-{tier[:3].upper()}-{secrets.token_hex(4).upper()}"
            PREMIUM["codes"][code] = {
                "tier": tier,
                "duration_days": days,
                "created_at": datetime.now().isoformat(),
                "created_by": ctx.author.id,
                "used_by": None,
            }
            codes.append(code)
        _save(PREMIUM)
        _log("gen_codes", str(ctx.author), f"{tier} {days}d ×{count}")

        embed = discord.Embed(
            title=f"🎟️ Generated {count} code(s)",
            description=f"**Tier:** {TIERS[tier]['name']}\n"
                        f"**Duration:** {'∞' if days == 0 else f'{days}d'}",
            color=discord.Color.green(),
        )
        embed.add_field(name="Codes", value="\n".join(f"`{c}`" for c in codes), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="revokecode")
    @commands.is_owner()
    async def revoke_code(self, ctx: commands.Context, code: str):
        """`&revokecode <code>` — Owner"""
        code = code.upper()
        if code in PREMIUM["codes"]:
            PREMIUM["codes"].pop(code)
            _save(PREMIUM)
            return await ctx.send(f"✅ Code `{code}` revoked!")
        await ctx.send("❌ Code ma kaynch!")

    @commands.command(name="revokeguild")
    @commands.is_owner()
    async def revoke_guild(self, ctx: commands.Context, guild_id: int):
        """`&revokeguild <id>` — Owner"""
        if guild_id in PREMIUM["guilds"]:
            PREMIUM["guilds"][guild_id]["tier"] = "free"
            PREMIUM["guilds"][guild_id]["expires_at"] = None
            _save(PREMIUM)
            return await ctx.send(f"✅ Guild `{guild_id}` downgraded to free")
        await ctx.send("❌ Guild ma kaynch!")

    @commands.command(name="premiumlist")
    @commands.is_owner()
    async def premium_list(self, ctx: commands.Context):
        """`&premiumlist` — Owner"""
        guilds = PREMIUM["guilds"]
        codes = PREMIUM["codes"]
        unused = [c for c, d in codes.items() if not d.get("used_by")]

        embed = discord.Embed(title="💎 Premium Overview", color=discord.Color.gold())
        embed.add_field(name="🏠 Premium Guilds", value=f"`{len([g for g in guilds.values() if g.get('tier','free') != 'free'])}`", inline=True)
        embed.add_field(name="🎟️ Total Codes", value=f"`{len(codes)}`", inline=True)
        embed.add_field(name="🆓 Unused Codes", value=f"`{len(unused)}`", inline=True)

        if unused:
            embed.add_field(
                name="Unused (last 10)",
                value="\n".join(f"`{c}` → {codes[c]['tier']}" for c in unused[:10]),
                inline=False,
            )

        await ctx.send(embed=embed)


# ═══════════════════════════════════════════════════════════════════
# ─── HELPER for other cogs
# ═══════════════════════════════════════════════════════════════════
def check_gambling_limit(guild_id: int, amount: int) -> tuple[bool, str]:
    """Rje3 (ok, msg)."""
    lim = get_limits(guild_id)
    max_bet = lim["gambling_max"]
    if max_bet == -1:
        return True, ""
    if amount > max_bet:
        return False, f"❌ Max bet dyalek: `{max_bet:,}` (upgrade l premium!)"
    return True, ""


async def setup(bot):
    await bot.add_cog(Premium(bot))