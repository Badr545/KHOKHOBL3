# cogs/reactionroles.py
# =====================================================================
# ─── REACTION ROLES — Button-based panels
# =====================================================================
import discord
from discord.ext import commands
import json
import os

DATA_FILE = "data/reactionroles.json"


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


RR = _load()


class RRButton(discord.ui.Button):
    def __init__(self, guild_id: int, message_id: int, role_id: int, label: str, emoji: str = None):
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.secondary,
            custom_id=f"rr:{guild_id}:{message_id}:{role_id}",
        )
        self.role_id = role_id
        self.guild_id = guild_id
        self.message_id = message_id

    async def callback(self, it: discord.Interaction):
        role = it.guild.get_role(self.role_id)
        if role is None:
            return await it.response.send_message("❌ Role ma kaynch!", ephemeral=True)
        if role in it.user.roles:
            try:
                await it.user.remove_roles(role, reason="Reaction role toggle")
                return await it.response.send_message(f"❌ Thyed lik {role.mention}", ephemeral=True)
            except Exception as e:
                return await it.response.send_message(f"❌ `{e}`", ephemeral=True)
        else:
            try:
                await it.user.add_roles(role, reason="Reaction role toggle")
                return await it.response.send_message(f"✅ 3tit lik {role.mention}", ephemeral=True)
            except Exception as e:
                return await it.response.send_message(f"❌ `{e}`", ephemeral=True)


class RRView(discord.ui.View):
    def __init__(self, guild_id: int, message_id: int, mappings: list):
        super().__init__(timeout=None)
        for m in mappings[:25]:
            self.add_item(RRButton(guild_id, message_id, m["role_id"], m["label"], m.get("emoji")))


class ReactionRoles(commands.Cog):
    """Reaction roles b buttons"""

    def __init__(self, bot):
        self.bot = bot

    async def create_panel(self, channel: discord.TextChannel, title: str, description: str,
                           mappings: list, author: discord.Member) -> bool:
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Par {author.name}")
        try:
            msg = await channel.send(embed=embed)
        except Exception:
            return False

        RR.setdefault(channel.guild.id, {})[msg.id] = {
            "channel_id": channel.id,
            "mappings": mappings,
            "title": title,
            "description": description,
        }
        _save(RR)

        view = RRView(channel.guild.id, msg.id, mappings)
        try:
            await msg.edit(view=view)
        except Exception:
            return False
        return True

    async def restore_views(self):
        for gid, msgs in RR.items():
            for mid, data in msgs.items():
                guild = self.bot.get_guild(gid)
                if not guild:
                    continue
                view = RRView(gid, mid, data["mappings"])
                self.bot.add_view(view)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.restore_views()


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))