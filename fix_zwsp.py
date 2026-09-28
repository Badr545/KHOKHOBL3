# fix_zwsp.py — Fix Zero-Width Space characters
import os

ZWSP = "\u200b"      # zero-width space
ZWJ  = "\u200d"      # zero-width joiner
ZWNJ = "\u200c"      # zero-width non-joiner
BOM  = "\ufeff"      # byte order mark
NBSP = "\u00a0"      # non-breaking space

BAD_CHARS = {
    ZWSP: "", ZWJ: "", ZWNJ: "", BOM: "", NBSP: " ",
}

def fix_file(path: str) -> int:
    if not os.path.exists(path):
        print(f"❌ File ma kaynch: {path}")
        return 0
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    original = content
    for bad, good in BAD_CHARS.items():
        content = content.replace(bad, good)
    if content != original:
        # Backup
        with open(path + ".bak", "w", encoding="utf-8") as f:
            f.write(original)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        count = sum(original.count(c) for c in BAD_CHARS)
        print(f"✅ Fixed {path} — {count} bad chars removed (backup: {path}.bak)")
        return count
    print(f"✔️  {path} clean")
    return 0


if __name__ == "__main__":
    files = [
        "cogs/games.py",
        "cogs/basic.py",
        "cogs/economy.py",
        "cogs/gambling.py",
        "cogs/bir.py",
        "cogs/levels.py",
        "cogs/rankcard.py",
        "cogs/leaderboard.py",
        "cogs/shop.py",
        "cogs/secret_admin.py",
        "cogs/banking.py",
        "cogs/achievements.py",
        "cogs/moregames.py",
        "cogs/premium.py",
        "cogs/antiraid.py",
    ]
    total = 0
    for f in files:
        total += fix_file(f)
    print(f"\n🎉 Total: {total} bad characters removed.")