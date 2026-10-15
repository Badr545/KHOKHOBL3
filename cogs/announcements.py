# =====================================================================
# ─── ANNOUNCEMENTS — Event / Meeting / News (Styled + Ping)
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import require_any_role, require_any_role_prefix
from botconfig import HELPER_ROLES, MODERATOR_ROLES, ADMIN_ROLES


SEP = "✧─────────────────✧"
ANNOUNCER_ROLES = HELPER_ROLES + MODERATOR_ROLES + ADMIN_ROLES


# ═══════════════════════════════════════════════════════════════════
# ─── PING HELPER
# ═══════════════════════════════════════════════════════════════════
def resolve_ping(ping_type: str, guild: discord.Guild) -> str:
    """
    Rje3 mention string 7sab ping_type.
    ping_type: 'none' | 'everyone' | 'here' | 'community'
    """
    if not ping_type:
        return ""
    p = str(ping_type).lower().strip()
    if p in ("none", "no", "off", "", "false"):
        return ""
    if p in ("everyone", "@everyone", "all", "true"):
        return "@everyone"
    if p in ("here", "@here"):
        return "@here"
    if p in ("community", "cm", "manager", "community manager"):
        for role in guild.roles:
            if "community manager" in role.name.lower():
                return role.mention
        return ""
    return ""


def _ping_sections(ping_type: str) -> list:
    """Rje3 list dyal sections dyal ping bash nzidohom f description."""
    if not ping_type:
        return []
    p = str(ping_type).lower().strip()
    if p in ("everyone", "@everyone", "all", "true"):
        return ["@everyone", SEP]
    if p in ("here", "@here"):
        return ["@here", SEP]
    return []


