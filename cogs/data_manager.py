# data_manager.py — F ROOT (machi f cogs/)
# ═══════════════════════════════════════════════════════════════════
# ─── CENTRAL DATA MANAGER — kolchi f blasa wa7da
# ═══════════════════════════════════════════════════════════════════
import json
import os


# ═══════════════════════════════════════════════════════════════════
# ─── DATA
# ═══════════════════════════════════════════════════════════════════
ECONOMY: dict = {}
LEVELS: dict = {}
BIR: dict = {}
WARNINGS: dict = {}


# ═══════════════════════════════════════════════════════════════════
# ─── LOAD
# ═══════════════════════════════════════════════════════════════════
def _load_json(path: str, name: str) -> dict:
    if not os.path.exists(path):
        print(f"ℹ️ {name}: ma kaynch file — kbda b khawi")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        data = {
            int(g): {int(u): d for u, d in users.items()}
            for g, users in raw.items()
        }
        print(f"✅ Loaded {name}: {len(data)} guilds")
        return data
    except Exception as e:
        print(f"⚠️ Load {name} failed: {e}")
        return {}


def load_all():
    global ECONOMY, LEVELS, BIR, WARNINGS
    ECONOMY  = _load_json("data/economy.json",  "economy")
    LEVELS   = _load_json("data/levels.json",   "levels")
    BIR      = _load_json("data/bir.json",      "bir")
    WARNINGS = _load_json("data/warnings.json", "warnings")


# ═══════════════════════════════════════════════════════════════════
# ─── SAVE
# ═══════════════════════════════════════════════════════════════════
def _save_json(path: str, data: dict, name: str):
    os.makedirs("data", exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Save {name} failed: {e}")


def save_economy():
    _save_json("data/economy.json", ECONOMY, "economy")


def save_levels():
    _save_json("data/levels.json", LEVELS, "levels")


def save_bir():
    _save_json("data/bir.json", BIR, "bir")


def save_warnings():
    _save_json("data/warnings.json", WARNINGS, "warnings")


# ═══════════════════════════════════════════════════════════════════
# ─── AUTO LOAD ON IMPORT
# ═══════════════════════════════════════════════════════════════════
load_all()