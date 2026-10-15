# =====================================================================
# ─── INFO COMMANDS (anime, manga, weather, translate, lyrics, ...)
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from datetime import datetime
from urllib.parse import quote


# ═══════════════════════════════════════════════════════════════════
# ─── LANG ALIASES
# ═══════════════════════════════════════════════════════════════════
LANG_ALIASES = {
    "arabe": "ar", "arabic": "ar", "3arabiya": "ar", "arabiya": "ar",
    "francais": "fr", "french": "fr", "français": "fr",
    "english": "en", "anglais": "en", "engliyziya": "en",
    "espanol": "es", "spanish": "es", "español": "es",
    "deutsch": "de", "german": "de", "almaniya": "de",
    "italian": "it", "italiano": "it", "talyan": "it",
    "portuguese": "pt", "portugais": "pt",
    "russian": "ru", "russe": "ru",
    "japanese": "ja", "japoniya": "ja", "japonais": "ja",
    "korean": "ko", "coreen": "ko",
    "chinese": "zh", "chinois": "zh", "siniwiya": "zh",
    "turkish": "tr", "turc": "tr",
    "dutch": "nl", "neerlandais": "nl",
    "polish": "pl", "polonais": "pl",
    "hindi": "hi",
}


def resolve_lang(code: str) -> str:
    """Beddel alias l code, wla rje3 code as-is"""
    code = code.lower().strip()
    return LANG_ALIASES.get(code, code)


def is_valid_lang(code: str) -> bool:
    """Check wach code lugha s7i7 (2-3 lettres)"""
    return code.isalpha() and 2 <= len(code) <= 3


