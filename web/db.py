# web/db.py
# =====================================================================
# ─── DB BRIDGE — read-only queries l SQLite
# =====================================================================
import os
import sqlite3
import json
import threading

DB_PATH = os.getenv("DB_PATH", "data/bot.db")
_lock = threading.RLock()
_conn = None


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10.0)
        _conn.row_factory = sqlite3.Row
        try:
            _conn.execute("PRAGMA journal_mode=WAL")
            _conn.execute("PRAGMA query_only=ON")
        except Exception:
            pass
    return _conn


def query_all(sql, params=()):
    with _lock:
        try:
            cur = get_conn().cursor()
            cur.execute(sql, params)
            return cur.fetchall()
        except Exception as e:
            print(f"⚠️ DB query error: {e}")
            return []


def query_one(sql, params=()):
    rows = query_all(sql, params)
    return rows[0] if rows else None


# ═══════════════════════════════════════════════════════════════════
# ─── HIGH LEVEL QUERIES
# ═══════════════════════════════════════════════════════════════════
def get_user_economy(guild_id: int, user_id: int) -> dict:
    row = query_one(
        "SELECT data FROM economy WHERE guild_id=? AND user_id=?",
        (guild_id, user_id),
    )
    if not row:
        return {"balance": 0, "bank": 0}
    try:
        return json.loads(row["data"])
    except Exception:
        return {"balance": 0, "bank": 0}


def get_user_levels(guild_id: int, user_id: int) -> dict:
    row = query_one(
        "SELECT data FROM levels WHERE guild_id=? AND user_id=?",
        (guild_id, user_id),
    )
    if not row:
        return {"xp": 0, "level": 0, "messages": 0}
    try:
        return json.loads(row["data"])
    except Exception:
        return {"xp": 0, "level": 0, "messages": 0}


def get_user_bir(guild_id: int, user_id: int) -> int:
    row = query_one(
        "SELECT data FROM bir WHERE guild_id=? AND user_id=?",
        (guild_id, user_id),
    )
    if not row:
        return 0
    try:
        return json.loads(row["data"]).get("bir", 0)
    except Exception:
        return 0


def get_leaderboard_money(guild_id: int, limit: int = 10) -> list:
    rows = query_all(
        "SELECT user_id, data FROM economy WHERE guild_id=?",
        (guild_id,),
    )
    users = []
    for r in rows:
        try:
            d = json.loads(r["data"])
            total = d.get("balance", 0) + d.get("bank", 0)
            users.append({"user_id": r["user_id"], "total": total})
        except Exception:
            continue
    users.sort(key=lambda x: x["total"], reverse=True)
    return users[:limit]


def get_leaderboard_levels(guild_id: int, limit: int = 10) -> list:
    rows = query_all(
        "SELECT user_id, data FROM levels WHERE guild_id=?",
        (guild_id,),
    )
    users = []
    for r in rows:
        try:
            d = json.loads(r["data"])
            users.append({
                "user_id": r["user_id"],
                "level": d.get("level", 0),
                "xp": d.get("xp", 0),
            })
        except Exception:
            continue
    users.sort(key=lambda x: (x["level"], x["xp"]), reverse=True)
    return users[:limit]


def get_guild_stats(guild_id: int) -> dict:
    eco = query_one("SELECT COUNT(*) as c FROM economy WHERE guild_id=?", (guild_id,))
    lv = query_one("SELECT COUNT(*) as c FROM levels WHERE guild_id=?", (guild_id,))
    warn = query_one("SELECT COUNT(*) as c FROM warnings WHERE guild_id=?", (guild_id,))
    return {
        "economy_users": eco["c"] if eco else 0,
        "level_users": lv["c"] if lv else 0,
        "warned_users": warn["c"] if warn else 0,
    }


def get_all_guilds_with_data() -> list:
    rows = query_all("SELECT DISTINCT guild_id FROM economy UNION SELECT DISTINCT guild_id FROM levels")
    return [r["guild_id"] for r in rows]


def get_warnings(guild_id: int, user_id: int) -> list:
    row = query_one(
        "SELECT data FROM warnings WHERE guild_id=? AND user_id=?",
        (guild_id, user_id),
    )
    if not row:
        return []
    try:
        return json.loads(row["data"])
    except Exception:
        return []