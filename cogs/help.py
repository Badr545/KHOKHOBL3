# cogs/help.py
# =====================================================================
# ─── HELP SYSTEM — &help (public) + +help (staff only)
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
from botconfig import (
    user_has_permission, is_known_command,
    ADMIN_ROLES, MODERATOR_ROLES, ROLE_NAME_TO_ID,
)


# ═══════════════════════════════════════════════════════════════════
# ─── HELP CATEGORIES
# ═══════════════════════════════════════════════════════════════════
HELP_CATEGORIES = {
    # ═══════════════ PUBLIC CATEGORIES ═══════════════
    "🏠 Home": {
        "description": "L-basics — bda mn hna",
        "commands": [
            ("help",       "Affichi had l-menu",                     "/help",                     "public"),
            ("cmds",       "Menu b prefix",                          "&help",                     "public"),
            ("ping",       "Latency dyal l-bot",                     "/ping",                     "public"),
            ("serverinfo", "Ma3loumat 3la l-server",                 "/serverinfo",               "public"),
            ("userinfo",   "Ma3loumat 3la user",                     "/userinfo [@user]",         "public"),
            ("avatar",     "Avatar dyal user",                       "/avatar [@user]",           "public"),
            ("banner",     "Banner dyal user",                       "/banner [@user]",           "public"),
        ],
    },
    "🎮 Games": {
        "description": "Al3ab w tfasli7",
        "commands": [
            ("8ball",     "S'el chi soual",                         "/8ball <question>",         "public"),
            ("roll",      "Rmi dice",                               "/roll [sides]",             "public"),
            ("coinflip",  "Rmi coin (pile wla face)",               "/coinflip",                 "public"),
            ("dice",      "Zhar b emojis",                          "/dice [count]",             "public"),
            ("slots",     "Makanat l-haz (bla flous)",              "/slots",                    "public"),
            ("rps",       "Rock Paper Scissors",                    "/rps <choice>",             "public"),
            ("trivia",    "Soual culture",                          "/trivia",                   "public"),
            ("guess",     "Khamen ra9m",                            "&guess",                    "public"),
            ("poll",      "Sondage",                                "/poll <question>",          "public"),
            ("ttt",       "🎮 Tic-Tac-Toe (b bet)",                 "&ttt @user [bet]",          "public"),
            ("c4",        "🔴 Connect 4 (b bet)",                   "&c4 @user [bet]",           "public"),
            ("wordle",    "🎯 Wordle (b bet)",                      "&wordle [bet]",             "public"),
        ],
    },
    "🎯 Game Requests": {
        "description": "3ayet l-gamers — ping role dyal game",
        "commands": [
            ("ff",         "Invite Free Fire players",     "&ff",         "public"),
            ("pes",        "Invite PES players",           "&pes",        "public"),
            ("valo",       "Invite Valorant players",      "&valo",       "public"),
            ("roblox",     "Invite Roblox players",        "&roblox",     "public"),
            ("listgames",  "Chouf games configurés",       "&listgames",  "public"),
            ("setgame",    "[Staff] Setup game request",   "+setgame <cmd> @role", "admin_only"),
            ("delgame",    "[Staff] Hyed game request",    "+delgame <cmd>",       "admin_only"),
        ],
    },
    "💰 Economy": {
        "description": "Nizam l-flous (Coins)",
        "commands": [
            ("balance",     "Chouf l-balance",                      "/balance [@user]",          "public"),
            ("coins",       "Chouf l-balance (+coins)",             "&coins [@user]",            "public"),
            ("daily",       "Rati yawmi",                           "/daily",                    "public"),
            ("work",        "Khdm w jib flous (10s)",               "/work",                     "public"),
            ("rob",         "Srq chi wa7ed",                        "/rob @user",                "public"),
            ("pay",         "Sift flous l chi wa7ed",               "/pay @user <amount>",       "public"),
            ("gamble",      "Qamr flousek",                         "/gamble <amount>",          "public"),
            ("collect",     "Jme3 income mn roles (30min)",         "/collect",                  "public"),
        ],
    },
    "🏦 Banking": {
        "description": "Banking kamel — Loans / Businesses / Stocks / Crypto",
        "commands": [
            ("bank",         "🏦 Dashboard dyal bank",              "/bank [@user]",             "public"),
            ("loan",         "💰 Khoud loan",                        "/loan take <amt>",          "public"),
            ("business",     "🏢 Businesses (buy/collect/upgrade)", "/business list",            "public"),
            ("stocks",       "📈 Stock market",                      "/stocks list",              "public"),
            ("crypto",       "🪙 Crypto market",                     "/crypto list",              "public"),
            ("savings",      "💎 Savings account",                   "/savings info",             "public"),
            ("interest",     "💰 Jme3 interest",                     "/interest",                 "public"),
            ("transactions", "📜 History",                           "/transactions",             "public"),
            ("auction",      "🔨 Auction",                           "/auction <item> <start> <min>","public"),
            ("pool",         "🎲 Betting pool",                      "/pool <q> <opts>",          "public"),
        ],
    },
    "🔮 Bir": {
        "description": "العملة الثانية — non-transferable",
        "commands": [
            ("bir",     "Chouf l-Bir dyalk",       "&bir [@user]",   "public"),
            ("birwork", "Khdm bash tjib Bir",      "&bw",            "public"),
            ("birtop",  "Top 10 Bir",              "&bt",            "public"),
        ],
    },
    "🎖️ Rank & Levels": {
        "description": "Nizam l-levels w XP",
        "commands": [
            ("rankcard", "Rank Card dyalk",   "/rankcard [@user]",   "public"),
            ("rcard",    "Rank Card (prefix)", "&rcard [@user]",      "public"),
            ("rank",     "Rank (info)",       "/rank [@user]",       "public"),
            ("levels",   "Top 10 levels",     "/levels",             "public"),
            ("toprank",  "Top 10 rank",       "/toprank",            "public"),
        ],
    },
    "🏆 Achievements": {
        "description": "Achievements + Badges",
        "commands": [
            ("profile",      "🏆 Profile b badges",    "/profile [@user]",       "public"),
            ("achievements", "📋 List dyal achievements","/achievements [@user]",  "public"),
            ("topbadges",    "🏅 Top 10 badges",       "/topbadges",             "public"),
        ],
    },
    "🎲 Gambling": {
        "description": "Kasino dyal bot — ghir f Casino channels 🎰",
        "commands": [
            ("cf",     "🪙 Coinflip (50/50)",                    "&cf <amount> <pile|face>",         "public"),
            ("d",      "🎲 Dice (5x)",                            "&d <amount> <1-6>",                "public"),
            ("rl",     "🔴 Roulette (2x / 14x)",                  "&rl <amount> <red|black|green>",   "public"),
            ("rp",     "🔴 Roulette (alias)",                     "&rp <amount> <color>",             "public"),
            ("s",      "🎰 Slots (10x max)",                      "&s <amount>",                      "public"),
            ("bj",     "🃏 Blackjack (Hit / Stand / Double)",    "&bj <amount>",                     "public"),
            ("hl",     "📈 High-Low (Higher / Lower)",            "&hl <amount>",                     "public"),
            ("mines",  "💣 Mines (5x5 grid)",                     "&mines <amount> [bombs]",          "public"),
            ("crash",  "🚀 Crash (Cash Out 9bel crash)",          "&crash <amount>",                  "public"),
            ("bac",    "🎴 Baccarat (Player / Banker / Tie)",     "&bac <amount>",                    "public"),
            ("poker",  "🃏 Video Poker (Hold / Draw)",            "&poker <amount>",                  "public"),
            ("vp",     "🃏 Video Poker (alias)",                  "&vp <amount>",                     "public"),
            ("tower",  "🗼 Tower (8 floors, 1 mn 3)",             "&tower <amount>",                  "public"),
            ("tw",     "🗼 Tower (alias)",                        "&tw <amount>",                     "public"),
            ("rlt",    "🎡 Roulette Interactive (buttons)",       "&rlt <amount>",                    "public"),
            ("hr",     "🐎 Horse Race (5 horses)",                "&hr <1-5> <amount>",               "public"),
            ("wheel",  "🎡 Wheel of Fortune (10x)",               "&wheel <amount>",                  "public"),
            ("plinko", "🎯 Plinko (low/medium/high)",             "&plinko <amount> [risk]",          "public"),
            ("pl",     "🎯 Plinko (alias)",                       "&pl <amount> [risk]",              "public"),
        ],
    },
    "🛒 Shop": {
        "description": "Chri roles b flousek + income",
        "commands": [
            ("shop",    "Chouf l-shop",    "/shop",           "public"),
            ("buy",     "Chri item",       "/buy <item_key>", "public"),
            ("collect", "Jme3 income",     "/collect",        "public"),
        ],
    },
    "🔥 Streaks & Quests": {
        "description": "Streaks + Daily/Weekly quests",
        "commands": [
            ("claim",       "🔥 Claim streak daily (+bonus)",   "&claim",                    "public"),
            ("streak",      "Chouf streak dyalk",                "&streak [@user]",           "public"),
            ("streaktop",   "Top 10 streaks",                    "&streaktop",                "public"),
            ("quests",      "📋 Daily quests (3 quests)",        "&quests",                   "public"),
            ("questclaim",  "🎁 Claim quest reward",             "&questclaim <id> [type]",   "public"),
            ("questweekly", "📋 Weekly quests (3 quests)",       "&questweekly",              "public"),
        ],
    },
    "📦 Lootbox": {
        "description": "Scratch cards + lootboxes (common → legendary)",
        "commands": [
            ("lootbox",    "M7l lootbox (b tiers)",              "&lootbox <tier>",           "public"),
            ("lootdaily",  "🎁 Free daily lootbox",              "&lootdaily",                "public"),
            ("lootstats",  "Chouf stats dyalek",                 "&lootstats [@user]",        "public"),
        ],
    },
    "🐾 Pets": {
        "description": "Adopt + Feed + Battle pets",
        "commands": [
            ("pets",         "Chouf pets dyalk",                 "&pets [@user]",             "public"),
            ("pets adopt",   "Adopt pet (dog/cat/dragon...)",    "&pets adopt <type> [name]", "public"),
            ("pets feed",    "3ti makan l pet (+income)",        "&pets feed [name]",         "public"),
            ("pets play",    "L3ab m3a pet (+XP)",               "&pets play [name]",         "public"),
            ("pets battle",  "⚔️ Pet vs pet battle",              "&pets battle @user",        "public"),
            ("pets rename",  "Beddel smiya dyal pet",            "&pets rename <old> <new>",  "public"),
            ("pets release", "Khelli pet ymshi",                 "&pets release <name>",      "public"),
        ],
    },
    "⚔️ Adventure": {
        "description": "Dungeon fights + monsters",
        "commands": [
            ("adv",        "Chouf adventure stats",              "&adv",                      "public"),
            ("adv start",  "Bda combat m3a monster",             "&adv start",                "public"),
            ("adv attack", "Hjjem 3la monster",                  "&adv attack",               "public"),
            ("adv flee",   "Hreb mn combat",                     "&adv flee",                 "public"),
            ("adv heal",   "💊 Restore HP (costs 500)",          "&adv heal",                 "public"),
        ],
    },
    "🎭 Roleplay": {
        "description": "Fun roleplay actions b GIFs",
        "commands": [
            ("hug",     "🤗 Hug chi wa7ed",      "/hug @user",     "public"),
            ("kiss",    "💋 Kiss chi wa7ed",     "/kiss @user",    "public"),
            ("slap",    "👋 Slap chi wa7ed",     "/slap @user",    "public"),
            ("pat",     "👐 Pat chi wa7ed",      "/pat @user",     "public"),
            ("cuddle",  "🫂 Cuddle chi wa7ed",   "/cuddle @user",  "public"),
            ("poke",    "👉 Poke chi wa7ed",     "/poke @user",    "public"),
            ("bite",    "🦷 Bite chi wa7ed",     "/bite @user",    "public"),
            ("dance",   "💃 Dance m3a chi wa7ed","/dance @user",   "public"),
            ("tickle",  "🤣 Tickle chi wa7ed",   "/tickle @user",  "public"),
            ("bonk",    "🔨 Bonk chi wa7ed",     "&bonk @user",    "public"),
        ],
    },
    "🔢 Counting": {
        "description": "Counting game f channel",
        "commands": [
            ("counting",         "Info counting",         "&counting",                 "public"),
            ("counting setup",   "Setup counting",         "+counting setup #channel",  "admin_only"),
            ("counting reset",   "Reset count",            "+counting reset",           "admin_only"),
        ],
    },
    "📊 Activity": {
        "description": "Activity tracking (messages + voice)",
        "commands": [
            ("activity",      "Chouf activity dyalek",     "&activity [@user]",           "public"),
            ("activity_top",  "Top active users",          "&activity_top [mode]",        "public"),
        ],
    },
    "🏆 Tournaments": {
        "description": "Tournament system — prize pool",
        "commands": [
            ("tournament",         "List open tournaments",       "&tournament",                          "public"),
            ("tournament create",  "Sayeb tournament",            "&tournament create <game> <entry> <max>","public"),
            ("tournament join",    "Dkhol f tournament",          "&tournament join <id>",                "public"),
            ("tournament start",   "Bda tournament (host only)",  "&tournament start <id>",               "public"),
            ("tournament leave",   "Kherj + refund",              "&tournament leave <id>",               "public"),
        ],
    },
    "🏴‍☠️ Heist": {
        "description": "Team bank robbery (min 3 players)",
        "commands": [
            ("heist",        "Chouf active heist",                "&heist",                    "public"),
            ("heist start",  "Bda heist (min 1,000)",             "&heist start <amount>",     "public"),
            ("heist join",   "Dkhol f heist",                     "&heist join",               "public"),
            ("heist go",     "Bda l-heist (host only)",           "&heist go",                 "public"),
        ],
    },
    "🕵️ Spy": {
        "description": "Chouf info dyal users (b cost)",
        "commands": [
            ("spy",        "Chouf wallet/level (500 🪙)",        "&spy @user",                "public"),
            ("steal-info", "Chouf inventory (2,000 🪙)",         "&steal-info @user",         "public"),
            ("spystats",   "Spy stats dyalek",                    "&spystats [@user]",         "public"),
        ],
    },
    "🎉 Events": {
        "description": "Random server events (Coin rain / Hunt)",
        "commands": [
            ("events", "Info 3la events auto (kola 30min)",      "&events",                   "public"),
        ],
    },
    "🏆 Leaderboards": {
        "description": "Top 10 dyal kolchi",
        "commands": [
            ("lb",        "Top 10 Coins",   "&lb",        "public"),
            ("topmoney",  "Top 10 Coins",   "/topmoney",  "public"),
            ("bt",        "Top 10 Bir",     "&bt",        "public"),
            ("toprank",   "Top 10 Rank",    "/toprank",   "public"),
            ("streaktop", "Top 10 Streaks", "&streaktop","public"),
        ],
    },
    "ℹ️ Info": {
        "description": "Ma3loumat mn l-internet",
        "commands": [
            ("anime",     "Ma3loumat anime",                        "/anime <title>",            "public"),
            ("manga",     "Ma3loumat manga",                        "/manga <title>",            "public"),
            ("weather",   "Weather f chi mdina",                    "/weather <city>",           "public"),
            ("translate", "Traduchi text",                          "/translate <text> <to>",    "public"),
            ("lyrics",    "Lyrics dyal gheniya",                    "/lyrics <artist> <title>",  "public"),
            ("members",   "Statistiques dyal members",              "/members",                  "public"),
            ("bots",      "L-lista dyal bots",                      "/bots",                     "public"),
            ("invites",   "Invitations dyal server",                "/invites",                  "public"),
        ],
    },
    "🎨 Utility": {
        "description": "Adawat mfidin",
        "commands": [
            ("math",      "7sab riyadi",         "/math <expression>",    "public"),
            ("base64",    "Encode/Decode base64","/base64 <text> <mode>", "public"),
            ("password",  "Générer password qwi","/password [length]",    "public"),
            ("uuid",      "Générer UUID",        "/uuid",                 "public"),
            ("timestamp", "Discord timestamp",   "/timestamp <datetime>", "public"),
        ],
    },
    "💎 Premium": {
        "description": "Premium tiers + License",
        "commands": [
            ("premium",        "💎 Status dyal Premium",     "/premium",                 "public"),
            ("premium_redeem", "🎟️ Redeem code",              "/premium_redeem <code>",   "public"),
        ],
    },
    "🎙️ Temp Voice": {
        "description": "Temp Voice — OneTap + Control",
        "commands": [
            ("ot",  "Creeyi temp VC",       "/ot",                "public"),
            ("vc",  "Control VC dyalk",     "&vc <action>",       "public"),
        ],
    },

    # ═══════════════ ADMIN / STAFF CATEGORIES ═══════════════
    "🛠️ Moderation": {
        "description": "Adawat dyal moderation",
        "commands": [
            ("ms7",         "Msa7 messages",              "+ms7 <amount>",             "moderation"),
            ("kick",        "Kherrej user",               "+kick @user [reason]",      "moderation"),
            ("ban",         "Ban user",                   "+ban @user [days] [reason]","moderation"),
            ("warn",        "Warning l member",           "+warn @user [reason]",      "moderation"),
            ("warnings",    "Chouf warnings",             "+warnings @user",           "moderation"),
            ("clearwarns",  "Msa7 warnings",              "+clearwarns @user",         "moderation"),
            ("slowmode",    "Slow mode f channel",        "+slowmode <seconds>",       "moderation"),
            ("lock",        "Qfel channel",               "+lock",                     "moderation"),
            ("unlock",      "Ftah channel",               "+unlock",                   "moderation"),
            ("jail",        "🔒 Sjen member (hyed kolchi roles)", "+jail @user [reason]",  "moderation"),
            ("rta7",        "🔓 7ayed jail (rejje3 roles)",       "+rta7 @user",           "moderation"),
            ("timeout",     "⏱️ Timeout member (1h/30m/1d/7d)",  "+timeout @user <dur>",  "moderation"),
        ],
    },
    "🎭 Roles": {
        "description": "Adawat dyal roles",
        "commands": [
            ("giverole",   "3ti role l member",    "+giverole @user @role",   "moderation"),
            ("removerole", "Hyed role mn member",  "+removerole @user @role", "moderation"),
            ("massrole",   "3ti role l kolchi",    "+massrole @role",         "admin_only"),
        ],
    },
    "🔧 Channels": {
        "description": "Channel manager — create/delete/rename/move/bulk",
        "commands": [
            ("cm",       "Channel manager menu",       "+cm",                              "moderation"),
            ("channel",  "Channel commands",           "+channel create/delete/rename/...", "moderation"),
            ("category", "Category commands",          "+category create/delete/rename",    "moderation"),
        ],
    },
    "🎙️ Voice Admin": {
        "description": "Bot voice control",
        "commands": [
            ("join",      "Bot ydkhol l voice",     "+join",      "admin_only"),
            ("leave",     "Bot ykhrej mn voice",    "+leave",     "admin_only"),
            ("voice247",  "Status dyal voice 24/7", "+voice247",  "admin_only"),
        ],
    },
    "📢 Announcements": {
        "description": "Announcements (Event / Meeting / News)",
        "commands": [
            ("announce", "Styled announcement (3 types)", "+announce <type> <title> ...", "moderation"),
            ("embed",    "Embed custom",                    "+embed <title> <desc>",         "moderation"),
        ],
    },
    "🔒 Staff Only": {
        "description": "Commands ghir l-Staff l-fo9",
        "commands": [
            ("addmod",     "Zid role f Moderators",                 "+addmod @role",          "admin_only"),
            ("removemod",  "Hyed role mn Moderators",               "+removemod @role",       "admin_only"),
            ("listroles",  "Chouf roles configurés",                "+listroles",             "admin_only"),
            ("checkperm",  "Check permission dyal command",         "+checkperm <command>",   "admin_only"),
            ("setserver",  "Auto-create categories/channels/roles", "+setserver confirm",     "admin_only"),
            ("fixroles",   "Fix colors + perms + tartib dyal roles","+fixroles confirm",      "admin_only"),
            ("setcolors",  "Colors only (bla perms/reorder)",       "+setcolors",             "admin_only"),
            ("setperms",   "Permissions only (bla colors)",         "+setperms",              "admin_only"),
            ("rolesinfo",  "Preview dyal role hierarchy",           "+rolesinfo",             "admin_only"),
            ("duproles",   "Chouf roles duplicates (safe)",         "+duproles",              "admin_only"),
            ("cleandroles","Msa7 roles duplicates",                 "+cleandroles confirm",   "admin_only"),
            ("roles",      "L-lista dyal roles (staff)",            "+roles",                 "admin_only"),
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════
# ─── CATEGORY GROUPS
# ═══════════════════════════════════════════════════════════════════
PUBLIC_CATEGORIES = [
    "🏠 Home",
    "🎮 Games",
    "🎯 Game Requests",
    "💰 Economy",
    "🏦 Banking",
    "🔮 Bir",
    "🎖️ Rank & Levels",
    "🏆 Achievements",
    "🎲 Gambling",
    "🛒 Shop",
    "🔥 Streaks & Quests",
    "📦 Lootbox",
    "🐾 Pets",
    "⚔️ Adventure",
    "🎭 Roleplay",
    "🔢 Counting",
    "📊 Activity",
    "🏆 Tournaments",
    "🏴‍☠️ Heist",
    "🕵️ Spy",
    "🎉 Events",
    "🏆 Leaderboards",
    "ℹ️ Info",
    "🎨 Utility",
    "💎 Premium",
    "🎙️ Temp Voice",
]

ADMIN_CATEGORIES = [
    "🛠️ Moderation",
    "🎭 Roles",
    "🔧 Channels",
    "🎙️ Voice Admin",
    "📢 Announcements",
    "🔒 Staff Only",
]


# ═══════════════════════════════════════════════════════════════════
# ─── STAFF CHECK
# ═══════════════════════════════════════════════════════════════════
def _is_staff(member: discord.Member) -> bool:
    if member is None or member.guild is None:
        return False
    if member.id == member.guild.owner_id:
        return True
    names = {r.name for r in member.roles}
    ids = {r.id for r in member.roles}
    for r in ADMIN_ROLES + MODERATOR_ROLES:
        if r in names:
            return True
        rid = ROLE_NAME_TO_ID.get(r)
        if rid and rid in ids:
            return True
    return False


# ═══════════════════════════════════════════════════════════════════
# ─── UI COMPONENTS
# ═══════════════════════════════════════════════════════════════════
class CategorySelect(discord.ui.Select):
    """Dropdown dyal categories — kayqbel 25 options max. Kaytqsm f pages."""

    def __init__(self, categories, user, page: int = 0, total_pages: int = 1):
        options = [
            discord.SelectOption(
                label=cat.split(" ", 1)[1],
                emoji=cat.split(" ", 1)[0],
                value=cat,
                description=HELP_CATEGORIES[cat]["description"][:100],
            )
            for cat in categories[:25]
        ]
        if total_pages > 1:
            placeholder = f"📂 Categories ({page + 1}/{total_pages})..."
        else:
            placeholder = "Khtar category..."
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
            row=page,  # kol page f row dyalo
        )
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "❌ Had l-menu machi dyalek!", ephemeral=True
            )
        category = self.values[0]
        embed = build_category_embed(category, interaction.user)
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self, categories, user, mode: str = "public"):
        super().__init__(timeout=180)
        self.user = user
        self.mode = mode

        # ─── Split f chunks dyal 25 (Discord max options per select)
        if categories:
            chunks = [categories[i:i + 25] for i in range(0, len(categories), 25)]
            total = len(chunks)
            for i, chunk in enumerate(chunks):
                self.add_item(CategorySelect(chunk, user, page=i, total_pages=total))

    @discord.ui.button(label="Home", emoji="🏠", style=discord.ButtonStyle.secondary, row=2)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ Machi dyalek!", ephemeral=True)
        embed = build_home_embed(interaction.user, self.mode)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Close", emoji="✖️", style=discord.ButtonStyle.danger, row=2)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ Machi dyalek!", ephemeral=True)
        await interaction.message.delete()


