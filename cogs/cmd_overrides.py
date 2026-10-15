# cogs/cmd_overrides.py
# =====================================================================
# ─── COMMAND OVERRIDES — Beddel smiyat dyal commands (aliases)
# =====================================================================
import discord
from discord.ext import commands
import json
import os

# Fix: Absolute path bash l-file ykoun dima f nafs l-blassa
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "cmd_overrides.json")


def _load():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {int(g): v for g, v in raw.items()}
    except Exception as e:
        print(f"❌ Error loading cmd_overrides.json: {e}")
        return {}


def _save(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# {guild_id: {original_name: {"aliases": [list]}}}
OVERRIDES = _load()


class CmdOverrides(commands.Cog):
    """Manage command aliases (renames) via panel"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.apply_all()

    def apply_all(self):
        """Apply kol aliases mn JSON l commands."""
        count = 0
        for guild_id, overrides in OVERRIDES.items():
            for orig_name, data in overrides.items():
                cmd = self.bot.get_command(orig_name)
                if not cmd:
                    print(f"⚠️ Command `{orig_name}` ma kaynch (guild {guild_id})")
                    continue
                for alias in data.get("aliases", []):
                    if alias not in cmd.aliases:
                        try:
                            cmd.aliases.append(alias)
                            count += 1
                        except Exception as e:
                            print(f"❌ Error appending alias {alias} to {orig_name}: {e}")
        print(f"✅ Command overrides applied: {count} aliases")

    def add_alias(self, guild_id: int, original: str, alias: str) -> str:
        """
        Zid alias l command.
        Rje3: 'ok' | 'no_cmd' | 'dup' | 'conflict' | 'bad'
        """
        original = original.lower().strip().lstrip("&+")
        alias = alias.lower().strip().lstrip("&+")

        if not original or not alias or " " in alias:
            return "bad"

        cmd = self.bot.get_command(original)
        if not cmd:
            return "no_cmd"

        if alias in cmd.aliases or alias == cmd.name:
            return "dup"

        # Fix: Check wach l-alias deja command akhor
        existing_cmd = self.bot.get_command(alias)
        if existing_cmd and existing_cmd != cmd:
            return "conflict"

        # Fix: Check wach l-alias deja alias dyal command akhor
        for c in self.bot.commands:
            if alias in c.aliases and c != cmd:
                return "conflict"

        # Save
        OVERRIDES.setdefault(guild_id, {}).setdefault(original, {"aliases": []})
        if alias not in OVERRIDES[guild_id][original]["aliases"]:
            OVERRIDES[guild_id][original]["aliases"].append(alias)
        _save(OVERRIDES)

        # Apply l command
        try:
            cmd.aliases.append(alias)
        except Exception:
            return "bad"
        return "ok"

    def remove_alias(self, guild_id: int, original: str, alias: str) -> bool:
        original = original.lower().strip().lstrip("&+")
        alias = alias.lower().strip().lstrip("&+")

        if guild_id not in OVERRIDES or original not in OVERRIDES[guild_id]:
            return False
        if alias not in OVERRIDES[guild_id][original].get("aliases", []):
            return False

        OVERRIDES[guild_id][original]["aliases"].remove(alias)
        if not OVERRIDES[guild_id][original]["aliases"]:
            OVERRIDES[guild_id].pop(original)
        if not OVERRIDES[guild_id]:
            OVERRIDES.pop(guild_id)
        _save(OVERRIDES)

        cmd = self.bot.get_command(original)
        if cmd and alias in cmd.aliases:
            try:
                cmd.aliases.remove(alias)
            except Exception:
                pass
        return True

    def clear_guild(self, guild_id: int) -> int:
        """Hyed kolchi dyal had guild."""
        if guild_id not in OVERRIDES:
            return 0
        count = 0
        for orig_name, data in OVERRIDES[guild_id].items():
            cmd = self.bot.get_command(orig_name)
            if cmd:
                for alias in data.get("aliases", []):
                    if alias in cmd.aliases:
                        try:
                            cmd.aliases.remove(alias)
                            count += 1
                        except Exception:
                            pass
        OVERRIDES.pop(guild_id, None)
        _save(OVERRIDES)
        return count

    def list_guild(self, guild_id: int) -> dict:
        return OVERRIDES.get(guild_id, {})


# ═══════════════════════════════════════════════════════════════════
# ─── PANEL VIEW
# ═══════════════════════════════════════════════════════════════════
class CommandManagerPanel(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id

    @discord.ui.button(label="Rename / Alias", emoji="✏️", style=discord.ButtonStyle.primary)
    async def rename_btn(self, it, b):
        await it.response.send_modal(RenameCmdModal(self.guild_id))

    @discord.ui.button(label="Remove Alias", emoji="❌", style=discord.ButtonStyle.danger)
    async def remove_btn(self, it, b):
        await it.response.send_modal(RemoveAliasModal(self.guild_id))

    @discord.ui.button(label="List Aliases", emoji="📋", style=discord.ButtonStyle.secondary)
    async def list_btn(self, it, b):
        cog = it.client.get_cog("CmdOverrides")
        if not cog:
            return await it.response.send_message("❌ Cog machi loaded!", ephemeral=True)
        data = cog.list_guild(self.guild_id)
        if not data:
            return await it.response.send_message(
                "📋 Ma kaynch aliases f had server.", ephemeral=True,
            )
        lines = []
        for orig, d in data.items():
            aliases = ", ".join(f"`{a}`" for a in d.get("aliases", []))
            lines.append(f"• **`{orig}`** → {aliases or '*—*'}")
        embed = discord.Embed(
            title=f"✏️ Command Aliases ({len(data)})",
            description="\n".join(lines[:30]),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Kol alias kaykhdem 3la commands")
        await it.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Clear All", emoji="🗑️", style=discord.ButtonStyle.danger)
    async def clear_btn(self, it, b):
        cog = it.client.get_cog("CmdOverrides")
        if not cog:
            return await it.response.send_message("❌ Cog machi loaded!", ephemeral=True)
        n = cog.clear_guild(self.guild_id)
        await it.response.send_message(f"🗑️ Tsaybo `{n}` aliases!", ephemeral=True)

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary)
    async def refresh_btn(self, it, b):
        cog = it.client.get_cog("CmdOverrides")
        if cog:
            cog.apply_all()
        await it.response.send_message("✅ Refreshed!", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════
# ─── MODALS
# ═══════════════════════════════════════════════════════════════════
class RenameCmdModal(discord.ui.Modal, title="✏️ Rename / Alias Command"):
    original = discord.ui.TextInput(
        label="Original command name",
        placeholder="kick / ban / warn / shop / help ...",
        max_length=50,
    )
    new_name = discord.ui.TextInput(
        label="New name (alias)",
        placeholder="kherrej / b7 / 3ta-warning / magasin ...",
        max_length=50,
    )

    def __init__(self, guild_id):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, it: discord.Interaction):
        cog = it.client.get_cog("CmdOverrides")
        if not cog:
            return await it.response.send_message("❌ Cog machi loaded!", ephemeral=True)

        result = cog.add_alias(self.guild_id, self.original.value, self.new_name.value)
        orig = self.original.value.strip().lstrip("&+")
        new = self.new_name.value.strip().lstrip("&+")

        if result == "ok":
            await it.response.send_message(
                f"✅ **`{orig}`** daba 3endou alias **`{new}`**!\n"
                f"💡 Jerreb: `+{new}` (wla `&{new}`)",
                ephemeral=True,
            )
        elif result == "no_cmd":
            await it.response.send_message(
                f"❌ Command `{orig}` ma kaynch!",
                ephemeral=True,
            )
        elif result == "dup":
            await it.response.send_message(
                f"⚠️ `{new}` deja alias dyal `{orig}`!",
                ephemeral=True,
            )
        elif result == "conflict":
            await it.response.send_message(
                f"❌ `{new}` deja command wla alias dyal command akhor!",
                ephemeral=True,
            )
        else:
            await it.response.send_message(
                "❌ Input ghalat! (bla espaces f new name)",
                ephemeral=True,
            )


class RemoveAliasModal(discord.ui.Modal, title="❌ Remove Alias"):
    original = discord.ui.TextInput(
        label="Original command name",
        max_length=50,
    )
    alias = discord.ui.TextInput(
        label="Alias li bghiti thyed",
        max_length=50,
    )

    def __init__(self, guild_id):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, it: discord.Interaction):
        cog = it.client.get_cog("CmdOverrides")
        if not cog:
            return await it.response.send_message("❌ Cog machi loaded!", ephemeral=True)

        ok = cog.remove_alias(self.guild_id, self.original.value, self.alias.value)
        if ok:
            await it.response.send_message(
                f"✅ Alias `{self.alias.value.strip()}` thyed!",
                ephemeral=True,
            )
        else:
            await it.response.send_message("⚠️ Ma l9itch had alias!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(CmdOverrides(bot))