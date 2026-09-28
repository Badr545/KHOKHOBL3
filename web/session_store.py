# web/session_store.py
# =====================================================================
# ─── SESSION STORE — in-memory cache l guilds (bach cookie yb9a sghir)
# =====================================================================
import threading
import time

_lock = threading.RLock()
_store: dict = {}

TTL = 3600  # 1 hour


def set(key: str, value, ttl: int = TTL):
    with _lock:
        _store[key] = {"value": value, "expires": time.time() + ttl}


def get(key: str, default=None):
    with _lock:
        item = _store.get(key)
        if not item:
            return default
        if time.time() > item["expires"]:
            _store.pop(key, None)
            return default
        return item["value"]


def delete(key: str):
    with _lock:
        _store.pop(key, None)


def cleanup():
    now = time.time()
    with _lock:
        expired = [k for k, v in _store.items() if now > v["expires"]]
        for k in expired:
            _store.pop(k, None)
    return len(expired)