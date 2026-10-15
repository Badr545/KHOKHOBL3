# =====================================================================
# ─── RANK CARD — صورة PNG (بحال الصورة)
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
from cogs.levels import LEVELS, xp_for_level
from cogs.economy import ECONOMY
from cogs.bir import BIR
from PIL import Image, ImageDraw, ImageFont
import io
import os
import aiohttp


CARD_WIDTH = 900
CARD_HEIGHT = 250

BG_COLOR = (30, 30, 45)
TEXT_COLOR = (255, 255, 255)
SUBTLE_COLOR = (170, 170, 190)
BAR_BG = (60, 60, 80)
BAR_FILL = (88, 101, 242)
BAR_FILL_2 = (180, 100, 255)


class RankCard(commands.Cog):
    """Rank Card — صورة PNG"""

    def __init__(self, bot):
        self.bot = bot
        self._font_cache = {}

    def _get_font(self, size: int):
        if size in self._font_cache:
            return self._font_cache[size]

        font_paths = [
            "assets/font.ttf",  # ← ✅ Hada l-ahsan — dir font f assets/
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        for path in font_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, size)
                    self._font_cache[size] = font
                    return font
                except Exception:
                    continue

        # ⚠️ WARNING: Font default sghir bezzaf — text ghadi ykoun mchi m9roui
        print("⚠️ WARNING: Ma l9itch font! Zid assets/font.ttf f project.")
        font = ImageFont.load_default()
        self._font_cache[size] = font
        return font

    def _circle_avatar(self, avatar_bytes: bytes, size: int) -> Image.Image:
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((size, size), Image.LANCZOS)

        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)

        result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        result.paste(avatar, (0, 0), mask=mask)
        return result

    async def _fetch_avatar(self, url: str) -> bytes:
        async with aiohttp.ClientSession() as s:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with s.get(url, headers=headers) as r:
                return await r.read()

    async def build_rank_card(self, member: discord.Member, guild) -> io.BytesIO:
        level_data = LEVELS.get(guild.id, {}).get(member.id, {
            "xp": 0, "level": 0, "messages": 0,
        })
        bir_data = BIR.get(guild.id, {}).get(member.id, {"bir": 0})

        guild_levels = LEVELS.get(guild.id, {})
        sorted_users = sorted(
            guild_levels.items(),
            key=lambda x: (x[1].get("level", 0), x[1].get("xp", 0)),
            reverse=True,
        )
        rank_position = next(
            (i + 1 for i, (uid, _) in enumerate(sorted_users) if uid == member.id),
            len(sorted_users) + 1 if sorted_users else 1,
        )

        current_xp = level_data["xp"]
        current_level = level_data["level"]
        needed = xp_for_level(current_level + 1)
        progress = min(current_xp / needed, 1.0) if needed else 0

        # Background
        if os.path.exists("assets/background.png"):
            bg = Image.open("assets/background.png").convert("RGB")
            bg = bg.resize((CARD_WIDTH, CARD_HEIGHT), Image.LANCZOS)
            img = bg
        else:
            img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), BG_COLOR)
            draw = ImageDraw.Draw(img)
            for y in range(CARD_HEIGHT):
                r = int(30 + (y / CARD_HEIGHT) * 20)
                g = int(30 + (y / CARD_HEIGHT) * 15)
                b = int(45 + (y / CARD_HEIGHT) * 30)
                draw.line([(0, y), (CARD_WIDTH, y)], fill=(r, g, b))

        draw = ImageDraw.Draw(img)

        # ─── AVATAR (دائري) — FIRST!
        avatar_size = 160
        avatar_x = 40
        avatar_y = (CARD_HEIGHT - avatar_size) // 2

        try:
            avatar_bytes = None
            for size in (512, 256, 128):
                try:
                    avatar_url = member.display_avatar.with_size(size).url
                    avatar_bytes = await self._fetch_avatar(avatar_url)
                    if avatar_bytes and len(avatar_bytes) > 0:
                        break
                except Exception as e:
                    print(f"⚠️ Try size {size} failed: {e}")
                    continue

            if avatar_bytes:
                avatar = self._circle_avatar(avatar_bytes, avatar_size)

                border_size = avatar_size + 8
                border = Image.new("RGBA", (border_size, border_size), (0, 0, 0, 0))
                bdraw = ImageDraw.Draw(border)
                bdraw.ellipse(
                    (0, 0, border_size - 1, border_size - 1),
                    outline=(255, 255, 255, 255),
                    width=4,
                )

                img.paste(avatar, (avatar_x, avatar_y), avatar=avatar)
                img.paste(border, (avatar_x - 4, avatar_y - 4), border)
                print(f"✅ Avatar paste OK: {member.name}")
            else:
                fallback = Image.new("RGBA", (avatar_size, avatar_size), (80, 80, 100, 255))
                mask = Image.new("L", (avatar_size, avatar_size), 0)
                mdraw = ImageDraw.Draw(mask)
                mdraw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                img.paste(fallback, (avatar_x, avatar_y), mask=mask)
        except Exception as e:
            print(f"❌ Avatar error: {e}")
            fallback = Image.new("RGBA", (avatar_size, avatar_size), (80, 80, 100, 255))
            mask = Image.new("L", (avatar_size, avatar_size), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
            img.paste(fallback, (avatar_x, avatar_y), mask=mask)

        # #POSITION
        pos_font = self._get_font(42)
        pos_text = f"#{rank_position}"
        bbox = draw.textbbox((0, 0), pos_text, font=pos_font)
        pos_w = bbox[2] - bbox[0]
        draw.text((CARD_WIDTH - pos_w - 40, 30), pos_text, fill=TEXT_COLOR, font=pos_font)

        # Username
        name_font = self._get_font(36)
        username = member.name[:20]
        draw.text((230, 35), username, fill=TEXT_COLOR, font=name_font)

        # Bars
        bar_x = 230
        bar_width = 580
        label_font = self._get_font(20)

        # BAR 1: Level
        bar1_y = 100
        bar1_height = 28
        draw.text((bar_x, bar1_y - 28), f"Level {current_level}", fill=SUBTLE_COLOR, font=label_font)

        xp_text = f"{current_xp:,} / {needed:,} XP"
        bbox = draw.textbbox((0, 0), xp_text, font=label_font)
        xp_w = bbox[2] - bbox[0]
        draw.text((bar_x + bar_width - xp_w, bar1_y - 28), xp_text, fill=SUBTLE_COLOR, font=label_font)

        draw.rounded_rectangle(
            (bar_x, bar1_y, bar_x + bar_width, bar1_y + bar1_height),
            radius=bar1_height // 2,
            fill=BAR_BG,
        )
        fill_width = int(bar_width * progress)
        if fill_width > 0:
            draw.rounded_rectangle(
                (bar_x, bar1_y, bar_x + fill_width, bar1_y + bar1_height),
                radius=bar1_height // 2,
                fill=BAR_FILL,
            )

        # BAR 2: Bir
        bar2_y = 165
        bar2_height = 28
        draw.text((bar_x, bar2_y - 28), "Bir", fill=SUBTLE_COLOR, font=label_font)

        bir_text = f"{bir_data.get('bir', 0):,}"
        bbox = draw.textbbox((0, 0), bir_text, font=label_font)
        bir_w = bbox[2] - bbox[0]
        draw.text((bar_x + bar_width - bir_w, bar2_y - 28), bir_text, fill=SUBTLE_COLOR, font=label_font)

        draw.rounded_rectangle(
            (bar_x, bar2_y, bar_x + bar_width, bar2_y + bar2_height),
            radius=bar2_height // 2,
            fill=BAR_BG,
        )
        draw.rounded_rectangle(
            (bar_x, bar2_y, bar_x + bar_width, bar2_y + bar2_height),
            radius=bar2_height // 2,
            fill=BAR_FILL_2,
        )

        output = io.BytesIO()
        img.save(output, format="PNG", optimize=True)
        output.seek(0)
        return output

    @app_commands.command(name="rankcard", description="Chouf rank card dyalk")
    @app_commands.describe(member="L-user")
    async def rankcard(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        if member is None:
            member = interaction.user

        try:
            img = await self.build_rank_card(member, interaction.guild)
            file = discord.File(img, filename="rank.png")
            await interaction.followup.send(file=file)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur: `{e}`")
            print(f"❌ Rank card error: {e}")

    @commands.command(name="rcard")
    async def rcard_prefix(self, ctx: commands.Context, member: discord.Member = None):
        """+rcard [@user] — Rank card b صورة"""
        if member is None:
            member = ctx.author

        async with ctx.typing():
            try:
                img = await self.build_rank_card(member, ctx.guild)
                file = discord.File(img, filename="rank.png")
                await ctx.send(file=file)
            except Exception as e:
                await ctx.send(f"❌ Erreur: `{e}`")
                print(f"❌ Rank card error: {e}")


async def setup(bot):
    await bot.add_cog(RankCard(bot))