# ═══════════════════════════════════════════════════════════════════
# ─── BUILDERS
# ═══════════════════════════════════════════════════════════════════
def build_home_embed(user: discord.Member, mode: str = "public") -> discord.Embed:
    is_admin_help = mode == "admin"

    if is_admin_help:
        title = "🔒 Staff Help Menu"
        desc = (
            "**Marhba f l-menu dyal l-Staff!**\n\n"
            "Khtar **category** mn l-dropdown bash tchouf l-commands.\n\n"
            "🔹 **Admin commands:** `+command`\n"
            "🔸 **Public commands:** `&command`\n\n"
            "💡 Ila bghiti l-public help → st3mel `&help`"
        )
        color = discord.Color.dark_red()
    else:
        title = "📖 Help Menu"
        desc = (
            "**Marhba f l-menu dyal l-bot!**\n\n"
            "Khtar **category** mn l-dropdown bash tchouf l-commands.\n"
            "L-commands kaytbanou **7sab Roles dyalk**.\n\n"
            "🔹 **Slash:** `/command`\n"
            "🔸 **Prefix:** `&command`\n\n"
            "💡 **Staff?** St3mel `+help` bash tchouf admin commands."
        )
        color = discord.Color.blurple()

    embed = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text=f"Requested by {user.name}", icon_url=user.display_avatar.url)

    categories_list = []
    cats = ADMIN_CATEGORIES if is_admin_help else PUBLIC_CATEGORIES
    for cat_name in cats:
        visible = get_visible_commands(cat_name, user)
        if visible:
            categories_list.append(f"{cat_name} — `{len(visible)} commands`")

    if categories_list:
        embed.add_field(name="📂 Categories", value="\n".join(categories_list), inline=False)
    else:
        embed.add_field(name="⚠️ Ma 3ndkch permission", value="3ayet l Admin.", inline=False)

    return embed


