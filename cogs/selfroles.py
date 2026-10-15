# cogs/selfroles.py
# =====================================================================
# ─── SELF ROLES — Dropdown-based (multi-categories) PERSISTENT
# =====================================================================
import discord
from discord.ext import commands
import json
import os

DATA_FILE = "data/selfroles.json"


def _load():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {int(g): {int(m): v for m, v in d.items()} for g, d in raw.items()}
    except Exception:
        return {}


def _save(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


SELFROLES = _load()


# ═══════════════════════════════════════════════════════════════════
# ─── DROPDOWN (kola category = dropdown) — PERSISTENT
# ═══════════════════════════════════════════════════════════════════
class RoleSelect(discord.ui.Select):
    def __init__(self, category_name: str, options: list, message_id: int, index: int):
        """
        options = [{"role_id": int, "label": str, "emoji": str, "description": str}]
        message_id + index = bash custom_id ykoun UNIQUE
        """
        opts = []
        for o in options[:25]:
            opts.append(discord.SelectOption(
                label=o["label"][:100],
                value=str(o["role_id"]),
                emoji=o.get("emoji") or None,
                description=(o.get("description") or "")[:100] or None,
            ))

        super().__init__(
            custom_id=f"selfrole:{message_id}:{index}",
            placeholder=f"Select {category_name}",
            min_values=0,
            max_values=len(opts),
            options=opts,
        )
        self.category_name = category_name

    async def callback(self, it: discord.Interaction):
        guild = it.guild
        added = []
        removed = []
        failed = []

        for value in self.values:
            try:
                role_id = int(value)
            except ValueError:
                continue
            role = guild.get_role(role_id)
            if role is None:
                failed.append(value)
                continue

            try:
                if role in it.user.roles:
                    await it.user.remove_roles(role, reason=f"SelfRole: {self.category_name}")
                    removed.append(role.mention)
                else:
                    await it.user.add_roles(role, reason=f"SelfRole: {self.category_name}")
                    added.append(role.mention)
            except discord.Forbidden:
                failed.append(role.name)
            except Exception:
                failed.append(role.name)

        lines = []
        if added:
            lines.append(f"✅ **Added:** {', '.join(added)}")
        if removed:
            lines.append(f"❌ **Removed:** {', '.join(removed)}")
        if failed:
            lines.append(f"⚠️ **Failed:** {', '.join(str(f) for f in failed)}")
        if not lines:
            lines.append("🤷 Ma 3mlti walo.")

        await it.response.send_message("\n".join(lines), ephemeral=True)


class SelfRolesView(discord.ui.View):
    def __init__(self, categories: list, message_id: int):
        """
        categories = [{"name": str, "options": [...]}]
        message_id = ID dyal message (bach custom_id ykoun UNIQUE)
        """
        super().__init__(timeout=None)
        for i, cat in enumerate(categories[:5]):  # Discord max 5 selects
            self.add_item(RoleSelect(cat["name"], cat["options"], message_id, i))


# ═══════════════════════════════════════════════════════════════════
# ─── COG
# ═══════════════════════════════════════════════════════════════════
class SelfRoles(commands.Cog):
    """Self Roles b Dropdowns (multi-categories)"""

    def __init__(self, bot):
        self.bot = bot

    async def create_panel(
        self,
        channel: discord.TextChannel,
        title: str,
        description: str,
        banner_url: str,
        categories: list,
        author: discord.Member,
    ) -> bool:
        """
        categories = [
            {"name": "Games roles", "options": [
                {"role_id": 123, "label": "Valorant", "emoji": "🎮", "description": "..."},
                {"role_id": 456, "label": "Minecraft", "emoji": "⛏️"}
            ]},
        ]
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.from_rgb(30, 30, 35),
        )
        if banner_url:
            embed.set_image(url=banner_url)
        embed.set_footer(text=f"Par {author.name}")

        # ─── 1. Sift message bla view (bach n3erfo message_id)
        try:
            msg = await channel.send(embed=embed)
        except Exception as e:
            print(f"❌ create_panel send error: {e}")
            return False

        # ─── 2. Save f JSON
        SELFROLES.setdefault(channel.guild.id, {})[msg.id] = {
            "channel_id": channel.id,
            "title": title,
            "description": description,
            "banner_url": banner_url,
            "categories": categories,
        }
        _save(SELFROLES)

        # ─── 3. Daba 3endna message_id → nsaybo view b custom_id
        view = SelfRolesView(categories, msg.id)
        try:
            await msg.edit(view=view)
        except Exception as e:
            print(f"❌ create_panel edit error: {e}")
            return False

        return True

    async def restore_views(self):
        """Restore kol panels mn JSON (mli bot yrestart)."""
        count = 0
        for gid, msgs in SELFROLES.items():
            for mid, data in msgs.items():
                try:
                    view = SelfRolesView(data["categories"], mid)
                    self.bot.add_view(view)
                    count += 1
                except Exception as e:
                    print(f"⚠️ Restore view {mid} failed: {e}")
        return count

    @commands.Cog.listener()
    async def on_ready(self):
        n = await self.restore_views()
        total = sum(len(m) for m in SELFROLES.values())
        print(f"✅ SelfRoles restored: {n}/{total} panels")


async def setup(bot):
    await bot.add_cog(SelfRoles(bot))