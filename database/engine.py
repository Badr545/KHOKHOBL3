# database/engine.py
# =====================================================================
# ─── SQLITE ENGINE — thread-safe connection + WAL mode
# =====================================================================
import os
import sqlite3
import threading

DB_PATH = os.getenv("DB_PATH", "data/bot.db")

_lock = threading.RLock()
_conn: sqlite3.Connection | None = None


def get_conn() -> sqlite3.Connection:
    """Rje3 (wla sayeb) connection singleton."""
    global _conn
    if _conn is None:
        # Create folder
        folder = os.path.dirname(DB_PATH)
        if folder:
            os.makedirs(folder, exist_ok=True)

        _conn = sqlite3.connect(
            DB_PATH,
            check_same_thread=False,
            timeout=30.0,
            isolation_level=None,  # autocommit, we handle transactions manually
        )
        _conn.row_factory = sqlite3.Row
        # WAL = better concurrency + durability
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA synchronous=NORMAL")
        _conn.execute("PRAGMA foreign_keys=ON")
        _conn.execute("PRAGMA temp_store=MEMORY")
        _conn.execute("PRAGMA cache_size=-64000")  # 64 MB
        print(f"✅ SQLite opened: {DB_PATH}")
    return _conn


def execute(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    with _lock:
        cur = get_conn().cursor()
        cur.execute(sql, params)
        return cur


def executemany(sql: str, params) -> sqlite3.Cursor:
    with _lock:
        cur = get_conn().cursor()
        cur.executemany(sql, params)
        return cur


def query_one(sql: str, params: tuple = ()):
    with _lock:
        cur = get_conn().cursor()
        cur.execute(sql, params)
        return cur.fetchone()


def query_all(sql: str, params: tuple = ()):
    with _lock:
        cur = get_conn().cursor()
        cur.execute(sql, params)
        return cur.fetchall()


def commit():
    with _lock:
        get_conn().commit()


def close():
    global _conn
    with _lock:
        if _conn is not None:
            try:
                _conn.commit()
            except Exception:
                pass
            try:
                _conn.close()
            except Exception:
                pass
            _conn = None
            print("🔒 SQLite closed.")