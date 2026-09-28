# database/migrate.py
# =====================================================================
# ─── MIGRATION — JSON files → SQLite (one-time, safe)
# =====================================================================
import json
import os
import shutil
from datetime import datetime

from database.engine import executemany, query_one, commit
from database.schema import init_schema, get_meta, set_meta


# Mapping: json file → sqlite table
MIGRATIONS = [
    ("data/economy.json",  "economy"),
    ("data/levels.json",   "levels"),
    ("data/bir.json",      "bir"),
    ("data/warnings.json", "warnings"),
    ("data/banking.json",  "banking"),
]


def _backup_dir() -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = f"data/json_backup_{ts}"
    os.makedirs(path, exist_ok=True)
    return path


def migrate_json_to_table(json_path: str, table: str, backup_dir: str) -> int:
    """Migrate had JSON l table. Rje3 3adad rows."""
    if not os.path.exists(json_path):
        return 0

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        print(f"⚠️  Migration {json_path} read failed: {e}")
        return 0

    rows = []
    for gid_str, users in raw.items():
        try:
            gid = int(gid_str)
        except Exception:
            continue
        if not isinstance(users, dict):
            continue
        for uid_str, data in users.items():
            try:
                uid = int(uid_str)
            except Exception:
                continue
            try:
                data_json = json.dumps(data, ensure_ascii=False, default=str)
            except Exception:
                continue
            rows.append((gid, uid, data_json))

    if rows:
        executemany(
            f"INSERT INTO {table} (guild_id, user_id, data) VALUES (?, ?, ?) "
            f"ON CONFLICT(guild_id, user_id) DO UPDATE SET data=excluded.data",
            rows,
        )
        commit()

    # ─── Backup original
    try:
        base = os.path.basename(json_path)
        shutil.copy2(json_path, os.path.join(backup_dir, base))
    except Exception:
        pass

    print(f"✅ Migrated {len(rows):,} rows: {json_path} → {table}")
    return len(rows)


def migrate_all(force: bool = False) -> dict:
    """
    Migrate kol JSON files l SQLite.
    force=True → 3awed migrate hta ila deja m-done.
    """
    init_schema()

    if get_meta("migration_done") and not force:
        return {"skipped": True}

    backup_dir = _backup_dir()
    print(f"📦 Backup dir: {backup_dir}")

    result = {}
    total = 0
    for json_path, table in MIGRATIONS:
        # Skip ila table 3mer
        row = query_one(f"SELECT COUNT(*) as c FROM {table}")
        if row and row["c"] > 0 and not force:
            result[table] = {"skipped": True, "existing": row["c"]}
            continue
        count = migrate_json_to_table(json_path, table, backup_dir)
        result[table] = count
        total += count

    set_meta("migration_done", "1")
    set_meta("migration_at", datetime.now().isoformat())
    set_meta("migration_total_rows", str(total))
    result["total"] = total
    result["backup_dir"] = backup_dir
    print(f"🎉 Migration complete: {total:,} total rows")
    return result


def auto_migrate_if_needed():
    """Auto-run migration ila DB khawya w JSON files kaynin."""
    init_schema()

    if get_meta("migration_done"):
        return {"already_done": True}

    # Hekk DB khawya?
    row = query_one("SELECT COUNT(*) as c FROM economy")
    if row and row["c"] > 0:
        set_meta("migration_done", "1")
        return {"already_done": True}

    # Hekk kaynin JSON files?
    has_json = any(os.path.exists(p) for p, _ in MIGRATIONS)
    if not has_json:
        set_meta("migration_done", "1")
        return {"no_json": True}

    print("📥 Auto-migrating JSON → SQLite...")
    return migrate_all()