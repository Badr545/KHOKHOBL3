# database/store.py
# =====================================================================
# ─── STORE — dict-like wrapper li kaypersist f SQLite
# =====================================================================
import json
from database.engine import execute, executemany, query_all, commit


class SqliteStore(dict):
    """
    Drop-in replacement for `dict[int, dict[int, <data>]]`.

    • Lazy loads guild b guild mn SQLite.
    • Kol access kaymarki guild dirty.
    • `.flush()` kay-diff w kay-write ghir li tbeddel.

    Example (cog code stays same):
        ECONOMY.setdefault(gid, {}).setdefault(uid, {"balance": 0})
        ECONOMY[gid][uid]["balance"] += 100
        save_economy()   # → ECONOMY.flush()
    """

    def __init__(self, table: str):
        super().__init__()
        self._table = table
        self._loaded: set[int] = set()
        self._dirty: set[int] = set()
        self._snapshot: dict[int, dict[int, str]] = {}  # gid → {uid: json}

    # ═══════════════════════════════════════════════════════════
    # ─── LOADING
    # ═══════════════════════════════════════════════════════════
    def _ensure_loaded(self, gid: int):
        if gid in self._loaded:
            return
        users = {}
        snap = {}
        rows = query_all(
            f"SELECT user_id, data FROM {self._table} WHERE guild_id = ?",
            (gid,),
        )
        for row in rows:
            uid = row["user_id"]
            raw = row["data"]
            try:
                users[uid] = json.loads(raw)
            except Exception:
                users[uid] = {}
            snap[uid] = raw
        dict.__setitem__(self, gid, users)
        self._snapshot[gid] = snap
        self._loaded.add(gid)

    def _load_all_guild_ids(self):
        rows = query_all(f"SELECT DISTINCT guild_id FROM {self._table}")
        for row in rows:
            self._ensure_loaded(row["guild_id"])

    # ═══════════════════════════════════════════════════════════
    # ─── DICT-LIKE ACCESS
    # ═══════════════════════════════════════════════════════════
    def __getitem__(self, gid):
        self._ensure_loaded(gid)
        self._dirty.add(gid)
        return dict.__getitem__(self, gid)

    def get(self, gid, default=None):
        try:
            self._ensure_loaded(gid)
        except Exception:
            return default
        if not dict.__contains__(self, gid):
            return default
        self._dirty.add(gid)
        return dict.__getitem__(self, gid)

    def setdefault(self, gid, default=None):
        self._ensure_loaded(gid)
        self._dirty.add(gid)
        if not dict.__contains__(self, gid):
            dict.__setitem__(self, gid, {})
        return dict.__getitem__(self, gid)

    def __contains__(self, gid):
        self._ensure_loaded(gid)
        return dict.__contains__(self, gid)

    def __setitem__(self, gid, value):
        self._loaded.add(gid)
        self._dirty.add(gid)
        dict.__setitem__(self, gid, value)

    def __delitem__(self, gid):
        self._dirty.add(gid)
        try:
            dict.__delitem__(self, gid)
        except KeyError:
            pass

    def keys(self):
        self._load_all_guild_ids()
        return dict.keys(self)

    def values(self):
        self._load_all_guild_ids()
        return dict.values(self)

    def items(self):
        self._load_all_guild_ids()
        return dict.items(self)

    def __iter__(self):
        self._load_all_guild_ids()
        return dict.__iter__(self)

    def __len__(self):
        self._load_all_guild_ids()
        return dict.__len__(self)

    # ═══════════════════════════════════════════════════════════
    # ─── PERSISTENCE
    # ═══════════════════════════════════════════════════════════
    def mark_dirty(self, gid: int | None = None):
        if gid is None:
            self._dirty.update(self._loaded)
        else:
            self._dirty.add(gid)

    def has_dirty(self) -> bool:
        return bool(self._dirty)

    def flush(self) -> int:
        """Diff w write ghir li tbeddel. Rje3 3adad rows written."""
        if not self._dirty:
            return 0

        dirty_gids = list(self._dirty)
        self._dirty.clear()
        total = 0

        for gid in dirty_gids:
            if not dict.__contains__(self, gid):
                continue
            guild_data = dict.__getitem__(self, gid)
            snap = self._snapshot.setdefault(gid, {})
            to_upsert = []

            for uid, data in guild_data.items():
                try:
                    new_json = json.dumps(
                        data, sort_keys=True, ensure_ascii=False, default=str,
                    )
                except Exception:
                    continue
                if snap.get(uid) != new_json:
                    to_upsert.append((gid, uid, new_json))
                    snap[uid] = new_json

            # ─── Deleted users
            removed = [uid for uid in snap if uid not in guild_data]
            for uid in removed:
                execute(
                    f"DELETE FROM {self._table} WHERE guild_id=? AND user_id=?",
                    (gid, uid),
                )
                del snap[uid]

            if to_upsert:
                executemany(
                    f"INSERT INTO {self._table} (guild_id, user_id, data) "
                    f"VALUES (?, ?, ?) "
                    f"ON CONFLICT(guild_id, user_id) DO UPDATE SET data=excluded.data",
                    to_upsert,
                )
                total += len(to_upsert)

        commit()
        return total

    # ═══════════════════════════════════════════════════════════
    # ─── UTIL
    # ═══════════════════════════════════════════════════════════
    def bulk_load_all(self):
        """Load kolchi f memory (l leaderboards globales)."""
        self._load_all_guild_ids()

    def stats(self) -> dict:
        row = execute(
            f"SELECT COUNT(*) as cnt, "
            f"COUNT(DISTINCT guild_id) as guilds "
            f"FROM {self._table}"
        ).fetchone()
        return {
            "rows": row["cnt"] if row else 0,
            "guilds": row["guilds"] if row else 0,
            "in_memory_guilds": len(self._loaded),
            "dirty_guilds": len(self._dirty),
        }


