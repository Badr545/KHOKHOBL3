# web/auth.py
# =====================================================================
# ─── DISCORD OAUTH2 — Login + session
# =====================================================================
import os
import requests
from functools import wraps
from flask import session, redirect, url_for, request, jsonify


DISCORD_API = "https://discord.com/api/v10"
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8080/callback")

OAUTH_URL = (
    f"https://discord.com/oauth2/authorize?"
    f"client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    f"&response_type=code&scope=identify%20guilds"
)


def get_login_url() -> str:
    return OAUTH_URL


def exchange_code(code: str) -> dict | None:
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        r = requests.post(f"{DISCORD_API}/oauth2/token", data=data, headers=headers, timeout=10)
        if r.status_code != 200:
            print(f"❌ OAuth token: {r.status_code} {r.text}")
            return None
        return r.json()
    except Exception as e:
        print(f"❌ OAuth exchange: {e}")
        return None


def get_user(access_token: str) -> dict | None:
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        r = requests.get(f"{DISCORD_API}/users/@me", headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


def get_user_guilds(access_token: str) -> list:
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        r = requests.get(f"{DISCORD_API}/users/@me/guilds", headers=headers, timeout=10)
        if r.status_code != 200:
            return []
        return r.json()
    except Exception:
        return []


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "unauthorized"}), 401
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated