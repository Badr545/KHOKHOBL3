# cogs/backup_restore.py
# =====================================================================
# ─── BACKUP / RESTORE — JSON files auto-backup
# =====================================================================
import discord
from discord.ext import commands, tasks
import os
import shutil
from datetime import datetime

BACKUP_DIR = "data/backups"
DATA_FILES = ["economy.json", "levels.json", "bir.json", "warnings.json",
              "automod.json", "tickets.json", "tempbans.json", "giveaways.json",
              "reactionroles.json", "customcommands.json"]
MAX_BACKUPS = 10


class BackupRestore(commands.Cog):
    """Backup system"""

    def __init__(self, bot):
        self.bot = bot
        self.auto_backup.start()

    def cog_unload(self):
        self.auto_backup.cancel()

    def make_backup(self) -> str | None:
        # Fix: Handle FileExistsError gracefully
        try:
            if not os.path.exists(BACKUP_DIR):
                os.makedirs(BACKUP_DIR, exist_ok=True)
            elif not os.path.isdir(BACKUP_DIR):
                # If it exists but is a file, rename it and create directory
                os.rename(BACKUP_DIR, BACKUP_DIR + ".bak")
                os.makedirs(BACKUP_DIR, exist_ok=True)
        except Exception as e:
            print(f"❌ Backup dir error: {e}")
            return None

        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        folder = os.path.join(BACKUP_DIR, ts)
        os.makedirs(folder, exist_ok=True)

        count = 0
        for f in DATA_FILES:
            src = os.path.join("data", f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(folder, f))
                count += 1

        if count == 0:
            try:
                os.rmdir(folder)
            except Exception:
                pass
            return None

        # Cleanup l-9dam
        backups = sorted(os.listdir(BACKUP_DIR))
        while len(backups) > MAX_BACKUPS:
            old = backups.pop(0)
            shutil.rmtree(os.path.join(BACKUP_DIR, old), ignore_errors=True)

        return folder

    def list_backups(self) -> list[str]:
        if not os.path.exists(BACKUP_DIR):
            return []
        return sorted(os.listdir(BACKUP_DIR), reverse=True)

    def restore(self, backup_name: str) -> tuple[int, int]:
        folder = os.path.join(BACKUP_DIR, backup_name)
        if not os.path.isdir(folder):
            return 0, 0
        ok, fail = 0, 0
        for f in DATA_FILES:
            src = os.path.join(folder, f)
            if os.path.exists(src):
                try:
                    shutil.copy2(src, os.path.join("data", f))
                    ok += 1
                except Exception:
                    fail += 1
        return ok, fail

    @tasks.loop(hours=1)
    async def auto_backup(self):
        self.make_backup()

    @auto_backup.before_loop
    async def before(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(BackupRestore(bot))