# ═══════════════════════════════════════════════════════════════════
# ─── KV STORE (l market w 7wayj sghira)
# ═══════════════════════════════════════════════════════════════════
class KVStore:
    """Simple key→value JSON store (l data li machi per-user)."""

    def __init__(self, key: str, default: dict | None = None):
        self._key = key
        self._default = default or {}
        self._data: dict | None = None
        self._dirty = False

    def _load(self):
        if self._data is not None:
            return
        row = execute("SELECT value FROM kv WHERE key=?", (self._key,)).fetchone()
        if row:
            try:
                self._data = json.loads(row["value"])
            except Exception:
                self._data = dict(self._default)
        else:
            self._data = dict(self._default)

    def __getitem__(self, k):
        self._load()
        return self._data[k]

    def __setitem__(self, k, v):
        self._load()
        self._data[k] = v
        self._dirty = True

    def __contains__(self, k):
        self._load()
        return k in self._data

    def __delitem__(self, k):
        self._load()
        del self._data[k]
        self._dirty = True

    def get(self, k, default=None):
        self._load()
        return self._data.get(k, default)

    def setdefault(self, k, default):
        self._load()
        if k not in self._data:
            self._data[k] = default
            self._dirty = True
        return self._data[k]

    def keys(self):
        self._load()
        return self._data.keys()

    def values(self):
        self._load()
        return self._data.values()

    def items(self):
        self._load()
        return self._data.items()

    def __iter__(self):
        self._load()
        return iter(self._data)

    def __len__(self):
        self._load()
        return len(self._data)

    def mark_dirty(self):
        self._dirty = True

    def flush(self) -> bool:
        if not self._dirty:
            return False
        self._load()
        value = json.dumps(self._data, ensure_ascii=False, default=str)
        execute(
            "INSERT INTO kv(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (self._key, value),
        )
        commit()
        self._dirty = False
        return True