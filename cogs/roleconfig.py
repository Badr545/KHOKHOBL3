# =====================================================================
# ─── ROLE CONFIG COMMANDS (Admin only)
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
import botconfig


class RoleConfig(commands.Cog):
    """Admin commands bash tbdel roles dinamiquement"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addmod", description="Zid role f Moderators")
    @app_commands.describe(role="Role li bghiti tzid")
    async def addmod(self, interaction: discord.Interaction, role: discord.Role):
        if not self._is_admin(interaction.user):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)

        if role.name in botconfig.MODERATOR_ROLES:
            return await interaction.response.send_message(f"⚠️ `{role.name}` deja kayn!", ephemeral=True)

        botconfig.MODERATOR_ROLES.append(role.name)
        await interaction.response.send_message(f"✅ `{role.name}` tzad f Moderators!")

    @app_commands.command(name="removemod", description="Hyed role mn Moderators")
    @app_commands.describe(role="Role li bghiti thyed")
    async def removemod(self, interaction: discord.Interaction, role: discord.Role):
        if not self._is_admin(interaction.user):
            return await interaction.response.send_message("❌ Admin only!", ephemeral=True)

        if role.name not in botconfig.MODERATOR_ROLES:
            return await interaction.response.send_message(f"⚠️ `{role.name}` ma kaynch!", ephemeral=True)

        botconfig.MODERATOR_ROLES.remove(role.name)
        await interaction.response.send_message(f"✅ `{role.name}` thyed mn Moderators!")

    @app_commands.command(name="listroles", description="Chouf roles configurés")
    async def listroles(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🔒 Roles Configuration", color=discord.Color.red())
        embed.add_field(name="👑 Admin", value="\n".join(f"`{r}`" for r in botconfig.ADMIN_ROLES) or "Khawi", inline=False)
        embed.add_field(name="🛡️ Moderator", value="\n".join(f"`{r}`" for r in botconfig.MODERATOR_ROLES) or "Khawi", inline=False)
        embed.add_field(name="💚 Helper", value="\n".join(f"`{r}`" for r in botconfig.HELPER_ROLES) or "Khawi", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="checkperm", description="Check permission dyal chi command")
    @app_commands.describe(command="Smiya dyal command")
    async def checkperm(self, interaction: discord.Interaction, command: str):
        from botconfig import user_has_permission, get_required_roles
        has = user_has_permission(interaction.user, command)
        required = get_required_roles(command)
        if has:
            await interaction.response.send_message(f"✅ **3endek** permission l `/{command}`", ephemeral=True)
        else:
            await interaction.response.send_message(
                f"❌ **Ma 3endkch** permission l `/{command}`\nKhass: {', '.join(f'`{r}`' for r in required)}",
                ephemeral=True,
            )

    def _is_admin(self, member: discord.Member) -> bool:
        if member.id == member.guild.owner_id:
            return True
        member_roles = [r.name for r in member.roles]
        return any(r in member_roles for r in botconfig.ADMIN_ROLES)


async def setup(bot):
    await bot.add_cog(RoleConfig(bot))