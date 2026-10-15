# cogs/transcripts.py
# =====================================================================
# ─── TICKET TRANSCRIPTS — HTML export
# =====================================================================
import discord
from discord.ext import commands
from discord import app_commands
import os
import html
from datetime import datetime


TRANSCRIPT_DIR = "data/transcripts"


class Transcripts(commands.Cog):
    """Ticket transcripts generator"""

    def __init__(self, bot):
        self.bot = bot
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

    async def generate_html(self, channel: discord.TextChannel) -> str | None:
        """Generate HTML transcript dyal channel."""
        try:
            messages = []
            async for msg in channel.history(limit=500, oldest_first=True):
                messages.append(msg)
        except discord.Forbidden:
            return None

        # Build HTML
        html_parts = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='utf-8'>",
            f"<title>Transcript — #{html.escape(channel.name)}</title>",
            "<style>",
            "body{background:#36393f;color:#dcddde;font-family:'Segoe UI',sans-serif;padding:20px;}",
            ".msg{display:flex;padding:8px;border-bottom:1px solid #40444b;}",
            ".avatar{width:40px;height:40px;border-radius:50%;margin-right:12px;}",
            ".author{color:#fff;font-weight:600;margin-right:8px;}",
            ".time{color:#72767d;font-size:0.75em;margin-left:8px;}",
            ".content{flex:1;}",
            ".bot{background:#5865f2;color:#fff;padding:1px 4px;border-radius:3px;font-size:0.7em;margin-left:4px;}",
            ".embed{border-left:4px solid #5865f2;background:#2f3136;padding:8px;margin-top:4px;border-radius:4px;}",
            ".attach{color:#00b0f4;text-decoration:none;}",
            "</style></head><body>",
            f"<h1>📜 Transcript — #{html.escape(channel.name)}</h1>",
            f"<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
            f"<p>Total messages: {len(messages)}</p>",
            "<hr>",
        ]

        for msg in messages:
            author = html.escape(str(msg.author))
            content = html.escape(msg.content or "")
            time_str = msg.created_at.strftime("%Y-%m-%d %H:%M")
            avatar = msg.author.display_avatar.url
            bot_tag = '<span class="bot">BOT</span>' if msg.author.bot else ""

            # Attachments
            attach_html = ""
            for att in msg.attachments:
                attach_html += f'<br><a class="attach" href="{html.escape(att.url)}">📎 {html.escape(att.filename)}</a>'

            # Embeds
            embed_html = ""
            for emb in msg.embeds:
                embed_html += '<div class="embed">'
                if emb.title:
                    embed_html += f"<b>{html.escape(emb.title)}</b><br>"
                if emb.description:
                    embed_html += f"{html.escape(emb.description)}"
                embed_html += "</div>"

            html_parts.append(
                f'<div class="msg">'
                f'<img class="avatar" src="{html.escape(avatar)}">'
                f'<div class="content">'
                f'<span class="author">{author}</span>{bot_tag}'
                f'<span class="time">{time_str}</span>'
                f'<br>{content}{attach_html}{embed_html}'
                f'</div></div>'
            )

        html_parts.append("</body></html>")
        return "\n".join(html_parts)

    async def save_transcript(self, channel: discord.TextChannel) -> str | None:
        """Save transcript w rje3 l-path."""
        html_content = await self.generate_html(channel)
        if html_content is None:
            return None

        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"transcript-{channel.name}-{ts}.html"
        path = os.path.join(TRANSCRIPT_DIR, filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return path
        except Exception as e:
            print(f"❌ Transcript save: {e}")
            return None

    @app_commands.command(name="transcript", description="📜 Generate transcript dyal had channel")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def transcript_cmd(self, it: discord.Interaction):
        await it.response.defer(ephemeral=True)
        path = await self.save_transcript(it.channel)
        if path is None:
            return await it.followup.send("❌ Ma qdertch n-generate!", ephemeral=True)

        file = discord.File(path, filename=os.path.basename(path))
        await it.followup.send("✅ Transcript:", file=file, ephemeral=True)

    @commands.command(name="transcript")
    @commands.has_permissions(manage_messages=True)
    async def transcript_prefix(self, ctx: commands.Context):
        """+transcript — Generate transcript"""
        async with ctx.typing():
            path = await self.save_transcript(ctx.channel)
            if path is None:
                return await ctx.send("❌ Ma qdertch n-generate!")
            file = discord.File(path, filename=os.path.basename(path))
            await ctx.send("✅ Transcript:", file=file)


async def setup(bot):
    await bot.add_cog(Transcripts(bot))