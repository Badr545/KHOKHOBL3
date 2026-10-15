# cogs/embedbuilder.py
# =====================================================================
# ─── EMBED BUILDER — Interactive (buttons + modals)
# =====================================================================
import discord
from discord.ext import commands


class EmbedBuilderSession:
    def __init__(self, channel: discord.TextChannel, author: discord.Member):
        self.channel = channel
        self.author = author
        self.data = {
            "title": None,
            "description": None,
            "color": 0x5865F2,
            "image": None,
            "thumbnail": None,
            "footer": None,
            "author_name": None,
            "fields": [],  # list[tuple(name, value, inline)]
        }

    def build(self) -> discord.Embed:
        e = discord.Embed(color=discord.Color(self.data["color"]))
        if self.data["title"]:
            e.title = self.data["title"]
        if self.data["description"]:
            e.description = self.data["description"]
        if self.data["image"]:
            e.set_image(url=self.data["image"])
        if self.data["thumbnail"]:
            e.set_thumbnail(url=self.data["thumbnail"])
        if self.data["footer"]:
            e.set_footer(text=self.data["footer"])
        if self.data["author_name"]:
            e.set_author(name=self.data["author_name"])
        for name, value, inline in self.data["fields"][:25]:
            e.add_field(name=name, value=value, inline=inline)
        return e


class FieldModal(discord.ui.Modal, title="➕ Zid field"):
    name = discord.ui.TextInput(label="Name", max_length=256)
    value = discord.ui.TextInput(label="Value", style=discord.TextStyle.paragraph, max_length=1024)
    inline = discord.ui.TextInput(label="Inline? (yes/no)", default="no", max_length=3)

    def __init__(self, session: EmbedBuilderSession):
        super().__init__()
        self.session = session

    async def on_submit(self, it: discord.Interaction):
        inline = self.inline.value.lower().startswith("y")
        self.session.data["fields"].append((self.name.value, self.value.value, inline))
        await it.response.send_message("✅ Field tzad!", ephemeral=True)


class BasicModal(discord.ui.Modal, title="✏️ Edit basic"):
    title_ = discord.ui.TextInput(label="Title", required=False, max_length=256)
    description = discord.ui.TextInput(label="Description", required=False, style=discord.TextStyle.paragraph)
    color = discord.ui.TextInput(label="Color (hex)", required=False, default="#5865F2", max_length=7)
    footer = discord.ui.TextInput(label="Footer", required=False, max_length=2048)
    author_name = discord.ui.TextInput(label="Author", required=False, max_length=256)

    def __init__(self, session: EmbedBuilderSession):
        super().__init__()
        self.session = session

    async def on_submit(self, it: discord.Interaction):
        if self.title_.value:
            self.session.data["title"] = self.title_.value
        if self.description.value:
            self.session.data["description"] = self.description.value
        if self.footer.value:
            self.session.data["footer"] = self.footer.value
        if self.author_name.value:
            self.session.data["author_name"] = self.author_name.value
        if self.color.value:
            try:
                self.session.data["color"] = int(self.color.value.replace("#", ""), 16)
            except Exception:
                pass
        await it.response.send_message("✅ Updated!", ephemeral=True)


class MediaModal(discord.ui.Modal, title="🖼️ Image / Thumbnail"):
    image = discord.ui.TextInput(label="Image URL", required=False)
    thumbnail = discord.ui.TextInput(label="Thumbnail URL", required=False)

    def __init__(self, session: EmbedBuilderSession):
        super().__init__()
        self.session = session

    async def on_submit(self, it: discord.Interaction):
        if self.image.value:
            self.session.data["image"] = self.image.value
        if self.thumbnail.value:
            self.session.data["thumbnail"] = self.thumbnail.value
        await it.response.send_message("✅ Updated!", ephemeral=True)


class BuilderView(discord.ui.View):
    def __init__(self, session: EmbedBuilderSession):
        super().__init__(timeout=600)
        self.session = session

    async def interaction_check(self, it: discord.Interaction) -> bool:
        return it.user.id == self.session.author.id

    @discord.ui.button(label="Basic", emoji="✏️", style=discord.ButtonStyle.primary)
    async def basic_btn(self, it: discord.Interaction, b: discord.ui.Button):
        await it.response.send_modal(BasicModal(self.session))

    @discord.ui.button(label="Media", emoji="🖼️", style=discord.ButtonStyle.primary)
    async def media_btn(self, it: discord.Interaction, b: discord.ui.Button):
        await it.response.send_modal(MediaModal(self.session))

    @discord.ui.button(label="Add Field", emoji="➕", style=discord.ButtonStyle.success)
    async def field_btn(self, it: discord.Interaction, b: discord.ui.Button):
        if len(self.session.data["fields"]) >= 25:
            return await it.response.send_message("❌ 25 fields max!", ephemeral=True)
        await it.response.send_modal(FieldModal(self.session))

    @discord.ui.button(label="Clear Fields", emoji="🗑️", style=discord.ButtonStyle.secondary)
    async def clear_btn(self, it: discord.Interaction, b: discord.ui.Button):
        self.session.data["fields"].clear()
        await it.response.send_message("🗑️ Cleared!", ephemeral=True)

    @discord.ui.button(label="Preview", emoji="👁️", style=discord.ButtonStyle.secondary)
    async def preview_btn(self, it: discord.Interaction, b: discord.ui.Button):
        await it.response.send_message(embed=self.session.build(), ephemeral=True)

    @discord.ui.button(label="Send", emoji="📤", style=discord.ButtonStyle.success, row=1)
    async def send_btn(self, it: discord.Interaction, b: discord.ui.Button):
        try:
            await self.session.channel.send(embed=self.session.build())
            await it.response.send_message(f"✅ Sift f {self.session.channel.mention}", ephemeral=True)
        except Exception as e:
            await it.response.send_message(f"❌ `{e}`", ephemeral=True)

    @discord.ui.button(label="Close", emoji="✖️", style=discord.ButtonStyle.danger, row=1)
    async def close_btn(self, it: discord.Interaction, b: discord.ui.Button):
        try:
            await it.message.delete()
        except Exception:
            pass


class EmbedBuilder(commands.Cog):
    """Interactive embed builder"""

    def __init__(self, bot):
        self.bot = bot

    async def open_builder(self, channel: discord.TextChannel, author: discord.Member) -> bool:
        session = EmbedBuilderSession(channel, author)
        embed = discord.Embed(
            title="🎨 Embed Builder",
            description=f"Channel target: {channel.mention}\nKhtar buttons bash tzid content.",
            color=discord.Color.blurple(),
        )
        try:
            await author.send(embed=embed, view=BuilderView(session))
            return True
        except Exception:
            return False


async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))