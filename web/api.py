# web/api.py
# =====================================================================
# ─── REST API — endpoints l dashboard
# =====================================================================
from flask import Blueprint, jsonify, session
from web.db import (
    get_user_economy, get_user_levels, get_user_bir,
    get_leaderboard_money, get_leaderboard_levels,
    get_guild_stats, get_warnings,
)
from web.auth import login_required, get_user_guilds

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/me")
@login_required
def me():
    return jsonify(session["user"])


@api_bp.route("/me/guilds")
@login_required
def my_guilds():
    guilds = session.get("guilds", [])
    # Filter: admin only
    admin_guilds = [g for g in guilds if (int(g.get("permissions", 0)) & 0x8) == 0x8]
    return jsonify(admin_guilds)


@api_bp.route("/stats/<int:guild_id>/<int:user_id>")
@login_required
def user_stats(guild_id: int, user_id: int):
    eco = get_user_economy(guild_id, user_id)
    lv = get_user_levels(guild_id, user_id)
    bir = get_user_bir(guild_id, user_id)
    return jsonify({
        "economy": eco,
        "levels": lv,
        "bir": bir,
    })


@api_bp.route("/leaderboard/<int:guild_id>/money")
@login_required
def lb_money(guild_id: int):
    return jsonify(get_leaderboard_money(guild_id, 10))


@api_bp.route("/leaderboard/<int:guild_id>/levels")
@login_required
def lb_levels(guild_id: int):
    return jsonify(get_leaderboard_levels(guild_id, 10))


@api_bp.route("/guild/<int:guild_id>/stats")
@login_required
def guild_stats(guild_id: int):
    return jsonify(get_guild_stats(guild_id))


@api_bp.route("/guild/<int:guild_id>/warnings/<int:user_id>")
@login_required
def user_warnings(guild_id: int, user_id: int):
    return jsonify(get_warnings(guild_id, user_id))