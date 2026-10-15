# cogs/channelmanager.py
# =====================================================================
# ─── CHANNEL MANAGER — Full Channel + Category Management
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
import asyncio


class ChannelManager(commands.Cog):
    """Full channel & category management + bulk tools"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════════════════════════
    # ─── HELPERS (used by Secret Panel)
    # ═══════════════════════════════════════════════════════════
    async def clone(self, channel):
        try:
            return await channel.clone(reason="ChannelManager clone")
        except Exception:
            return None

    async def sync_perms(self, channel, category: discord.CategoryChannel = None):
        try:
            await channel.edit(sync_permissions=True)
            return True
        except Exception:
            return False

    async def bulk_lock(self, guild, lock: bool) -> tuple[int, int]:
        ok, fail = 0, 0
        for ch in guild.text_channels:
            try:
                ow = ch.overwrites_for(guild.default_role)
                ow.send_messages = not lock
                await ch.set_permissions(guild.default_role, overwrite=ow)
                ok += 1
                await asyncio.sleep(0.4)
            except Exception:
                fail += 1
        return ok, fail

    async def bulk_slowmode(self, guild, seconds: int) -> tuple[int, int]:
        ok, fail = 0, 0
        for ch in guild.text_channels:
            try:
                await ch.edit(slowmode_delay=seconds)
                ok += 1
                await asyncio.sleep(0.3)
            except Exception:
                fail += 1
        return ok, fail

    # ═══════════════════════════════════════════════════════════
    # ─── SLASH: /channel (group)
    # ═══════════════════════════════════════════════════════════
    channel_group = app_commands.Group(name="channel", description="Channel management")

    # ─── CREATE
    @channel_group.command(name="create", description="Sayeb channel jdid")
    @app_commands.describe(
        name="Smiya dyal channel",
        type="Type dyal channel",
        category="Category (optionnel)",
        topic="Topic (text only)",
        nsfw="NSFW?",
        slowmode="Slowmode f seconds",
        user_limit="Voice limit (voice only)",
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="📝 Text", value="text"),
        app_commands.Choice(name="🔊 Voice", value="voice"),
        app_commands.Choice(name="🎤 Stage", value="stage"),
        app_commands.Choice(name="💬 Forum", value="forum"),
    ])
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channel_create(
        self,
        interaction: discord.Interaction,
        name: str,
        type: app_commands.Choice[str],
        category: discord.CategoryChannel = None,
        topic: str = None,
        nsfw: bool = False,
        slowmode: app_commands.Range[int, 0, 21600] = 0,
        user_limit: app_commands.Range[int, 0, 99] = 0,
    ):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        try:
            if type.value == "text":
                ch = await guild.create_text_channel(
                    name=name, category=category, topic=topic,
                    nsfw=nsfw, slowmode_delay=slowmode,
                    reason=f"Par {interaction.user}",
                )
            elif type.value == "voice":
                ch = await guild.create_voice_channel(
                    name=name, category=category, user_limit=user_limit,
                    reason=f"Par {interaction.user}",
                )
            elif type.value == "stage":
                ch = await guild.create_stage_channel(name=name, category=category)
            elif type.value == "forum":
                ch = await guild.create_forum(name=name, category=category)
            else:
                return await interaction.followup.send("❌ Type ghalat!", ephemeral=True)
        except discord.Forbidden:
            return await interaction.followup.send("❌ Ma 3ndich permission!", ephemeral=True)
        except Exception as e:
            return await interaction.followup.send(f"❌ `{e}`", ephemeral=True)

        await interaction.followup.send(f"✅ Channel tsayeb: {ch.mention}", ephemeral=True)

    # ─── DELETE
    @channel_group.command(name="delete", description="Msa7 channel")
    @app_commands.describe(channel="Channel li bghiti tmsa7")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channel_delete(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel):
        await interaction.response.defer(ephemeral=True)
        name = channel.name
        try:
            await channel.delete(reason=f"Par {interaction.user}")
        except discord.Forbidden:
            return await interaction.followup.send("❌ Ma 3ndich permission!", ephemeral=True)
        except Exception as e:
            return await interaction.followup.send(f"❌ `{e}`", ephemeral=True)
        await interaction.followup.send(f"✅ Channel `{name}` t-masa7!", ephemeral=True)

    # ─── RENAME
    @channel_group.command(name="rename", description="Beddel smiya dyal channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channel_rename(
        self,
        interaction: discord.Interaction,
        channel: discord.abc.GuildChannel,
        new_name: str,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            await channel.edit(name=new_name, reason=f"Par {interaction.user}")
        except discord.Forbidden:
            return await interaction.followup.send("❌ Ma 3ndich permission!", ephemeral=True)
        except Exception as e:
            return await interaction.followup.send(f"❌ `{e}`", ephemeral=True)
        await interaction.followup.send(f"✅ Smiya tbeddlat l: **{new_name}**", ephemeral=True)

    # ─── MOVE
    @channel_group.command(name="move", description="Nqel channel l category")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channel_move(
        self,
        interaction: discord.Interaction,
        channel: discord.abc.GuildChannel,
        category: discord.CategoryChannel = None,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            await channel.edit(category=category, reason=f"Par {interaction.user}")
        except discord.Forbidden:
            return await interaction.followup.send("❌ Ma 3ndich permission!", ephemeral=True)
        except Exception as e:
            return await interaction.followup.send(f"❌ `{e}`", ephemeral=True)
        where = category.mention if category else "**sans catégorie**"
        await interaction.followup.send(f"✅ {channel.mention} → {where}", ephemeral=True)

    # ─── CLONE
    @channel_group.command(name="clone", description="Copy channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channel_clone(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel):
        await interaction.response.defer(ephemeral=True)
        try:
            new = await channel.clone(reason=f"Par {interaction.user}")
        except discord.Forbidden:
            return await interaction.followup.send("❌ Ma 3ndich permission!", ephemeral=True)
        except Exception as e:
            return await interaction.followup.send(f"❌ `{e}`", ephemeral=True)
        await interaction.followup.send(f"✅ Clone tsayeb: {new.mention}", ephemeral=True)

    # ─── LOCK
    @channel_group.command(name="lock", description="Qfel channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channel_lock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel
        ow = channel.overwrites_for(interaction.guild.default_role)
        ow.send_messages = False
        try:
            await channel.set_permissions(interaction.guild.default_role, overwrite=ow)
        except discord.Forbidden:
            return await interaction.response.send_message("❌ Ma 3ndich permission!", ephemeral=True)
        await interaction.response.send_message(f"🔒 {channel.mention} t-qfel!", ephemeral=True)

    # ─── UNLOCK
    @channel_group.command(name="unlock", description="Ftah channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channel_unlock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel
        ow = channel.overwrites_for(interaction.guild.default_role)
        ow.send_messages = True
        try:
            await channel.set_permissions(interaction.guild.default_role, overwrite=ow)
        except discord.Forbidden:
            return await interaction.response.send_message("❌ Ma 3ndich permission!", ephemeral=True)
        await interaction.response.send_message(f"🔓 {channel.mention} t-fta7!", ephemeral=True)

    # ─── SLOWMODE
    @channel_group.command(name="slowmode", description="Beddel slowmode dyal channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channel_slowmode(
        self,
        interaction: discord.Interaction,
        seconds: app_commands.Range[int, 0, 21600],
        channel: discord.TextChannel = None,
    ):
        channel = channel or interaction.channel
        try:
            await channel.edit(slowmode_delay=seconds)
        except discord.Forbidden:
            return await interaction.response.send_message("❌ Ma 3ndich permission!", ephemeral=True)
        await interaction.response.send_message(f"🐌 Slowmode `{seconds}s` f {channel.mention}", ephemeral=True)

    # ─── BULK LOCK
    @channel_group.command(name="bulk-lock", description="Qfel GA3 text channels")
    @app_commands.checks.has_permissions(administrator=True)
    async def bulk_lock_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ok, fail = await self.bulk_lock(interaction.guild, True)
        await interaction.followup.send(f"🔒 Locked: `{ok}` | Failed: `{fail}`", ephemeral=True)

    # ─── BULK UNLOCK
    @channel_group.command(name="bulk-unlock", description="Ftah GA3 text channels")
    @app_commands.checks.has_permissions(administrator=True)
    async def bulk_unlock_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ok, fail = await self.bulk_lock(interaction.guild, False)
        await interaction.followup.send(f"🔓 Unlocked: `{ok}` | Failed: `{fail}`", ephemeral=True)

    # ─── BULK SLOWMODE
    @channel_group.command(name="bulk-slowmode", description="Slowmode l GA3 channels")
    @app_commands.checks.has_permissions(administrator=True)
    async def bulk_slowmode_cmd(
        self,
        interaction: discord.Interaction,
        seconds: app_commands.Range[int, 0, 21600],
    ):
        await interaction.response.defer(ephemeral=True)
        ok, fail = await self.bulk_slowmode(interaction.guild, seconds)
        await interaction.followup.send(f"🐌 Applied to `{ok}` | Failed: `{fail}`", ephemeral=True)

    # ═══════════════════════════════════════════════════════════
    # ─── SLASH: /category (group)
    # ═══════════════════════════════════════════════════════════
    category_group = app_commands.Group(name="category", description="Category management")

    @category_group.command(name="create", description="Sayeb category jdida")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def category_create(
        self,
        interaction: discord.Interaction,
        name: str,
        position: app_commands.Range[int, 0, 50] = 0,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            cat = await interaction.guild.create_category(
                name=name, position=position, reason=f"Par {interaction.user}",
            )
        except discord.Forbidden:
            return await interaction.followup.send("❌ Ma 3ndich permission!", ephemeral=True)
        except Exception as e:
            return await interaction.followup.send(f"❌ `{e}`", ephemeral=True)
        await interaction.followup.send(f"✅ Category tsayeb: **{cat.name}**", ephemeral=True)

    @category_group.command(name="delete", description="Msa7 category")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def category_delete(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        await interaction.response.defer(ephemeral=True)
        name = category.name
        try:
            await category.delete(reason=f"Par {interaction.user}")
        except discord.Forbidden:
            return await interaction.followup.send("❌ Ma 3ndich permission!", ephemeral=True)
        except Exception as e:
            return await interaction.followup.send(f"❌ `{e}`", ephemeral=True)
        await interaction.followup.send(f"✅ Category `{name}` t-masa7!", ephemeral=True)

    @category_group.command(name="rename", description="Beddel smiya dyal category")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def category_rename(
        self,
        interaction: discord.Interaction,
        category: discord.CategoryChannel,
        new_name: str,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            await category.edit(name=new_name, reason=f"Par {interaction.user}")
        except discord.Forbidden:
            return await interaction.followup.send("❌ Ma 3ndich permission!", ephemeral=True)
        await interaction.followup.send(f"✅ Category wella **{new_name}**", ephemeral=True)

    @category_group.command(name="list", description="List dyal categories")
    async def category_list(self, interaction: discord.Interaction):
        cats = interaction.guild.categories
        if not cats:
            return await interaction.response.send_message("❌ Ma kaynch categories!", ephemeral=True)
        lines = []
        for c in cats:
            lines.append(f"• **{c.name}** — `{len(c.channels)}` channels (pos: {c.position})")
        embed = discord.Embed(
            title=f"📂 Categories ({len(cats)})",
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ═══════════════════════════════════════════════════════════
    # ─── PREFIX: &cm
    # ═══════════════════════════════════════════════════════════
    @commands.group(name="cm", invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def cm_group(self, ctx: commands.Context):
        """`&cm` — Channel manager help"""
        embed = discord.Embed(title="🔧 Channel Manager", color=discord.Color.blurple())
        embed.add_field(name="📝 Channels", value=(
            "`&cm create <text|voice> <name> [category]`\n"
            "`&cm delete <channel>`\n"
            "`&cm rename <channel> <name>`\n"
            "`&cm move <channel> [category]`\n"
            "`&cm clone <channel>`"
        ), inline=False)
        embed.add_field(name="📂 Categories", value=(
            "`&cm cat create <name>`\n"
            "`&cm cat delete <name>`\n"
            "`&cm cat rename <old> <new>`\n"
            "`&cm cat list`"
        ), inline=False)
        embed.add_field(name="🔧 Tools", value=(
            "`&cm lock [channel]` / `&cm unlock [channel]`\n"
            "`&cm slowmode <sec> [channel]`\n"
            "`&cm bulklock` / `&cm bulkunlock`"
        ), inline=False)
        await ctx.send(embed=embed)

    @cm_group.command(name="create")
    @commands.has_permissions(manage_channels=True)
    async def cm_create(self, ctx: commands.Context, type_: str, name: str, *, category_name: str = None):
        """`&cm create text|voice <name> [category_name]`"""
        category = None
        if category_name:
            category = discord.utils.get(ctx.guild.categories, name=category_name)
        try:
            if type_.lower() == "text":
                ch = await ctx.guild.create_text_channel(name=name, category=category)
            elif type_.lower() == "voice":
                ch = await ctx.guild.create_voice_channel(name=name, category=category)
            else:
                return await ctx.send("❌ Type: `text` wla `voice`")
        except discord.Forbidden:
            return await ctx.send("❌ Ma 3ndich permission!")
        await ctx.send(f"✅ Tsayeb: {ch.mention}")

    @cm_group.command(name="delete")
    @commands.has_permissions(manage_channels=True)
    async def cm_delete(self, ctx: commands.Context, channel: discord.abc.GuildChannel):
        """`&cm delete <channel>`"""
        name = channel.name
        try:
            await channel.delete(reason=f"Par {ctx.author}")
        except discord.Forbidden:
            return await ctx.send("❌ Ma 3ndich permission!")
        await ctx.send(f"✅ `{name}` t-masa7!")

    @cm_group.command(name="rename")
    @commands.has_permissions(manage_channels=True)
    async def cm_rename(self, ctx: commands.Context, channel: discord.abc.GuildChannel, *, new_name: str):
        """`&cm rename <channel> <new_name>`"""
        try:
            await channel.edit(name=new_name)
        except discord.Forbidden:
            return await ctx.send("❌ Ma 3ndich permission!")
        await ctx.send(f"✅ Smiya: **{new_name}**")

    @cm_group.command(name="move")
    @commands.has_permissions(manage_channels=True)
    async def cm_move(self, ctx: commands.Context, channel: discord.abc.GuildChannel, *, category_name: str = None):
        """`&cm move <channel> [category_name]`"""
        category = None
        if category_name:
            category = discord.utils.get(ctx.guild.categories, name=category_name)
            if category is None:
                return await ctx.send(f"❌ Category `{category_name}` ma kaynch!")
        try:
            await channel.edit(category=category)
        except discord.Forbidden:
            return await ctx.send("❌ Ma 3ndich permission!")
        where = category.mention if category else "sans catégorie"
        await ctx.send(f"✅ {channel.mention} → {where}")

    @cm_group.command(name="clone")
    @commands.has_permissions(manage_channels=True)
    async def cm_clone(self, ctx: commands.Context, channel: discord.abc.GuildChannel):
        """`&cm clone <channel>`"""
        try:
            new = await channel.clone()
        except discord.Forbidden:
            return await ctx.send("❌ Ma 3ndich permission!")
        await ctx.send(f"✅ Clone: {new.mention}")

    @cm_group.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def cm_lock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """`&cm lock [channel]`"""
        channel = channel or ctx.channel
        ow = channel.overwrites_for(ctx.guild.default_role)
        ow.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=ow)
        await ctx.send(f"🔒 {channel.mention} t-qfel!")

    @cm_group.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def cm_unlock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """`&cm unlock [channel]`"""
        channel = channel or ctx.channel
        ow = channel.overwrites_for(ctx.guild.default_role)
        ow.send_messages = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=ow)
        await ctx.send(f"🔓 {channel.mention} t-fta7!")

    @cm_group.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def cm_slowmode(self, ctx: commands.Context, seconds: int, channel: discord.TextChannel = None):
        """`&cm slowmode <sec> [channel]`"""
        if seconds < 0 or seconds > 21600:
            return await ctx.send("❌ 0-21600!")
        channel = channel or ctx.channel
        await channel.edit(slowmode_delay=seconds)
        await ctx.send(f"🐌 Slowmode `{seconds}s` f {channel.mention}")

    @cm_group.command(name="bulklock")
    @commands.has_permissions(administrator=True)
    async def cm_bulklock(self, ctx: commands.Context):
        """`&cm bulklock`"""
        msg = await ctx.send("⏳ Kanqfel kolchi...")
        ok, fail = await self.bulk_lock(ctx.guild, True)
        await msg.edit(content=f"🔒 Locked: `{ok}` | Failed: `{fail}`")

    @cm_group.command(name="bulkunlock")
    @commands.has_permissions(administrator=True)
    async def cm_bulkunlock(self, ctx: commands.Context):
        """`&cm bulkunlock`"""
        msg = await ctx.send("⏳ Kanftah kolchi...")
        ok, fail = await self.bulk_lock(ctx.guild, False)
        await msg.edit(content=f"🔓 Unlocked: `{ok}` | Failed: `{fail}`")

    # ─── CATEGORY PREFIX
    @cm_group.group(name="cat", invoke_without_command=True)
    async def cm_cat(self, ctx: commands.Context):
        """`&cm cat` — Category commands"""
        await ctx.send("📂 `&cm cat create|delete|rename|list`")

    @cm_cat.command(name="create")
    @commands.has_permissions(manage_channels=True)
    async def cm_cat_create(self, ctx: commands.Context, *, name: str):
        """`&cm cat create <name>`"""
        try:
            cat = await ctx.guild.create_category(name=name)
        except discord.Forbidden:
            return await ctx.send("❌ Ma 3ndich permission!")
        await ctx.send(f"✅ Category: **{cat.name}**")

    @cm_cat.command(name="delete")
    @commands.has_permissions(manage_channels=True)
    async def cm_cat_delete(self, ctx: commands.Context, *, name: str):
        """`&cm cat delete <name>`"""
        cat = discord.utils.get(ctx.guild.categories, name=name)
        if not cat:
            return await ctx.send("❌ Category ma kaynch!")
        await cat.delete()
        await ctx.send(f"✅ Category `{name}` t-masa7!")

    @cm_cat.command(name="rename")
    @commands.has_permissions(manage_channels=True)
    async def cm_cat_rename(self, ctx: commands.Context, old_name: str, *, new_name: str):
        """`&cm cat rename <old> <new>`"""
        cat = discord.utils.get(ctx.guild.categories, name=old_name)
        if not cat:
            return await ctx.send("❌ Category ma kaynch!")
        await cat.edit(name=new_name)
        await ctx.send(f"✅ Category: **{new_name}**")

    @cm_cat.command(name="list")
    async def cm_cat_list(self, ctx: commands.Context):
        """`&cm cat list`"""
        cats = ctx.guild.categories
        if not cats:
            return await ctx.send("❌ Ma kaynch categories!")
        lines = [f"• **{c.name}** — `{len(c.channels)}` channels" for c in cats]
        await ctx.send("📂 **Categories:**\n" + "\n".join(lines))


async def setup(bot):
    await bot.add_cog(ChannelManager(bot))