# ═══════════════════════════════════════════════════════════════════
# ─── STYLED BUILDERS
# ═══════════════════════════════════════════════════════════════════
def build_event_embed(
    title: str,
    *,
    event_time: str = None,
    event_prize: str = None,
    concept: str = None,
    host: str = None,
    author: discord.Member = None,
    ping_type: str = None,
    color: discord.Color = discord.Color.from_rgb(255, 105, 180),
) -> discord.Embed:
    """🎉 Event announcement."""
    sections = []

    # Ping f l-top
    sections.extend(_ping_sections(ping_type))

    if event_time:
        sections.append(f"🍓 • **Event Time :** {event_time}")
    if event_prize:
        sections.append(f"🍓 • **Event Prize :** {event_prize}")
    if event_time or event_prize:
        sections.append(SEP)
    if concept:
        sections.append(f"💥 • **Concept :**\n{concept}")
        sections.append(SEP)
    if host:
        sections.append(f"🎉 • **Host :** {host}")
        sections.append(SEP)

    description = "\n\n".join(sections) if sections else "..."

    embed = discord.Embed(
        title=f"⭐  {title}  ⭐",
        description=description,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    if author:
        embed.set_footer(
            text=f"Par {author.name}",
            icon_url=author.display_avatar.url,
        )
    return embed


def build_meeting_embed(
    title: str,
    *,
    meeting_date: str = None,
    meeting_time: str = None,
    location: str = None,
    agenda: str = None,
    host: str = None,
    author: discord.Member = None,
    ping_type: str = None,
    color: discord.Color = discord.Color.from_rgb(88, 101, 242),
) -> discord.Embed:
    """📅 Meeting announcement."""
    sections = []

    # Ping f l-top
    sections.extend(_ping_sections(ping_type))

    date_line = []
    if meeting_date:
        date_line.append(f"📅 **Date :** {meeting_date}")
    if meeting_time:
        date_line.append(f"⏰ **Time :** {meeting_time}")
    if date_line:
        sections.append("\n".join(date_line))
        sections.append(SEP)

    if location:
        sections.append(f"📍 • **Location :** {location}")
        sections.append(SEP)

    if agenda:
        sections.append(f"📋 • **Agenda :**\n{agenda}")
        sections.append(SEP)

    if host:
        sections.append(f"🎤 • **Host :** {host}")
        sections.append(SEP)

    description = "\n\n".join(sections) if sections else "..."

    embed = discord.Embed(
        title=f"📅  {title}  📅",
        description=description,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    if author:
        embed.set_footer(
            text=f"Par {author.name}",
            icon_url=author.display_avatar.url,
        )
    return embed


def build_news_embed(
    title: str,
    *,
    message: str,
    category: str = None,
    link: str = None,
    author: discord.Member = None,
    ping_type: str = None,
    color: discord.Color = discord.Color.from_rgb(255, 200, 0),
) -> discord.Embed:
    """📰 News announcement."""
    sections = []

    # Ping f l-top
    sections.extend(_ping_sections(ping_type))

    if category:
        sections.append(f"🏷️ • **Category :** `{category}`")
        sections.append(SEP)

    if message:
        sections.append(f"📢 • **Details :**\n{message}")
        sections.append(SEP)

    if link:
        sections.append(f"🔗 • **Link :** {link}")
        sections.append(SEP)

    description = "\n\n".join(sections) if sections else "..."

    embed = discord.Embed(
        title=f"📰  {title}  📰",
        description=description,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    if author:
        embed.set_footer(
            text=f"Par {author.name}",
            icon_url=author.display_avatar.url,
        )
    return embed


# ═══════════════════════════════════════════════════════════════════
# ─── COG
# ═══════════════════════════════════════════════════════════════════
class Announcements(commands.Cog):
    """Announcements: event / meeting / news / embed"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════════════════════════
    # ─── /announce (type + ping choices)
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="announce", description="Sift announcement (event / meeting / news)")
    @app_commands.choices(
        type=[
            app_commands.Choice(name="🎉 Event", value="event"),
            app_commands.Choice(name="📅 Meeting", value="meeting"),
            app_commands.Choice(name="📰 News", value="news"),
        ],
        ping=[
            app_commands.Choice(name="🔕 Bla ping", value="none"),
            app_commands.Choice(name="📢 @everyone", value="everyone"),
            app_commands.Choice(name="📍 @here", value="here"),
            app_commands.Choice(name="⚜️ Community Manager", value="community"),
        ],
    )
    @app_commands.describe(
        type="Type dyal announcement",
        title="Titre",
        message="Message / Concept / Agenda / Details",
        time_or_date="Event: 'TODAY, 22:00' | Meeting: '2025-01-15 21:00'",
        prize="(Event only) Prize",
        host="Host (mentions)",
        location="(Meeting only) Location",
        category="(News only) Category",
        link="(News only) Link",
        channel="Channel (optionnel)",
        ping="Ping type",
        color="Lon (hex)",
    )
    @require_any_role(*ANNOUNCER_ROLES)
    async def announce(
        self,
        interaction: discord.Interaction,
        type: app_commands.Choice[str],
        title: str,
        message: str = None,
        time_or_date: str = None,
        prize: str = None,
        host: str = None,
        location: str = None,
        category: str = None,
        link: str = None,
        channel: discord.TextChannel = None,
        ping: app_commands.Choice[str] = None,
        color: str = None,
    ):
        if channel is None:
            channel = interaction.channel

        embed_color = None
        if color:
            try:
                embed_color = discord.Color(int(color.replace("#", ""), 16))
            except Exception:
                embed_color = None

        t = type.value
        ping_type = ping.value if ping else None

        # ─── Build
        if t == "event":
            kwargs = dict(
                title=title,
                event_time=time_or_date,
                event_prize=prize,
                concept=message,
                host=host,
                author=interaction.user,
                ping_type=ping_type,
            )
            if embed_color:
                kwargs["color"] = embed_color
            embed = build_event_embed(**kwargs)

        elif t == "meeting":
            m_date, m_time = None, None
            if time_or_date:
                parts = time_or_date.split(" ", 1)
                m_date = parts[0]
                if len(parts) > 1:
                    m_time = parts[1]

            kwargs = dict(
                title=title,
                meeting_date=m_date,
                meeting_time=m_time,
                location=location,
                agenda=message,
                host=host,
                author=interaction.user,
                ping_type=ping_type,
            )
            if embed_color:
                kwargs["color"] = embed_color
            embed = build_meeting_embed(**kwargs)

        else:  # news
            kwargs = dict(
                title=title,
                message=message or "...",
                category=category,
                link=link,
                author=interaction.user,
                ping_type=ping_type,
            )
            if embed_color:
                kwargs["color"] = embed_color
            embed = build_news_embed(**kwargs)

        # ⭐ Ping f content bach ykhdem b7a9
        content = resolve_ping(ping_type, interaction.guild) if ping_type else ""

        try:
            await channel.send(content=content or None, embed=embed)
            await interaction.response.send_message(
                f"✅ Sift f {channel.mention}! (ping: `{ping_type or 'none'}`)",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Ma 3ndich permission!", ephemeral=True
            )

    # ═══════════════════════════════════════════════════════════
    # ─── &announce (PREFIX)
    # ─── &announce event | Title | time | prize | concept | host | [ping]
    # ─── &announce meeting | Title | date | time | location | agenda | host | [ping]
    # ─── &announce news | Title | category | message | link | [ping]
    # ═══════════════════════════════════════════════════════════
    @commands.command(name="announce")
    @require_any_role_prefix(*ANNOUNCER_ROLES)
    async def announce_prefix(self, ctx: commands.Context, type: str = "event", *, body: str = ""):
        """
        &announce event | Title | time | prize | concept | host | [ping]
        &announce meeting | Title | date | time | location | agenda | host | [ping]
        &announce news | Title | category | message | link | [ping]

        ping (optionnel f l-a5er): everyone / here / community / none
        """
        t = type.lower().strip()

        if t not in ("event", "meeting", "news"):
            return await ctx.send(
                "❌ Type khass ykoun: `event`, `meeting`, wla `news`\n"
                "**Amthila:**\n"
                "`&announce event | GUESS THE ENDING | TODAY, 22:00 | 500 DH | Roulette... | @OUT MAN | everyone`\n"
                "`&announce meeting | Staff Meeting | 2025-01-15 | 21:00 | VC General | Agenda... | @Admin | here`\n"
                "`&announce news | Bot Update | Update | Version jdida... | https://... | community`"
            )

        parts = [p.strip() for p in body.split("|")] if body else []
        title = parts[0] if len(parts) > 0 and parts[0] else "Sans titre"

        # ⭐ Ping huwa l-a5er element (ila kayn)
        ping_type = None
        if len(parts) >= 2:
            last = parts[-1].lower().strip()
            if last in ("everyone", "here", "community", "none",
                        "@everyone", "@here", "cm", "manager"):
                ping_type = last
                parts = parts[:-1]

        # ─── Build 7sab type
        if t == "event":
            event_time = parts[1] if len(parts) > 1 and parts[1] else None
            prize = parts[2] if len(parts) > 2 and parts[2] else None
            concept = parts[3] if len(parts) > 3 and parts[3] else None
            host = parts[4] if len(parts) > 4 and parts[4] else None
            embed = build_event_embed(
                title,
                event_time=event_time,
                event_prize=prize,
                concept=concept,
                host=host,
                author=ctx.author,
                ping_type=ping_type,
            )

        elif t == "meeting":
            m_date = parts[1] if len(parts) > 1 and parts[1] else None
            m_time = parts[2] if len(parts) > 2 and parts[2] else None
            location = parts[3] if len(parts) > 3 and parts[3] else None
            agenda = parts[4] if len(parts) > 4 and parts[4] else None
            host = parts[5] if len(parts) > 5 and parts[5] else None
            embed = build_meeting_embed(
                title,
                meeting_date=m_date,
                meeting_time=m_time,
                location=location,
                agenda=agenda,
                host=host,
                author=ctx.author,
                ping_type=ping_type,
            )

        else:  # news
            category = parts[1] if len(parts) > 1 and parts[1] else None
            msg = parts[2] if len(parts) > 2 and parts[2] else "..."
            link = parts[3] if len(parts) > 3 and parts[3] else None
            embed = build_news_embed(
                title,
                message=msg,
                category=category,
                link=link,
                author=ctx.author,
                ping_type=ping_type,
            )

        # ⭐ Ping f content
        content = resolve_ping(ping_type, ctx.guild) if ping_type else ""
        await ctx.send(content=content or None, embed=embed)

    # ═══════════════════════════════════════════════════════════
    # ─── /embed
    # ═══════════════════════════════════════════════════════════
    @app_commands.command(name="embed", description="3mel embed custom")
    @require_any_role(*ANNOUNCER_ROLES)
    async def embed(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        color: str = "#5865F2",
        image: str = None,
        thumbnail: str = None,
    ):
        try:
            embed_color = discord.Color(int(color.replace("#", ""), 16))
        except Exception:
            embed_color = discord.Color.blurple()

        em = discord.Embed(title=title, description=description, color=embed_color)
        if image:
            em.set_image(url=image)
        if thumbnail:
            em.set_thumbnail(url=thumbnail)
        em.set_footer(text=f"Par {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        await interaction.channel.send(embed=em)
        await interaction.response.send_message("✅ Embed sift!", ephemeral=True)

    @commands.command(name="embed")
    @require_any_role_prefix(*ANNOUNCER_ROLES)
    async def embed_prefix(self, ctx: commands.Context, title: str, description: str, color: str = "#5865F2"):
        """&embed <title> | <description>"""
        try:
            embed_color = discord.Color(int(color.replace("#", ""), 16))
        except Exception:
            embed_color = discord.Color.blurple()

        em = discord.Embed(title=title, description=description, color=embed_color)
        em.set_footer(text=f"Par {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=em)


async def setup(bot):
    await bot.add_cog(Announcements(bot))