class Info(commands.Cog):
    """Info: anime, manga, weather, translate, lyrics, banner, roles, members, bots, invites"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════════════════════════
    # ─── /anime
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="anime", description="Ma3loumat anime")
    async def anime(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer()
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"https://api.jikan.moe/v4/anime?q={title}&limit=1") as r:
                    data = await r.json()
            if not data.get("data"):
                return await interaction.followup.send("❌ Ma l9itch!")
            a = data["data"][0]
            embed = discord.Embed(
                title=a["title"],
                url=a.get("url"),
                description=(a.get("synopsis") or "")[:300] + "...",
                color=discord.Color.purple(),
            )
            if a.get("images", {}).get("jpg", {}).get("image_url"):
                embed.set_thumbnail(url=a["images"]["jpg"]["image_url"])
            embed.add_field(name="⭐ Score", value=str(a.get("score") or "N/A"), inline=True)
            embed.add_field(name="📺 Episodes", value=str(a.get("episodes") or "N/A"), inline=True)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ `{e}`")

    # ═══════════════════════════════════════════════════════════
    # ─── /manga
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="manga", description="Ma3loumat manga")
    async def manga(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer()
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"https://api.jikan.moe/v4/manga?q={title}&limit=1") as r:
                    data = await r.json()
            if not data.get("data"):
                return await interaction.followup.send("❌ Ma l9itch!")
            m = data["data"][0]
            embed = discord.Embed(
                title=m["title"],
                url=m.get("url"),
                color=discord.Color.dark_purple(),
            )
            if m.get("images", {}).get("jpg", {}).get("image_url"):
                embed.set_thumbnail(url=m["images"]["jpg"]["image_url"])
            embed.add_field(name="⭐ Score", value=str(m.get("score") or "N/A"), inline=True)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ `{e}`")

    # ═══════════════════════════════════════════════════════════
    # ─── /weather (Open-Meteo)
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="weather", description="Weather f chi mdina")
    @app_commands.describe(city="Smiya dyal l-mdina")
    async def weather(self, interaction: discord.Interaction, city: str):
        await interaction.response.defer()
        try:
            async with aiohttp.ClientSession() as s:
                geo_url = (
                    f"https://geocoding-api.open-meteo.com/v1/search"
                    f"?name={quote(city)}&count=1&language=en&format=json"
                )
                async with s.get(geo_url) as r:
                    geo_data = await r.json()

                if not geo_data.get("results"):
                    return await interaction.followup.send(f"❌ Ma l9itch mdina: `{city}`")

                loc = geo_data["results"][0]
                lat, lon = loc["latitude"], loc["longitude"]
                name = loc["name"]
                country = loc.get("country", "")

                weather_url = (
                    f"https://api.open-meteo.com/v1/forecast?"
                    f"latitude={lat}&longitude={lon}"
                    f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
                    f"&timezone=auto"
                )
                async with s.get(weather_url) as r:
                    w = await r.json()

                c = w["current"]
                emoji, desc = self._weather_desc(c["weather_code"])

                embed = discord.Embed(
                    title=f"{emoji} Weather f {name}, {country}",
                    description=f"**{desc}**",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(),
                )
                embed.add_field(name="🌡️ Temp", value=f"`{c['temperature_2m']}°C`", inline=True)
                embed.add_field(name="💧 Humidity", value=f"`{c['relative_humidity_2m']}%`", inline=True)
                embed.add_field(name="💨 Wind", value=f"`{c['wind_speed_10m']} km/h`", inline=True)
                embed.set_footer(text="Powered by Open-Meteo")

                await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur: `{e}`")

    # ═══════════════════════════════════════════════════════════
    # ─── /translate
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="translate", description="Traduchi text")
    @app_commands.describe(
        text="Text li bghiti t-traduchi",
        to="L-lugha (ar, fr, en, arabe, francais, english...)",
    )
    async def translate(self, interaction: discord.Interaction, text: str, to: str = "en"):
        await interaction.response.defer()

        to = resolve_lang(to)
        if not is_valid_lang(to):
            return await interaction.followup.send(
                "❌ Code lugha ghalat!\n"
                "**Amthila:** `ar`, `fr`, `en`, `es`, `de`, `ja`, `zh`\n"
                "Wla b smiya: `arabe`, `francais`, `english`..."
            )

        result = await self._translate_text(text, to)
        if result is None:
            return await interaction.followup.send(
                "❌ Google rfed l-request. 3awed jereb mn ba3d."
            )

        await interaction.followup.send(
            f"🌐 **Original:** {text}\n**→ Traduction ({to}):** {result}"
        )

    # ═══════════════════════════════════════════════════════════
    # ─── /lyrics
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="lyrics", description="Jib lyrics dyal chi gheniya")
    @app_commands.describe(
        artist="Smiya dyal l-fennan (ex: Adele)",
        title="Smiya dyal gheniya (ex: Hello)",
    )
    async def lyrics(self, interaction: discord.Interaction, artist: str, title: str):
        await interaction.response.defer()

        lyrics_text = await self._fetch_lyrics(artist, title)
        if lyrics_text is None:
            return await interaction.followup.send(
                f"❌ Ma l9itch lyrics dyal **{title}** — **{artist}**\n"
                f"⚠️ T7eqqen mn smiya."
            )

        embed = self._build_lyrics_embed(title, artist, lyrics_text)
        await interaction.followup.send(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /banner
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="banner", description="Banner")
    async def banner(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        if member is None:
            member = interaction.user
        try:
            user = await self.bot.fetch_user(member.id)
            if user.banner:
                embed = discord.Embed(title=f"🖼️ {member.name}", color=discord.Color.blurple())
                embed.set_image(url=user.banner.url)
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ Ma 3endouch banner!")
        except Exception as e:
            await interaction.followup.send(f"❌ `{e}`")

    # ═══════════════════════════════════════════════════════════
    # ─── /roles
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="roles", description="Roles")
    async def roles(self, interaction: discord.Interaction):
        await interaction.response.defer()
        roles = [r for r in interaction.guild.roles if not r.is_default()]
        roles.reverse()
        chunks = [roles[i:i+20] for i in range(0, len(roles), 20)]
        embed = discord.Embed(title=f"🎭 Roles ({len(roles)})", color=discord.Color.teal())
        for chunk in chunks[:5]:
            embed.add_field(name="\u200b", value=" ".join(r.mention for r in chunk), inline=False)
        await interaction.followup.send(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /members
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="members", description="Members stats")
    async def members(self, interaction: discord.Interaction):
        await interaction.response.defer()
        g = interaction.guild
        online = sum(1 for m in g.members if m.status != discord.Status.offline)
        bots = sum(1 for m in g.members if m.bot)
        embed = discord.Embed(title="👥 Members", color=discord.Color.green())
        embed.add_field(name="📊 Total", value=f"`{g.member_count}`", inline=True)
        embed.add_field(name="🟢 Online", value=f"`{online}`", inline=True)
        embed.add_field(name="👤 Humans", value=f"`{g.member_count - bots}`", inline=True)
        embed.add_field(name="🤖 Bots", value=f"`{bots}`", inline=True)
        await interaction.followup.send(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /bots
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="bots", description="Bots f server")
    async def bots(self, interaction: discord.Interaction):
        await interaction.response.defer()
        bots = [m for m in interaction.guild.members if m.bot]
        if not bots:
            return await interaction.followup.send("❌ Ma kaynch bots!")
        embed = discord.Embed(title=f"🤖 Bots ({len(bots)})", color=discord.Color.dark_gray())
        embed.description = "\n".join(f"{b.mention} — `{b.id}`" for b in bots[:30])
        await interaction.followup.send(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /invites
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="invites", description="Invitations")
    async def invites(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            invites = await interaction.guild.invites()
            if not invites:
                return await interaction.followup.send("❌ Ma kaynin!", ephemeral=True)
            embed = discord.Embed(title="📨 Invitations", color=discord.Color.blue())
            for inv in invites[:15]:
                uses = f"{inv.uses}/{inv.max_uses}" if inv.max_uses else f"{inv.uses}/∞"
                embed.add_field(name=inv.code, value=f"Uses: `{uses}`", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ Permission `Manage Server`!", ephemeral=True)

    # ═══════════════════════════════════════════════════════════
    # ─── PREFIX COMMANDS
    # ═══════════════════════════════════════════════════════════

    @commands.command(name="anime")
    async def anime_prefix(self, ctx: commands.Context, *, title: str):
        """&anime <title>"""
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"https://api.jikan.moe/v4/anime?q={title}&limit=1") as r:
                    data = await r.json()
            if not data.get("data"):
                return await ctx.send("❌ Ma l9itch!")
            a = data["data"][0]
            embed = discord.Embed(title=a["title"], url=a.get("url"), color=discord.Color.purple())
            if a.get("images", {}).get("jpg", {}).get("image_url"):
                embed.set_thumbnail(url=a["images"]["jpg"]["image_url"])
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ `{e}`")

    @commands.command(name="manga")
    async def manga_prefix(self, ctx: commands.Context, *, title: str):
        """&manga <title>"""
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"https://api.jikan.moe/v4/manga?q={title}&limit=1") as r:
                    data = await r.json()
            if not data.get("data"):
                return await ctx.send("❌ Ma l9itch!")
            m = data["data"][0]
            embed = discord.Embed(title=m["title"], url=m.get("url"), color=discord.Color.dark_purple())
            if m.get("images", {}).get("jpg", {}).get("image_url"):
                embed.set_thumbnail(url=m["images"]["jpg"]["image_url"])
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ `{e}`")

    @commands.command(name="weather")
    async def weather_prefix(self, ctx: commands.Context, *, city: str):
        """&weather <city>"""
        try:
            async with aiohttp.ClientSession() as s:
                geo_url = (
                    f"https://geocoding-api.open-meteo.com/v1/search"
                    f"?name={quote(city)}&count=1&language=en&format=json"
                )
                async with s.get(geo_url) as r:
                    geo_data = await r.json()

                if not geo_data.get("results"):
                    return await ctx.send(f"❌ Ma l9itch mdina: `{city}`")

                loc = geo_data["results"][0]
                lat, lon = loc["latitude"], loc["longitude"]
                name = loc["name"]
                country = loc.get("country", "")

                weather_url = (
                    f"https://api.open-meteo.com/v1/forecast?"
                    f"latitude={lat}&longitude={lon}"
                    f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
                    f"&timezone=auto"
                )
                async with s.get(weather_url) as r:
                    w = await r.json()

                c = w["current"]
                await ctx.send(
                    f"🌤️ **{name}, {country}**\n"
                    f"🌡️ `{c['temperature_2m']}°C` | "
                    f"💧 `{c['relative_humidity_2m']}%` | "
                    f"💨 `{c['wind_speed_10m']} km/h`"
                )
        except Exception as e:
            await ctx.send(f"❌ Erreur: `{e}`")

    @commands.command(name="translate")
    async def translate_prefix(self, ctx: commands.Context, to: str, *, text: str):
        """&translate <to> <text>  —  ex: &translate ar hello"""
        to = resolve_lang(to)
        if not is_valid_lang(to):
            return await ctx.send(
                "❌ Code lugha ghalat!\n"
                "**Amthila:** `ar`, `fr`, `en`, `es`, `de`, `ja`, `zh`\n"
                "Wla b smiya: `arabe`, `francais`, `english`..."
            )

        result = await self._translate_text(text, to)
        if result is None:
            return await ctx.send("❌ Google rfed l-request. 3awed jereb mn ba3d.")

        await ctx.send(f"🌐 **Original:** {text}\n**→ Traduction ({to}):** {result}")

    @commands.command(name="lyrics")
    async def lyrics_prefix(self, ctx: commands.Context, artist: str, *, title: str):
        """&lyrics <artist> <title>  —  ex: &lyrics Adele Hello"""
        lyrics_text = await self._fetch_lyrics(artist, title)
        if lyrics_text is None:
            return await ctx.send(
                f"❌ Ma l9itch lyrics dyal **{title}** — **{artist}**\n"
                f"⚠️ T7eqqen mn smiya."
            )

        embed = self._build_lyrics_embed(title, artist, lyrics_text)
        await ctx.send(embed=embed)

    @commands.command(name="banner")
    async def banner_prefix(self, ctx: commands.Context, member: discord.Member = None):
        """&banner [@user]"""
        if member is None:
            member = ctx.author
        try:
            user = await self.bot.fetch_user(member.id)
            if user.banner:
                embed = discord.Embed(title=f"🖼️ {member.name}", color=discord.Color.blurple())
                embed.set_image(url=user.banner.url)
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Ma 3endouch banner!")
        except Exception as e:
            await ctx.send(f"❌ `{e}`")

    @commands.command(name="roles")
    async def roles_prefix(self, ctx: commands.Context):
        """&roles"""
        roles = [r for r in ctx.guild.roles if not r.is_default()]
        roles.reverse()
        await ctx.send("🎭 **Roles:**\n" + " ".join(r.mention for r in roles[:30]))

    @commands.command(name="members")
    async def members_prefix(self, ctx: commands.Context):
        """&members"""
        g = ctx.guild
        online = sum(1 for m in g.members if m.status != discord.Status.offline)
        bots = sum(1 for m in g.members if m.bot)
        await ctx.send(
            f"👥 Total: `{g.member_count}` | 🟢 Online: `{online}` | "
            f"👤 Humans: `{g.member_count - bots}` | 🤖 Bots: `{bots}`"
        )

    @commands.command(name="bots")
    async def bots_prefix(self, ctx: commands.Context):
        """&bots"""
        bots = [m for m in ctx.guild.members if m.bot]
        if not bots:
            return await ctx.send("❌ Ma kaynch bots!")
        await ctx.send(
            f"🤖 **Bots ({len(bots)}):**\n" +
            "\n".join(f"{b.mention} — `{b.id}`" for b in bots[:30])
        )

    # ═══════════════════════════════════════════════════════════
    # ─── HELPERS (private)
    # ═══════════════════════════════════════════════════════════

    async def _translate_text(self, text: str, to: str):
        """Traduchi text. Rje3 None ila fchel."""
        try:
            async with aiohttp.ClientSession() as s:
                url = (
                    f"https://translate.googleapis.com/translate_a/single"
                    f"?client=gtx&sl=auto&tl={to}&dt=t&q={quote(text)}"
                )
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                }
                async with s.get(url, headers=headers) as r:
                    ct = r.headers.get("Content-Type", "")
                    if "application/json" not in ct:
                        return None
                    data = await r.json()

            if not data or not data[0]:
                return None

            translated = "".join([x[0] for x in data[0] if x and x[0]])
            return translated or None

        except Exception:
            return None

    async def _fetch_lyrics(self, artist: str, title: str):
        """Jib lyrics mn lyrics.ovh. Rje3 None ila fchel."""
        try:
            async with aiohttp.ClientSession() as s:
                url = f"https://api.lyrics.ovh/v1/{quote(artist)}/{quote(title)}"
                async with s.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status != 200:
                        return None
                    data = await r.json()

            lyrics_text = data.get("lyrics", "").strip()
            if not lyrics_text:
                return None

            # Nadi l-lyrics
            lyrics_text = "\n".join(
                line.strip() for line in lyrics_text.splitlines() if line.strip()
            )
            return lyrics_text

        except Exception as e:
            print(f"❌ Lyrics error: {e}")
            return None

    def _build_lyrics_embed(self, title: str, artist: str, lyrics_text: str) -> discord.Embed:
        """3mel embed dyal lyrics"""
        if len(lyrics_text) > 4000:
            lyrics_text = lyrics_text[:4000] + "\n\n**... (b9a chwiya)**"

        embed = discord.Embed(
            title=f"🎵 {title}",
            description=f"**Par:** {artist}\n\n{lyrics_text}",
            color=discord.Color.from_rgb(30, 215, 96),
        )
        embed.set_footer(text="Powered by lyrics.ovh")
        return embed

    def _weather_desc(self, code: int):
        """Weather code → (emoji, description)"""
        weather_emojis = {
            0: ("☀️", "Safi (Clear)"),
            1: ("🌤️", "Chwiya s7ab (Mainly clear)"),
            2: ("⛅", "S7ab (Partly cloudy)"),
            3: ("☁️", "S7ab kbir (Overcast)"),
            45: ("🌫️", "Dbab (Fog)"),
            48: ("🌫️", "Dbab (Depositing rime fog)"),
            51: ("🌦️", "Chta khfifa (Light drizzle)"),
            53: ("🌦️", "Chta (Moderate drizzle)"),
            55: ("🌧️", "Chta qwiya (Dense drizzle)"),
            61: ("🌧️", "Chta khfifa (Slight rain)"),
            63: ("🌧️", "Chta (Moderate rain)"),
            65: ("🌧️", "Chta qwiya (Heavy rain)"),
            71: ("🌨️", "Talj khfif (Slight snow)"),
            73: ("🌨️", "Talj (Moderate snow)"),
            75: ("❄️", "Talj qwi (Heavy snow)"),
            80: ("🌦️", "Chta khfifa (Rain showers)"),
            81: ("🌧️", "Chta (Moderate showers)"),
            82: ("⛈️", "Chta qwiya (Violent showers)"),
            95: ("⛈️", "R3od (Thunderstorm)"),
            96: ("⛈️", "R3od m3a talj (Thunderstorm + hail)"),
            99: ("⛈️", "R3od qwi (Thunderstorm + heavy hail)"),
        }
        return weather_emojis.get(code, ("🌡️", "Unknown"))


async def setup(bot):
    await bot.add_cog(Info(bot))