def build_category_embed(category: str, user: discord.Member) -> discord.Embed:
    data = HELP_CATEGORIES[category]
    emoji, name = category.split(" ", 1)

    embed = discord.Embed(
        title=f"{emoji} {name}",
        description=data["description"],
        color=discord.Color.from_rgb(88, 101, 242),
        timestamp=discord.utils.utcnow(),
    )

    visible = get_visible_commands(category, user)
    if not visible:
        embed.add_field(
            name="⚠️ Ma 3ndkch permission",
            value="Ma 3ndkch permission f had category.",
            inline=False,
        )
        return embed

    for cmd_name, desc, usage, _ in visible:
        embed.add_field(
            name=f"🔹 {cmd_name}",
            value=f"{desc}\n**Usage:** `{usage}`",
            inline=False,
        )

    embed.set_footer(
        text=f"{len(visible)} commands • {user.name}",
        icon_url=user.display_avatar.url,
    )
    return embed


def get_visible_commands(category: str, user: discord.Member):
    data = HELP_CATEGORIES[category]
    visible = []
    for cmd in data["commands"]:
        cmd_name = cmd[0]
        if not is_known_command(cmd_name):
            visible.append(cmd)
        elif user_has_permission(user, cmd_name):
            visible.append(cmd)
    return visible


