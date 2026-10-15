# cogs/welcome.py
# =====================================================================
# ─── WELCOME SYSTEM — Auto Role + Welcome + DM + Leaves
# =====================================================================
import discord
from discord.ext import commands
from datetime import datetime
import asyncio
import time
from botconfig import (
    WELCOME_CHANNEL_NAME,
    LEAVES_CHANNEL_NAME,
    VERIFIED_ROLE_NAME,
    AUTO_ROLE_ENABLED,
    WELCOME_DM_ENABLED,
)


class Welcome(commands.Cog):
    """Welcome system: auto role + welcome message + DM + leaves"""

    def __init__(self, bot):
        self.bot = bot
        self._dm_lock = asyncio.Lock()
        self._dm_sent = {}

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        print(f"👋 {member.name} ({member.id}) dkhl l **{member.guild.name}**")

        await asyncio.sleep(2)

        if AUTO_ROLE_ENABLED:
            await self._give_verified_role(member)

        await self._send_welcome_message(member)

        if WELCOME_DM_ENABLED:
            await asyncio.sleep(1)
            await self._send_welcome_dm(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        print(f"🚪 {member.name} khrj mn **{member.guild.name}**")

        channel = discord.utils.get(member.guild.text_channels, name=LEAVES_CHANNEL_NAME)

        if channel is None:
            print(f"⚠️ Channel '{LEAVES_CHANNEL_NAME}' ma kaynach!")
            return

        embed = discord.Embed(
            title="👋 Bslama!",
            description=(
                f"**{member.name}** khlla l-server... 😢\n\n"
                f"**Kan m3ana mn:** {member.joined_at.strftime('%d/%m/%Y') if member.joined_at else '?'}\n"
                f"**Roles:** `{len([r for r in member.roles if not r.is_default()])}`\n\n"
                f"Allah y-sahel f triqo! 🌟"
            ),
            color=discord.Color.from_rgb(231, 76, 60),
            timestamp=datetime.now(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Members daba: {member.guild.member_count}")

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            print(f"❌ Ma 3ndich permission f #{channel.name}!")

    # ═══════════════════════════════════════════════════════════
    # ─── HELPERS
    # ═══════════════════════════════════════════════════════════

    async def _give_verified_role(self, member: discord.Member):
        role = discord.utils.get(member.guild.roles, name=VERIFIED_ROLE_NAME)

        if role is None:
            print(f"⚠️ Role '{VERIFIED_ROLE_NAME}' ma kaynach! Sayeb role b had smiya.")
            return

        bot_member = member.guild.get_member(self.bot.user.id)
        if bot_member is None:
            print("❌ Bot member ma l9itouch f guild!")
            return

        # ✅ DEBUG LOGS
        print(f"🔍 Bot top role: '{bot_member.top_role.name}' (pos: {bot_member.top_role.position})")
        print(f"🔍 Target role: '{role.name}' (pos: {role.position})")

        # ✅ FIX: Bot khass ykoun strictly fo9 target role
        if bot_member.top_role.position <= role.position:
            print(f"❌ Bot role '{bot_member.top_role.name}' TA7T wla ÉGAL '{role.name}'!")
            print(f"   → 7arrek role dyal bot FO9 '{role.name}' f Server Settings > Roles")
            return

        # ✅ Check bot permissions
        if not bot_member.guild_permissions.manage_roles:
            print(f"❌ Bot ma 3endou 'Manage Roles' permission!")
            return

        try:
            await member.add_roles(role, reason="Auto-role on join")
            print(f"✅ {member.name} t-3ta role **{VERIFIED_ROLE_NAME}**")
        except discord.Forbidden:
            print(f"❌ Bot ma 3endich permission (Manage Roles)!")
        except Exception as e:
            print(f"❌ Erreur auto-role: {e}")

    async def _send_welcome_message(self, member: discord.Member):
        channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL_NAME)

        if channel is None:
            print(f"⚠️ Channel '{WELCOME_CHANNEL_NAME}' ma kaynach!")
            return

        embed = discord.Embed(
            title=f"🎉 Marhba bik f {member.guild.name}!",
            description=(
                f"### 👋 Salam {member.mention}!\n"
                f"7na mse7bin bik f **{member.guild.name}**! 🥳\n\n"
                f"📜 **9ra les règles** 9bel ma tbda\n"
                f"🎭 **Role** dyalek t-3ta automatique\n"
                f"💬 **Stenana** f chat\n\n"
                f"**Ntmennaw lik wa9t zwin m3ana!** 💚"
            ),
            color=discord.Color.from_rgb(88, 101, 242),
            timestamp=datetime.now(),
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="👤 Username", value=f"`{member.name}`", inline=True)
        embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
        embed.add_field(
            name="📅 Account tsayeb",
            value=f"<t:{int(member.created_at.timestamp())}:R>",
            inline=True,
        )
        embed.add_field(name="👥 Members", value=f"`{member.guild.member_count}`", inline=True)
        embed.add_field(name="📆 Dkhel daba", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
        embed.add_field(name="🎭 Role", value=f"`{VERIFIED_ROLE_NAME}`", inline=True)

        embed.set_footer(
            text=f"Member #{member.guild.member_count} • {member.guild.name}",
            icon_url=member.guild.icon.url if member.guild.icon else None,
        )

        try:
            await channel.send(content=f"👋 {member.mention}", embed=embed)
        except discord.Forbidden:
            print(f"❌ Bot ma 3endich permission f #{channel.name}!")

    async def _send_welcome_dm(self, member: discord.Member):
        now = time.time()
        last = self._dm_sent.get(member.id, 0)
        if now - last < 3600:
            print(f"⏭️ Skip DM l {member.name} (cooldown)")
            return

        embed = discord.Embed(
            title=f"👋 Marhba bik f {member.guild.name}!",
            description=(
                f"### Salam **{member.name}**! 🎉\n\n"
                f"7na mse7bin bik f **{member.guild.name}**!\n\n"
                f"🔗 **Chno tdir daba:**\n"
                f"1️⃣ Zor les channels\n"
                f"2️⃣ 9ra les règles\n"
                f"3️⃣ 3ayet 3la chi wa7ed ila 3endek so'al\n\n"
                f"**Ntmennaw lik wa9t zwin!** 💚"
            ),
            color=discord.Color.from_rgb(88, 101, 242),
            timestamp=datetime.now(),
        )

        if member.guild.icon:
            embed.set_thumbnail(url=member.guild.icon.url)

        embed.set_footer(text=f"{member.guild.name} • Powered by Khokho Bl3 Bot")

        async with self._dm_lock:
            try:
                await member.send(embed=embed)
                self._dm_sent[member.id] = now
                print(f"📩 DM sift l {member.name}")
            except discord.Forbidden:
                print(f"⚠️ DM msdoud 3la {member.name}")
            except discord.HTTPException as e:
                if e.code == 40003:
                    print(f"⚠️ Rate limited f DM l {member.name} — skip")
                else:
                    print(f"❌ DM HTTP error l {member.name}: {e}")
            except Exception as e:
                print(f"❌ DM error l {member.name}: {e}")

            await asyncio.sleep(1.5)


async def setup(bot):
    await bot.add_cog(Welcome(bot))