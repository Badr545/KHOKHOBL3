# app.py
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.presences = True

# ═══════════════════════════════════════════════════════════════════
# ─── PREFIXES — & (public) + (admin)
# ═══════════════════════════════════════════════════════════════════
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("&", "+"),
    intents=intents,
    help_command=None,
)


# ═══════════════════════════════════════════════════════════════════
# ─── ADMIN COMMANDS (khass +)
# ═══════════════════════════════════════════════════════════════════
ADMIN_PREFIX_COMMANDS = {
    # ─── Moderation
    "kick", "ban", "warn", "warnings", "clearwarns",
    "slowmode", "lock", "unlock", "ms7",
    "giverole", "removerole", "massrole",
    # ─── Announcements
    "announce", "embed",
    # ─── Channel manager
    "cm", "channel", "category",
    # ─── Voice admin
    "join", "leave", "voice247",
    # ─── Admin only
    "reload", "shutdown", "eval", "config",
    "addmod", "removemod", "listroles", "checkperm",
    # ─── Game Requests (admin)
    "setgame", "delgame", "listgames",
}


# ═══════════════════════════════════════════════════════════════════
# ─── DUAL COMMANDS — kaykhedmo b & W + (help, cmds)
# ═══════════════════════════════════════════════════════════════════
DUAL_PREFIX_COMMANDS = {
    "help",
    "cmds",
}


COGS = [
    "cogs.basic", "cogs.admin", "cogs.announcements", "cogs.roles",
    "cogs.economy", "cogs.gambling", "cogs.games", "cogs.bir",
    "cogs.levels", "cogs.rankcard", "cogs.leaderboard", "cogs.shop",
    "cogs.info", "cogs.utility", "cogs.help", "cogs.logs",
    "cogs.welcome", "cogs.stats", "cogs.tempvoice", "cogs.voice",
    "cogs.roleconfig",
    "cogs.automod",
    "cogs.tickets",
    "cogs.tempban",
    "cogs.giveaway",
    "cogs.embedbuilder",
    "cogs.reactionroles",
    "cogs.channelmanager",
    "cogs.backup_restore",
    "cogs.customcommands",
    "cogs.cmd_overrides",
    "cogs.insights",
    "cogs.secret_admin",
    "cogs.selfroles",
    # ─── Jdad
    "cogs.banking",
    "cogs.antiraid",
    "cogs.achievements",
    "cogs.moregames",
    "cogs.premium",
    "cogs.transcripts",
    "cogs.social",
    "cogs.scheduled",
    "cogs.notifications",
    "cogs.temproles",
    "cogs.profile",
    "cogs.vote",
]


# ═══════════════════════════════════════════════════════════════════
# ─── GLOBAL PREFIX CHECK
# ═══════════════════════════════════════════════════════════════════
@bot.check
async def global_prefix_check(ctx: commands.Context) -> bool:
    if ctx.command is None:
        return True
    if ctx.guild is None:
        return True

    root = ctx.command.root_parent if ctx.command.root_parent else ctx.command
    cmd_name = root.name.lower()

    if cmd_name in DUAL_PREFIX_COMMANDS:
        return True

    is_admin = cmd_name in ADMIN_PREFIX_COMMANDS

    if is_admin and ctx.prefix != "+":
        raise commands.CheckFailure(f"__WRONG_PREFIX_ADMIN__{cmd_name}")

    if (not is_admin) and ctx.prefix == "+":
        raise commands.CheckFailure(f"__WRONG_PREFIX_PUBLIC__{cmd_name}")

    return True


# ═══════════════════════════════════════════════════════════════════
# ─── WEB DASHBOARD (background thread)
# ═══════════════════════════════════════════════════════════════════
def start_web_dashboard():
    """Bda web dashboard f background thread."""
    try:
        from web.app import app as flask_app
    except Exception as e:
        print(f"⚠️  Web dashboard ma tsayebch: {e}")
        print("   → T2ekked belli web/ folder kayn b files kamlin")
        return

    port = int(os.getenv("WEB_PORT", 8080))
    host = "0.0.0.0"

    def run():
        try:
            print(f"🌐 Web dashboard: http://localhost:{port}")
            flask_app.run(
                host=host,
                port=port,
                debug=False,
                use_reloader=False,
                threaded=True,
            )
        except Exception as e:
            print(f"❌ Web dashboard error: {e}")

    thread = threading.Thread(target=run, name="web-dashboard", daemon=True)
    thread.start()
    print(f"✅ Web dashboard started f thread (port {port})")