def get_visible_categories(user: discord.Member, mode: str = "public"):
    cats = ADMIN_CATEGORIES if mode == "admin" else PUBLIC_CATEGORIES
    visible = []
    for cat in cats:
        if get_visible_commands(cat, user):
            visible.append(cat)
    return visible


def _find_category(raw: str, cats: list) -> str | None:
    raw = raw.lower().strip()
    for cat_name in cats:
        label = cat_name.split(" ", 1)[1].lower().strip() if " " in cat_name else cat_name.lower()
        if raw == label:
            return cat_name
    for cat_name in cats:
        label = cat_name.split(" ", 1)[1].lower().strip() if " " in cat_name else cat_name.lower()
        if raw and raw in label:
            return cat_name
    return None


# ═══════════════════════════════════════════════════════════════════
# ─── COG
# ═══════════════════════════════════════════════════════════════════
class Help(commands.Cog):
    """Help menu b Categories + Dropdown (public + admin)"""

    def __init__(self, bot):
        self.bot = bot

    async def _send_help_menu(self, ctx: commands.Context, command: str = None, mode: str = "public"):
        if command:
            return await self._show_command_details_prefix(ctx, command, mode=mode)

        user = ctx.author
        categories = get_visible_categories(user, mode=mode)

        if not categories:
            msg = (
                "⚠️ Ma 3ndkch permission l hta admin command!"
                if mode == "admin"
                else "⚠️ Ma 3ndkch permission l hta command!"
            )
            return await ctx.send(msg)

        embed = build_home_embed(user, mode=mode)
        view = HelpView(categories, user, mode=mode)
        await ctx.send(embed=embed, view=view)

    @app_commands.command(name="help", description="Affichi l-menu dyal l-commands")
    @app_commands.describe(command="(Optionnel) Category wla smiya dyal command")
    async def help_slash(self, interaction: discord.Interaction, command: str = None):
        if command:
            return await self._show_command_details(interaction, command, mode="public")

        user = interaction.user
        categories = get_visible_categories(user, mode="public")

        if not categories:
            return await interaction.response.send_message(
                "⚠️ Ma 3ndkch permission l hta command!", ephemeral=True
            )

        embed = build_home_embed(user, mode="public")
        view = HelpView(categories, user, mode="public")
        await interaction.response.send_message(embed=embed, view=view)

    @commands.command(name="help")
    async def help_prefix(self, ctx: commands.Context, command: str = None):
        """&help (public) • +help (staff only)"""
        mode = "admin" if ctx.prefix == "+" else "public"

        if mode == "admin" and not _is_staff(ctx.author):
            try:
                await ctx.message.add_reaction("🚫")
            except Exception:
                pass
            try:
                await ctx.send(
                    f"🚫 {ctx.author.mention} — `+help` ghir l-**Staff**!\n"
                    f"💡 L-public help → `&help`",
                    delete_after=8,
                )
                await ctx.message.delete(delay=8)
            except Exception:
                pass

            logs_cog = self.bot.get_cog("Logs")
            if logs_cog and ctx.guild:
                try:
                    await logs_cog.log_permission_denied(ctx.guild, ctx.author, "+help")
                except Exception:
                    pass
            return

        await self._send_help_menu(ctx, command, mode=mode)

    @commands.command(name="cmds")
    async def cmds_prefix(self, ctx: commands.Context, command: str = None):
        """&cmds [command|category] — Alias dyal &help (public only)"""
        await self._send_help_menu(ctx, command, mode="public")

    async def _show_command_details(self, interaction: discord.Interaction, query: str, mode: str = "public"):
        raw = query.lower().strip().replace("/", "").replace("&", "").replace("+", "")
        cats = ADMIN_CATEGORIES if mode == "admin" else PUBLIC_CATEGORIES

        cat_match = _find_category(raw, cats)
        if cat_match:
            embed = build_category_embed(cat_match, interaction.user)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        for cat_name in cats:
            data = HELP_CATEGORIES[cat_name]
            for cmd in data["commands"]:
                if cmd[0] == raw:
                    if not user_has_permission(interaction.user, raw):
                        return await interaction.response.send_message(
                            "❌ Ma 3ndkch permission!", ephemeral=True
                        )
                    emoji = cat_name.split(" ", 1)[0]
                    embed = discord.Embed(
                        title=f"{emoji} `{cmd[0]}`",
                        description=cmd[1],
                        color=discord.Color.blurple(),
                    )
                    embed.add_field(name="📁 Category", value=cat_name, inline=True)
                    embed.add_field(name="📝 Usage", value=f"`{cmd[2]}`", inline=False)
                    embed.add_field(name="🔹 Slash", value=f"`/{cmd[0]}`", inline=True)
                    embed.add_field(name="🔸 Prefix", value=f"`{cmd[2].split(' ')[0]}`", inline=True)
                    return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.send_message(
            f"❌ Ma l9itch `{raw}` (machi category wla command f had section)!",
            ephemeral=True,
        )

    async def _show_command_details_prefix(self, ctx: commands.Context, query: str, mode: str = "public"):
        raw = query.lower().strip().replace("/", "").replace("&", "").replace("+", "")
        cats = ADMIN_CATEGORIES if mode == "admin" else PUBLIC_CATEGORIES

        cat_match = _find_category(raw, cats)
        if cat_match:
            embed = build_category_embed(cat_match, ctx.author)
            return await ctx.send(embed=embed)

        for cat_name in cats:
            data = HELP_CATEGORIES[cat_name]
            for cmd in data["commands"]:
                if cmd[0] == raw:
                    if not user_has_permission(ctx.author, raw):
                        return await ctx.send("❌ Ma 3ndkch permission!")
                    emoji = cat_name.split(" ", 1)[0]
                    embed = discord.Embed(
                        title=f"{emoji} `{cmd[0]}`",
                        description=cmd[1],
                        color=discord.Color.blurple(),
                    )
                    embed.add_field(name="📁 Category", value=cat_name, inline=True)
                    embed.add_field(name="📝 Usage", value=f"`{cmd[2]}`", inline=False)
                    embed.add_field(name="🔹 Slash", value=f"`/{cmd[0]}`", inline=True)
                    embed.add_field(name="🔸 Prefix", value=f"`{cmd[2].split(' ')[0]}`", inline=True)
                    return await ctx.send(embed=embed)

        await ctx.send(f"❌ Ma l9itch `{raw}` (machi category wla command f had section)!")


async def setup(bot):
    await bot.add_cog(Help(bot))