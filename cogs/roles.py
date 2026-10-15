# =====================================================================
# ─── ROLE MANAGEMENT — Giverole, Removerole, Massrole
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.checks import require_role, require_role_prefix


class Roles(commands.Cog):
    """Role management: giverole, removerole, massrole"""

    def __init__(self, bot):
        self.bot = bot

    def _check_hierarchy(self, author: discord.Member, role: discord.Role) -> bool:
        if author.id == author.guild.owner_id:
            return True
        return role < author.top_role

    # ═══════════════════════════════════════════════════════════
    # ─── /giverole
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="giverole", description="3ti role l member")
    @app_commands.describe(member="L-member", role="Role li bghiti t3ti")
    @require_role("giverole")
    async def giverole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if not self._check_hierarchy(interaction.user, role):
            return await interaction.response.send_message(
                "❌ Ma tqderch t3ti role fo9 dyalek!", ephemeral=True
            )

        bot_member = interaction.guild.get_member(self.bot.user.id)
        if bot_member and role >= bot_member.top_role:
            return await interaction.response.send_message(
                "❌ Role fo9 role dyal bot!", ephemeral=True
            )

        if role in member.roles:
            return await interaction.response.send_message(
                f"⚠️ {member.mention} deja 3endou {role.mention}!", ephemeral=True
            )

        try:
            await member.add_roles(role, reason=f"Par {interaction.user.name}")
            embed = discord.Embed(
                title="✅ Role Added",
                description=f"**{role.mention}** t-3ta l {member.mention}",
                color=discord.Color.green(),
            )
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Ma 3ndich permission!", ephemeral=True)

    @commands.command(name="giverole")
    @require_role_prefix("giverole")
    @commands.bot_has_permissions(manage_roles=True)
    async def giverole_prefix(self, ctx: commands.Context, member: discord.Member, *, role: discord.Role):
        """&giverole @user @role"""
        if not self._check_hierarchy(ctx.author, role):
            return await ctx.send("❌ Role fo9 dyalek!")
        if role in member.roles:
            return await ctx.send(f"⚠️ Deja 3endou {role.mention}!")
        try:
            await member.add_roles(role, reason=f"Par {ctx.author.name}")
            await ctx.send(f"✅ **{role.mention}** t-3ta l {member.mention}")
        except discord.Forbidden:
            await ctx.send("❌ Ma 3ndich permission!")

    # ═══════════════════════════════════════════════════════════
    # ─── /removerole
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="removerole", description="Hyed role mn member")
    @app_commands.describe(member="L-member", role="Role li bghiti thyed")
    @require_role("removerole")
    async def removerole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if not self._check_hierarchy(interaction.user, role):
            return await interaction.response.send_message(
                "❌ Ma tqderch thyed role fo9 dyalek!", ephemeral=True
            )

        if role not in member.roles:
            return await interaction.response.send_message(
                f"⚠️ {member.mention} ma 3endouch {role.mention}!", ephemeral=True
            )

        try:
            await member.remove_roles(role, reason=f"Par {interaction.user.name}")
            embed = discord.Embed(
                title="✅ Role Removed",
                description=f"**{role.mention}** t-hyed mn {member.mention}",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Ma 3ndich permission!", ephemeral=True)

    @commands.command(name="removerole")
    @require_role_prefix("removerole")
    @commands.bot_has_permissions(manage_roles=True)
    async def removerole_prefix(self, ctx: commands.Context, member: discord.Member, *, role: discord.Role):
        """&removerole @user @role"""
        if not self._check_hierarchy(ctx.author, role):
            return await ctx.send("❌ Role fo9 dyalek!")
        if role not in member.roles:
            return await ctx.send(f"⚠️ Ma 3endouch {role.mention}!")
        try:
            await member.remove_roles(role, reason=f"Par {ctx.author.name}")
            await ctx.send(f"✅ **{role.mention}** t-hyed mn {member.mention}")
        except discord.Forbidden:
            await ctx.send("❌ Ma 3ndich permission!")

    # ═══════════════════════════════════════════════════════════
    # ─── /massrole — 3ti role l kolchi (rate-limit safe)
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="massrole", description="3ti role l ga3 l-members")
    @app_commands.describe(role="Role li bghiti t3ti", bots="3ti l bots?")
    @require_role("massrole")
    async def massrole(self, interaction: discord.Interaction, role: discord.Role, bots: bool = False):
        if not self._check_hierarchy(interaction.user, role):
            return await interaction.response.send_message("❌ Role fo9 dyalek!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        count = 0
        failed = 0
        # ✅ FIX: Semaphore bash n7tarmo rate-limits
        sem = asyncio.Semaphore(5)

        async def add_role_safe(member):
            nonlocal count, failed
            async with sem:
                try:
                    await member.add_roles(role, reason=f"Massrole par {interaction.user.name}")
                    count += 1
                except Exception:
                    failed += 1
                await asyncio.sleep(0.3)  # ← delay bin requests

        tasks = []
        for member in interaction.guild.members:
            if member.bot and not bots:
                continue
            if role in member.roles:
                continue
            tasks.append(add_role_safe(member))

        await asyncio.gather(*tasks, return_exceptions=True)

        await interaction.followup.send(
            f"✅ **{role.mention}** t-3ta l `{count}` members!\n"
            f"❌ Failed: `{failed}`",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Roles(bot))