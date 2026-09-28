# web/app.py
# =====================================================================
# ─── WEB DASHBOARD — Flask + Discord OAuth2
# =====================================================================
import os
import sys
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from dotenv import load_dotenv

# Load env
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from web.auth import (
    get_login_url, exchange_code, get_user, get_user_guilds, login_required,
)
from web.api import api_bp
from web.db import get_guild_stats, get_user_economy, get_user_levels, get_user_bir


app = Flask(__name__)
app.secret_key = os.getenv("WEB_SECRET_KEY", "change_me_in_env")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True

app.register_blueprint(api_bp)


# ═══════════════════════════════════════════════════════════════════
# ─── PAGES
# ═══════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    user = session.get("user")
    return render_template(
        "index.html",
        user=user,
        login_url=get_login_url(),
    )


@app.route("/login")
def login():
    return redirect(get_login_url())


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return redirect(url_for("index"))

    tokens = exchange_code(code)
    if not tokens:
        return "❌ Login failed", 400

    access_token = tokens["access_token"]
    user = get_user(access_token)
    if not user:
        return "❌ Failed to get user", 400

    guilds = get_user_guilds(access_token)

    session["user"] = {
        "id": user["id"],
        "username": user["username"],
        "discriminator": user.get("discriminator", "0"),
        "avatar": user.get("avatar"),
        "global_name": user.get("global_name"),
    }
    session["guilds"] = guilds
    session["access_token"] = access_token

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = session.get("user")
    guilds = session.get("guilds", [])
    admin_guilds = [g for g in guilds if (int(g.get("permissions", 0)) & 0x8) == 0x8]
    return render_template(
        "dashboard.html",
        user=user,
        admin_guilds=admin_guilds,
        guilds=guilds,
    )


@app.route("/servers")
@login_required
def servers():
    user = session.get("user")
    guilds = session.get("guilds", [])
    admin_guilds = [g for g in guilds if (int(g.get("permissions", 0)) & 0x8) == 0x8]
    return render_template("servers.html", user=user, guilds=admin_guilds)


@app.route("/server/<int:guild_id>")
@login_required
def server_detail(guild_id: int):
    user = session.get("user")
    guilds = session.get("guilds", [])
    guild = next((g for g in guilds if int(g["id"]) == guild_id), None)
    if not guild:
        return redirect(url_for("servers"))

    stats = get_guild_stats(guild_id)
    my_eco = get_user_economy(guild_id, int(user["id"]))
    my_lv = get_user_levels(guild_id, int(user["id"]))
    my_bir = get_user_bir(guild_id, int(user["id"]))

    return render_template(
        "server.html",
        user=user,
        guild=guild,
        stats=stats,
        my_eco=my_eco,
        my_lv=my_lv,
        my_bir=my_bir,
    )


# ═══════════════════════════════════════════════════════════════════
# ─── ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# ═══════════════════════════════════════════════════════════════════
# ─── TEMPLATE FILTERS
# ═══════════════════════════════════════════════════════════════════
@app.template_filter("avatar_url")
def avatar_url(user):
    if not user:
        return "https://cdn.discordapp.com/embed/avatars/0.png"
    uid = user.get("id")
    avatar = user.get("avatar")
    if not avatar:
        return f"https://cdn.discordapp.com/embed/avatars/0.png"
    ext = "gif" if avatar.startswith("a_") else "png"
    return f"https://cdn.discordapp.com/avatars/{uid}/{avatar}.{ext}?size=256"


@app.template_filter("guild_icon")
def guild_icon(guild):
    if not guild or not guild.get("icon"):
        return "https://cdn.discordapp.com/embed/avatars/0.png"
    return f"https://cdn.discordapp.com/icons/{guild['id']}/{guild['icon']}.png?size=128"


@app.template_filter("fmt_num")
def fmt_num(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)


if __name__ == "__main__":
    port = int(os.getenv("WEB_PORT", 8080))
    print(f"🌐 Web dashboard running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)