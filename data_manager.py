# data_manager.py — SQLite backend + JSON fallback for MARKET
# ═══════════════════════════════════════════════════════════════════
# ─── CENTRAL DATA MANAGER — SQLite powered
# ═══════════════════════════════════════════════════════════════════
import json
import os
import atexit
import threading
import time

from database import (
    init_schema,
    auto_migrate_if_needed,
    SqliteStore,
    KVStore,
    query_all, query_one, execute, commit, close as db_close,
)


# ═══════════════════════════════════════════════════════════════════
# ─── INIT SCHEMA + MIGRATION
# ═══════════════════════════════════════════════════════════════════
init_schema()
mig_result = auto_migrate_if_needed()


# ═══════════════════════════════════════════════════════════════════
# ─── STORES (SQLite)
# ═══════════════════════════════════════════════════════════════════
ECONOMY  = SqliteStore("economy")
LEVELS   = SqliteStore("levels")
BIR      = SqliteStore("bir")
WARNINGS = SqliteStore("warnings")
BANKING  = SqliteStore("banking")


# ═══════════════════════════════════════════════════════════════════
# ─── MARKET (still JSON — tiny data, non per-user)
# ═══════════════════════════════════════════════════════════════════
MARKET_FILE = "data/market.json"


def _load_json_file(path: str, name: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ Loaded {name}: {len(data)} keys")
        return data
    except Exception as e:
        print(f"⚠️  Load {name} failed: {e}")
        return {}


def _save_json_file(path: str, data: dict, name: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  Save {name} failed: {e}")


MARKET: dict = _load_json_file(MARKET_FILE, "market")


# ═══════════════════════════════════════════════════════════════════
# ─── LOAD_ALL (compat — ma kaydir walo daba)
# ═══════════════════════════════════════════════════════════════════
def load_all():
    """Compat: kolchi kaytloada automatiquement daba."""
    return {
        "economy":  ECONOMY.stats(),
        "levels":   LEVELS.stats(),
        "bir":      BIR.stats(),
        "warnings": WARNINGS.stats(),
        "banking":  BANKING.stats(),
    }


# ═══════════════════════════════════════════════════════════════════
# ─── SAVE FUNCTIONS — b debounce (fast + safe)
# ═══════════════════════════════════════════════════════════════════
_flush_last = {}
_flush_lock = threading.Lock()
DEBOUNCE = 1.0  # seconds


def _debounced_flush(store, name: str):
    """Ila 3adaw >1s mn a5er flush → flush daba. Wla → flag l background."""
    now = time.time()
    with _flush_lock:
        last = _flush_last.get(name, 0)
        if now - last < DEBOUNCE:
            store.mark_dirty()
            return
        _flush_last[name] = now
    try:
        store.flush()
    except Exception as e:
        print(f"⚠️  Flush {name} failed: {e}")


def save_economy():
    _debounced_flush(ECONOMY, "economy")


def save_levels():
    _debounced_flush(LEVELS, "levels")


def save_bir():
    _debounced_flush(BIR, "bir")


def save_warnings():
    _debounced_flush(WARNINGS, "warnings")


def save_banking():
    _debounced_flush(BANKING, "banking")


def save_market():
    _save_json_file(MARKET_FILE, MARKET, "market")


# ═══════════════════════════════════════════════════════════════════
# ─── FLUSH ALL (l shutdown)
# ═══════════════════════════════════════════════════════════════════
def flush_all():
    total = 0
    for store, name in [
        (ECONOMY, "economy"),
        (LEVELS, "levels"),
        (BIR, "bir"),
        (WARNINGS, "warnings"),
        (BANKING, "banking"),
    ]:
        try:
            n = store.flush()
            total += n
            if n:
                print(f"💾 Flushed {name}: {n} rows")
        except Exception as e:
            print(f"❌ Flush {name} error: {e}")
    save_market()
    return total


# ═══════════════════════════════════════════════════════════════════
# ─── BACKGROUND FLUSHER (safety net — kol 5s)
# ═══════════════════════════════════════════════════════════════════
def _background_flush_loop():
    while True:
        time.sleep(5)
        try:
            for store, name in [
                (ECONOMY, "economy"),
                (LEVELS, "levels"),
                (BIR, "bir"),
                (WARNINGS, "warnings"),
                (BANKING, "banking"),
            ]:
                if store.has_dirty():
                    store.flush()
        except Exception as e:
            print(f"⚠️  Background flush: {e}")


_flush_thread = threading.Thread(
    target=_background_flush_loop,
    daemon=True,
    name="db-flusher",
)
_flush_thread.start()


# ═══════════════════════════════════════════════════════════════════
# ─── GRACEFUL SHUTDOWN
# ═══════════════════════════════════════════════════════════════════
def _on_exit():
    print("🔻 Shutdown: flushing DB...")
    try:
        flush_all()
    except Exception as e:
        print(f"❌ Exit flush: {e}")
    try:
        db_close()
    except Exception:
        pass


atexit.register(_on_exit)


# ═══════════════════════════════════════════════════════════════════
# ─── STATS (l admin commands)
# ═══════════════════════════════════════════════════════════════════
def get_db_stats() -> dict:
    return {
        "economy":  ECONOMY.stats(),
        "levels":   LEVELS.stats(),
        "bir":      BIR.stats(),
        "warnings": WARNINGS.stats(),
        "banking":  BANKING.stats(),
    }