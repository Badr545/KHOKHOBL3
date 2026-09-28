# =====================================================================
# ─── KHOKHO BL3 BOT — CONFIG
# =====================================================================
import discord

# ═══════════════════════════════════════════════════════════════════
# ─── WELCOME
# ═══════════════════════════════════════════════════════════════════
WELCOME_CHANNEL_NAME = "𝑾𝒆𝒍𝒄𝒐𝒎"
VERIFIED_ROLE_NAME = "Verified ✓"
LEAVES_CHANNEL_NAME = "leaves"
AUTO_ROLE_ENABLED = True
WELCOME_DM_ENABLED = True


# ═══════════════════════════════════════════════════════════════════
# ─── VOICE 24/7
# ═══════════════════════════════════════════════════════════════════
VOICE_CHANNEL_ID = 1522640260440522793


# ═══════════════════════════════════════════════════════════════════
# ─── LOGS
# ═══════════════════════════════════════════════════════════════════
LOG_CHANNEL_NAME = "logs"


# ═══════════════════════════════════════════════════════════════════
# ─── GAMBLING
# ═══════════════════════════════════════════════════════════════════
CASINO_CHANNEL_ID = None   # ← ID dyal casino channel (wla None)
CASINO_CATEGORY_KEYWORDS = ["casino", "🎰", "🎲", "bet", "gamble", "grow casino"]


# ═══════════════════════════════════════════════════════════════════
# ─── ROLE-BASED PERMISSIONS
# ═══════════════════════════════════════════════════════════════════
ADMIN_ROLES = [
    "⚜️ Community Manager",
    "🛡️ Administrator",
    "🐦‍🔥 𝓕𝓸𝓾𝓷𝓭𝓮𝓻",
]

MODERATOR_ROLES = [
    "🔨  Moderator",
    "Mod",
    "Staff",
]

HELPER_ROLES = [
    "Helper",
    "Support",
]

BYPASS_ROLES = ADMIN_ROLES + ["🐦‍🔥 𝓕𝓸𝓾𝓷𝓭𝓮𝓻"]

ANNOUNCER_ROLES = HELPER_ROLES + MODERATOR_ROLES + ADMIN_ROLES

# ═══════════════════════════════════════════════════════════════════
# ─── COMMAND CATEGORIES → ROLE MAPPING
# ═══════════════════════════════════════════════════════════════════
COMMAND_PERMISSIONS = {
    "moderation": {
        "roles": MODERATOR_ROLES + ADMIN_ROLES,
        "commands": [
            "kick", "ban", "warn", "warnings", "ms7", "slowmode", "lock", "unlock",
            "clearwarns", "giverole", "removerole",
        ],
    },
    "admin_only": {
        "roles": ADMIN_ROLES,
        "commands": [
            "reload", "shutdown", "eval", "config",
            "addmod", "removemod", "listroles", "checkperm",
            "massrole",
        ],
    },
    "announcement": {
        "roles": HELPER_ROLES + MODERATOR_ROLES + ADMIN_ROLES,
        "commands": ["announce", "embed"],
    },
    "public": {
        "roles": [],
        "commands": [
            # ─── BASIC
            "ping", "say", "userinfo", "serverinfo", "avatar", "help", "cmds",
            # ─── INFO
            "anime", "manga", "weather", "translate", "lyrics",
            "banner", "roles", "members", "bots", "invites",
            # ─── GAMES
            "8ball", "roll", "coinflip", "poll", "trivia", "rps", "dice",
            "guess", "slots",
            # ─── UTILITY
            "math", "base64", "password", "uuid", "timestamp",
            # ─── ECONOMY
            "balance", "coins", "daily", "work", "rob", "pay", "gamble",
            # ─── SHOP
            "shop", "buy",
            # ─── LEVELS / RANK
            "rank", "rankcard", "rcard", "levels", "toprank",
            # ─── LEADERBOARDS
            "topmoney", "lb", "leaderboard",
            # ─── GAMBLING (short)
            "cf", "d", "rl", "s", "bj", "rp",
            # ─── BIR
            "bir", "birwork", "bw", "birtop", "bt",
            # ─── TEMP VOICE
            "ot", "vc",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════
# ─── HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def is_known_command(command_name: str) -> bool:
    """Check wach command mذكour f COMMAND_PERMISSIONS."""
    for category, data in COMMAND_PERMISSIONS.items():
        if command_name in data["commands"]:
            return True
    return False


def get_required_roles(command_name: str) -> list:
    """Rje3 l-lista dyal roles li khass ykoun 3endhom had command."""
    for category, data in COMMAND_PERMISSIONS.items():
        if command_name in data["commands"]:
            return data["roles"]
    return []


def user_has_permission(member, command_name: str) -> bool:
    """Check wach l-member 3endou permission dyal command."""
    if not isinstance(member, discord.Member):
        return False

    if member.guild is None:
        return False

    if member.id == member.guild.owner_id:
        return True

    # ✅ Jbed names + ids
    member_role_names = {r.name for r in member.roles}
    member_role_ids = {r.id for r in member.roles}

    for bypass in BYPASS_ROLES:
        if bypass in member_role_names:
            return True
        rid = ROLE_NAME_TO_ID.get(bypass)
        if rid and rid in member_role_ids:
            return True

    if not is_known_command(command_name):
        return True

    required = get_required_roles(command_name)
    if not required:
        return True

    for role_name in required:
        if role_name in member_role_names:
            return True
        rid = ROLE_NAME_TO_ID.get(role_name)
        if rid and rid in member_role_ids:
            return True

    return False

# ═══════════════════════════════════════════════════════════════════
# ─── ROLE NAME → ID MAP
# ═══════════════════════════════════════════════════════════════════
ROLE_NAME_TO_ID: dict[str, int] = {}