# ═══════════════════════════════════════════════════════════════════
# ─── SETUP HOOK
# ═══════════════════════════════════════════════════════════════════
@bot.event
async def setup_hook():
    print("🔧 Setup hook — kanloadi cogs...")
    loaded = set()
    for cog in COGS:
        if cog in loaded:
            print(f"⏭️ Skip duplicate: {cog}")
            continue
        try:
            await bot.load_extension(cog)
            loaded.add(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed {cog}: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")

    # ─── Start web dashboard
    if os.getenv("ENABLE_WEB", "1") == "1":
        start_web_dashboard()


@bot.event
async def on_ready():
    print(f"🔥 Ready: {bot.user} ({bot.user.id})")
    print(f"📋 Prefix commands: {len(bot.commands)}")
    print(f"   • `&` = public")
    print(f"   • `+` = admin/mod")
    print(f"   • `help`/`cmds` = juj prefixes")
    print(f"🌐 Web dashboard: http://localhost:{os.getenv('WEB_PORT', 8080)}")


# ═══════════════════════════════════════════════════════════════════
# ─── PREFIX ERRORS
# ═══════════════════════════════════════════════════════════════════
@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.CheckFailure):
        err_str = str(error)

        if err_str.startswith("__WRONG_PREFIX_ADMIN__"):
            cmd_name = err_str.replace("__WRONG_PREFIX_ADMIN__", "")
            try:
                await ctx.message.add_reaction("❌")
            except Exception:
                pass
            try:
                await ctx.send(
                    f"❌ {ctx.author.mention} — Had command khass ykoun b **`+`**!\n"
                    f"💡 **Exemple:** `+{cmd_name} ...`\n"
                    f"🔒 Had command ghir l-**Staff**.",
                    delete_after=10,
                )
                await ctx.message.delete(delay=10)
            except Exception:
                pass
            logs_cog = bot.get_cog("Logs")
            if logs_cog and ctx.guild:
                try:
                    await logs_cog.log_permission_denied(ctx.guild, ctx.author, f"&{cmd_name} (wrong prefix)")
                except Exception:
                    pass
            return

        if err_str.startswith("__WRONG_PREFIX_PUBLIC__"):
            cmd_name = err_str.replace("__WRONG_PREFIX_PUBLIC__", "")
            try:
                await ctx.message.add_reaction("❌")
            except Exception:
                pass
            try:
                await ctx.send(
                    f"❌ {ctx.author.mention} — Had command khass ykoun b **`&`**!\n"
                    f"💡 **Exemple:** `&{cmd_name} ...`",
                    delete_after=8,
                )
                await ctx.message.delete(delay=8)
            except Exception:
                pass
            return

        cmd_name = ctx.command.name if ctx.command else "?"
        try:
            await ctx.message.add_reaction("🚫")
        except Exception:
            pass
        try:
            await ctx.send(
                f"🚫 {ctx.author.mention} — Had command machi lik!\n"
                f"🔒 **Khass roles a3la** • 📖 Chouf `&help`",
                delete_after=8,
            )
            await ctx.message.delete(delay=8)
        except Exception:
            pass
        logs_cog = bot.get_cog("Logs")
        if logs_cog and ctx.guild:
            try:
                await logs_cog.log_permission_denied(ctx.guild, ctx.author, f"&{cmd_name}")
            except Exception:
                pass
        return

    if isinstance(error, commands.MissingRequiredArgument):
        try:
            await ctx.send(
                f"⚠️ {ctx.author.mention} — Khass: `{error.param.name}`",
                delete_after=8,
            )
            await ctx.message.delete(delay=8)
        except Exception:
            pass
        return

    if isinstance(error, commands.CommandOnCooldown):
        try:
            await ctx.send(
                f"⏰ {ctx.author.mention} — 3awed mn ba3d `{error.retry_after:.1f}s`!",
                delete_after=5,
            )
        except Exception:
            pass
        return

    if isinstance(error, commands.BotMissingPermissions):
        try:
            await ctx.send(
                f"🤖 Ma 3ndich permission: `{', '.join(error.missing_permissions)}`",
                delete_after=8,
            )
        except Exception:
            pass
        return

    print(f"❌ Command error [{ctx.command}]: {error}")


# ═══════════════════════════════════════════════════════════════════
# ─── SLASH ERRORS
# ═══════════════════════════════════════════════════════════════════
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        cmd_name = interaction.command.name if interaction.command else "?"
        msg = "🚫 Had command machi lik!\n🔒 **Khass roles a3la** • 📖 Chouf `/help`"
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception:
            pass
        logs_cog = bot.get_cog("Logs")
        if logs_cog and interaction.guild:
            try:
                await logs_cog.log_permission_denied(
                    interaction.guild, interaction.user, f"/{cmd_name}",
                )
            except Exception:
                pass
        return

    if isinstance(error, app_commands.CommandOnCooldown):
        try:
            await interaction.response.send_message(
                f"⏰ 3awed mn ba3d `{error.retry_after:.1f}s`!",
                ephemeral=True,
            )
        except Exception:
            pass
        return

    if isinstance(error, app_commands.BotMissingPermissions):
        try:
            await interaction.response.send_message(
                f"🤖 Ma 3ndich permission: `{', '.join(error.missing_permissions)}`",
                ephemeral=True,
            )
        except Exception:
            pass
        return

    print(f"❌ Slash error [{interaction.command}]: {error}")


# ═══════════════════════════════════════════════════════════════════
# ─── MAIN
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))