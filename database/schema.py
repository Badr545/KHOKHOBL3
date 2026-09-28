# database/schema.py
# =====================================================================
# ─── SQLITE SCHEMA — tables + indexes + meta helpers
# =====================================================================
from database.engine import execute, commit


SCHEMA_SQL = [
    # ─── ECONOMY
    """
    CREATE TABLE IF NOT EXISTS economy (
        guild_id INTEGER NOT NULL,
        user_id  INTEGER NOT NULL,
        data     TEXT    NOT NULL DEFAULT '{}',
        PRIMARY KEY (guild_id, user_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_economy_guild ON economy(guild_id)",

    # ─── LEVELS
    """
    CREATE TABLE IF NOT EXISTS levels (
        guild_id INTEGER NOT NULL,
        user_id  INTEGER NOT NULL,
        data     TEXT    NOT NULL DEFAULT '{}',
        PRIMARY KEY (guild_id, user_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_levels_guild ON levels(guild_id)",

    # ─── BIR
    """
    CREATE TABLE IF NOT EXISTS bir (
        guild_id INTEGER NOT NULL,
        user_id  INTEGER NOT NULL,
        data     TEXT    NOT NULL DEFAULT '{}',
        PRIMARY KEY (guild_id, user_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_bir_guild ON bir(guild_id)",

    # ─── WARNINGS
    """
    CREATE TABLE IF NOT EXISTS warnings (
        guild_id INTEGER NOT NULL,
        user_id  INTEGER NOT NULL,
        data     TEXT    NOT NULL DEFAULT '[]',
        PRIMARY KEY (guild_id, user_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_warnings_guild ON warnings(guild_id)",

    # ─── BANKING
    """
    CREATE TABLE IF NOT EXISTS banking (
        guild_id INTEGER NOT NULL,
        user_id  INTEGER NOT NULL,
        data     TEXT    NOT NULL DEFAULT '{}',
        PRIMARY KEY (guild_id, user_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_banking_guild ON banking(guild_id)",

    # ─── KV (misc blobs like market)
    """
    CREATE TABLE IF NOT EXISTS kv (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,

    # ─── MIGRATION META
    """
    CREATE TABLE IF NOT EXISTS meta (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
]


def init_schema():
    """Sayeb kol tables + indexes ila makayninx."""
    for sql in SCHEMA_SQL:
        execute(sql)
    commit()


def get_meta(key: str, default: str | None = None) -> str | None:
    row = execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_meta(key: str, value: str):
    execute(
        "INSERT INTO meta(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    commit()