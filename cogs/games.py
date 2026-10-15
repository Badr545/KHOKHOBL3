# cogs/games.py
# =====================================================================
# ─── GAMES — Trivia MP (live countdown), 8ball, roll, coinflip,
#              rps, slots, dice, guess, poll
# =====================================================================
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio


# ═══════════════════════════════════════════════════════════════════
# ─── DATA
# ═══════════════════════════════════════════════════════════════════

EIGHT_BALL = [
    "✅ Absolutely yes!", "🎉 100% yes!", "💚 Yes, definitely!",
    "😎 Without a doubt!", "🌤️ Signs point to yes.",
    "🤔 Ask again later...", "⏳ Cannot predict now.",
    "🙃 Don't count on it.", "❌ No way.", "🛑 Absolutely not!",
]

TRIVIA_BANK = [
    ("What is the capital of France?", "Paris", ["London", "Berlin", "Madrid", "Rome"]),
    ("Which planet is known as the Red Planet?", "Mars", ["Venus", "Jupiter", "Mercury", "Saturn"]),
    ("Who painted the Mona Lisa?", "Leonardo da Vinci", ["Van Gogh", "Picasso", "Michelangelo", "Raphael"]),
    ("What is 7 × 8?", "56", ["48", "54", "64", "72"]),
    ("Who wrote Romeo and Juliet?", "William Shakespeare", ["Charles Dickens", "Leo Tolstoy", "Ernest Hemingway", "Jane Austen"]),
    ("What is the chemical symbol for gold?", "Au", ["Ag", "Go", "Gd", "Gl"]),
    ("How many continents are there?", "7", ["5", "6", "8", "9"]),
    ("What is the largest ocean?", "Pacific", ["Atlantic", "Indian", "Arctic", "Southern"]),
    ("Who developed the theory of relativity?", "Albert Einstein", ["Isaac Newton", "Nikola Tesla", "Stephen Hawking", "Niels Bohr"]),
    ("What is the largest planet?", "Jupiter", ["Earth", "Saturn", "Neptune", "Uranus"]),
    ("In which country is the Eiffel Tower?", "France", ["Italy", "Spain", "Germany", "Belgium"]),
    ("Who was the first man on the Moon?", "Neil Armstrong", ["Buzz Aldrin", "Yuri Gagarin", "Michael Collins", "John Glenn"]),
    ("What is the hardest natural substance?", "Diamond", ["Iron", "Gold", "Platinum", "Quartz"]),
    ("How many sides does a hexagon have?", "6", ["4", "5", "7", "8"]),
    ("Which language has the most native speakers?", "Mandarin Chinese", ["English", "Spanish", "Hindi", "Arabic"]),
    ("Who wrote '1984'?", "George Orwell", ["Aldous Huxley", "Franz Kafka", "Albert Camus", "Ernest Hemingway"]),
    ("What is H2O?", "Water", ["Salt", "Oxygen", "Hydrogen", "Sugar"]),
    ("How many players on a soccer team?", "11", ["9", "10", "12", "13"]),
    ("Who painted the Sistine Chapel ceiling?", "Michelangelo", ["Da Vinci", "Raphael", "Donatello", "Botticelli"]),
    ("What is the capital of Japan?", "Tokyo", ["Seoul", "Beijing", "Bangkok", "Hanoi"]),
    ("Which is the largest mammal?", "Blue Whale", ["Elephant", "Giraffe", "Orca", "Hippo"]),
    ("What year did World War II end?", "1945", ["1943", "1944", "1946", "1947"]),
    ("How many strings does a standard guitar have?", "6", ["4", "5", "7", "8"]),
    ("What is the smallest prime number?", "2", ["0", "1", "3", "5"]),
    ("What's the tallest mountain?", "Mount Everest", ["K2", "Kilimanjaro", "Denali", "Matterhorn"]),
    ("Who invented the telephone?", "Alexander Graham Bell", ["Thomas Edison", "Nikola Tesla", "Guglielmo Marconi", "Samuel Morse"]),
    ("What is the capital of Australia?", "Canberra", ["Sydney", "Melbourne", "Perth", "Brisbane"]),
    ("How many colors are in a rainbow?", "7", ["5", "6", "8", "9"]),
    ("What does DNA stand for?", "Deoxyribonucleic acid", ["Dinucleic acid", "Deoxyribose nucleus", "Dual nuclear acid", "Deoxyribon acid"]),
    ("Who wrote 'Pride and Prejudice'?", "Jane Austen", ["Charlotte Brontë", "Virginia Woolf", "George Eliot", "Mary Shelley"]),
    ("What is the largest country by area?", "Russia", ["USA", "Canada", "China", "Brazil"]),
    ("What is the fastest land animal?", "Cheetah", ["Lion", "Leopard", "Horse", "Gazelle"]),
    ("How many hearts does an octopus have?", "3", ["1", "2", "4", "5"]),
    ("What's the study of plants called?", "Botany", ["Zoology", "Ecology", "Biology", "Geology"]),
    ("Which gas do plants absorb?", "Carbon dioxide", ["Oxygen", "Nitrogen", "Hydrogen", "Helium"]),
    ("What is the longest bone in the human body?", "Femur", ["Tibia", "Humerus", "Fibula", "Spine"]),
    ("Who was the first US president?", "George Washington", ["Abraham Lincoln", "Thomas Jefferson", "John Adams", "James Madison"]),
    ("What is the capital of Italy?", "Rome", ["Milan", "Venice", "Naples", "Florence"]),
    ("What is the boiling point of water in Celsius?", "100", ["50", "80", "120", "150"]),
    ("What is the currency of Japan?", "Yen", ["Won", "Yuan", "Ringgit", "Baht"]),
    ("How many bones are in an adult human body?", "206", ["186", "226", "246", "266"]),
    ("Who invented the light bulb?", "Thomas Edison", ["Alexander Bell", "Nikola Tesla", "Michael Faraday", "Alessandro Volta"]),
    ("What is the largest species of shark?", "Whale Shark", ["Great White", "Tiger", "Hammerhead", "Mako"]),
    ("What planet is closest to the Sun?", "Mercury", ["Venus", "Earth", "Mars", "Jupiter"]),
    ("Who wrote 'The Great Gatsby'?", "F. Scott Fitzgerald", ["Ernest Hemingway", "John Steinbeck", "William Faulkner", "Mark Twain"]),
    ("What is the capital of Canada?", "Ottawa", ["Toronto", "Vancouver", "Montreal", "Calgary"]),
    ("How many keys does a standard piano have?", "88", ["76", "80", "84", "92"]),
    ("What is the main ingredient in guacamole?", "Avocado", ["Tomato", "Pepper", "Onion", "Lime"]),
    ("Which country invented pizza?", "Italy", ["Greece", "France", "Spain", "Portugal"]),
    ("What is the largest island in the world?", "Greenland", ["Australia", "Borneo", "Madagascar", "New Guinea"]),
    ("What is the freezing point of water in Fahrenheit?", "32", ["0", "16", "64", "100"]),
    ("Who was the first woman to win a Nobel Prize?", "Marie Curie", ["Rosalind Franklin", "Jane Addams", "Pearl Buck", "Mother Teresa"]),
    ("What's the largest internal organ in humans?", "Liver", ["Heart", "Lungs", "Kidney", "Brain"]),
    ("In chess, what's the most powerful piece?", "Queen", ["Pawn", "Knight", "Bishop", "Rook"]),
    ("Which country has the most pyramids?", "Sudan", ["Egypt", "Mexico", "Peru", "Iraq"]),
    ("How many moons does Mars have?", "2", ["0", "1", "3", "4"]),
    ("What's the capital of Germany?", "Berlin", ["Munich", "Hamburg", "Frankfurt", "Cologne"]),
    ("What's the most spoken language in Brazil?", "Portuguese", ["Spanish", "English", "French", "Italian"]),
    ("What is the chemical symbol for sodium?", "Na", ["So", "Sd", "Nu", "Sm"]),
    ("What year did the Titanic sink?", "1912", ["1905", "1918", "1920", "1925"]),
    ("What is the smallest country in the world?", "Vatican City", ["Monaco", "Nauru", "San Marino", "Tuvalu"]),
    ("Who discovered penicillin?", "Alexander Fleming", ["Louis Pasteur", "Robert Koch", "Edward Jenner", "Jonas Salk"]),
    ("How many chambers does a human heart have?", "4", ["2", "3", "5", "6"]),
    ("Which sport uses a shuttlecock?", "Badminton", ["Tennis", "Squash", "Table Tennis", "Racquetball"]),
    ("What is the capital of Egypt?", "Cairo", ["Alexandria", "Giza", "Luxor", "Aswan"]),
    ("What is the approximate speed of light?", "300,000 km/s", ["300 km/s", "3,000 km/s", "3 million km/s", "30 km/s"]),
    ("Who wrote 'War and Peace'?", "Leo Tolstoy", ["Fyodor Dostoevsky", "Anton Chekhov", "Nikolai Gogol", "Alexander Pushkin"]),
    ("What's the smallest planet in our solar system?", "Mercury", ["Pluto", "Mars", "Venus", "Earth"]),
    ("How many teeth does an adult human typically have?", "32", ["28", "30", "34", "36"]),
    ("What's the largest bird?", "Ostrich", ["Eagle", "Emu", "Albatross", "Condor"]),
    ("What's the capital of Spain?", "Madrid", ["Barcelona", "Seville", "Valencia", "Bilbao"]),
    ("Who invented the printing press?", "Johannes Gutenberg", ["Thomas Edison", "Benjamin Franklin", "William Caxton", "Leonardo da Vinci"]),
    ("What's the most abundant gas in Earth's atmosphere?", "Nitrogen", ["Oxygen", "Carbon Dioxide", "Hydrogen", "Argon"]),
    ("What is the largest species of big cat?", "Tiger", ["Lion", "Jaguar", "Leopard", "Puma"]),
    ("How many minutes are in a full day?", "1440", ["1000", "1200", "1600", "1800"]),
    ("What is the capital of India?", "New Delhi", ["Mumbai", "Delhi", "Kolkata", "Chennai"]),
    ("Which instrument has 88 keys?", "Piano", ["Organ", "Accordion", "Harp", "Harpsichord"]),
    ("What is the longest river in the world?", "Nile", ["Amazon", "Yangtze", "Mississippi", "Congo"]),
    ("What is the largest continent?", "Asia", ["Africa", "Europe", "North America", "South America"]),
    ("What is photosynthesis?", "How plants make food", ["Cell division", "Respiration", "Digestion", "Fermentation"]),
    ("Who founded Microsoft?", "Bill Gates", ["Steve Jobs", "Elon Musk", "Mark Zuckerberg", "Jeff Bezos"]),
    ("What is the chemical symbol for iron?", "Fe", ["Ir", "In", "Fr", "Io"]),
    ("What's the capital of Russia?", "Moscow", ["St Petersburg", "Kiev", "Minsk", "Volgograd"]),
    ("How many strings does a violin have?", "4", ["5", "6", "7", "8"]),
    ("What is the largest freshwater lake by area?", "Lake Superior", ["Lake Baikal", "Lake Victoria", "Lake Tanganyika", "Lake Michigan"]),
    ("What is a group of lions called?", "Pride", ["Herd", "Pack", "Flock", "School"]),
    ("Who wrote 'The Odyssey'?", "Homer", ["Virgil", "Sophocles", "Euripides", "Plato"]),
    ("What's the smallest bone in the human body?", "Stapes", ["Malleus", "Incus", "Hyoid", "Patella"]),
    ("What does HTTP stand for?", "HyperText Transfer Protocol", ["HyperText Transmission Protocol", "High Transfer Text Protocol", "Home Tool Transfer Protocol", "Hyper Transfer Text Protocol"]),
    ("Which ocean is the deepest?", "Pacific", ["Atlantic", "Indian", "Arctic", "Southern"]),
    ("What year did the Berlin Wall fall?", "1989", ["1987", "1988", "1990", "1991"]),
    ("What is the largest land carnivore?", "Polar Bear", ["Lion", "Tiger", "Brown Bear", "Wolf"]),
    ("What's the capital of China?", "Beijing", ["Shanghai", "Hong Kong", "Guangzhou", "Shenzhen"]),
    ("What is the pH of pure water?", "7", ["5", "6", "8", "9"]),
    ("Who is known as the father of computers?", "Charles Babbage", ["Alan Turing", "Ada Lovelace", "John von Neumann", "Grace Hopper"]),
    ("What is the world's longest wall?", "Great Wall of China", ["Berlin Wall", "Hadrian's Wall", "Wall of Babylon", "Wall of Constantinople"]),
    ("How many stripes are on the USA flag?", "13", ["11", "12", "14", "15"]),
    ("What is the capital of Morocco?", "Rabat", ["Casablanca", "Marrakech", "Fez", "Tangier"]),
    ("Which metal is liquid at room temperature?", "Mercury", ["Iron", "Lead", "Aluminum", "Copper"]),
    ("What is the symbol for pi (approx)?", "3.14", ["3.41", "2.71", "1.61", "4.13"]),
    ("How many degrees in a right angle?", "90", ["45", "60", "180", "360"]),
    ("What is the largest volcano in the solar system?", "Olympus Mons", ["Mauna Kea", "Mount Etna", "Vesuvius", "Krakatoa"]),
    ("Which country gifted the Statue of Liberty to the USA?", "France", ["England", "Spain", "Italy", "Netherlands"]),
    ("Who wrote 'The Little Prince'?", "Antoine de Saint-Exupéry", ["Victor Hugo", "Albert Camus", "Jules Verne", "Marcel Proust"]),
]


# ═══════════════════════════════════════════════════════════════════
# ─── VIEWS
# ═══════════════════════════════════════════════════════════════════

class TriviaLobbyView(discord.ui.View):
    """Lobby dyal multiplayer trivia — Join + Start"""

    def __init__(self, host: discord.Member):
        super().__init__(timeout=120)
        self.host = host
        self.players: dict[int, discord.Member] = {host.id: host}
        self.started = False
        self.message: discord.Message = None

    def _lobby_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎯 Multiplayer Trivia — Lobby",
            description=(
                f"**Host:** {self.host.mention}\n"
                f"**Players:** `{len(self.players)}`\n\n"
                "Brk **🎮 Join** bach tdkhol l-game!\n"
                f"{self.host.mention}, brk **▶️ Start** mnin tkono wajdin."
            ),
            color=discord.Color.blurple(),
        )
        names = "\n".join(f"• {p.mention}" for p in self.players.values())
        embed.add_field(name="👥 Players", value=names or "—", inline=False)
        embed.set_footer(text="10 questions • Whoever answers most correctly wins!")
        return embed

    @discord.ui.button(label="Join", emoji="🎮", style=discord.ButtonStyle.primary)
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.players:
            return await interaction.response.send_message("❌ You already joined!", ephemeral=True)
        self.players[interaction.user.id] = interaction.user
        await interaction.response.send_message("✅ You joined the game!", ephemeral=True)
        if self.message:
            try:
                await self.message.edit(embed=self._lobby_embed())
            except Exception:
                pass

    @discord.ui.button(label="Start", emoji="▶️", style=discord.ButtonStyle.success)
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.host.id:
            return await interaction.response.send_message("❌ Only the host can start!", ephemeral=True)
        if len(self.players) < 1:
            return await interaction.response.send_message("❌ Not enough players!", ephemeral=True)
        self.started = True
        await interaction.response.defer()
        self.stop()


class TriviaQuestionView(discord.ui.View):
    """Kol so2al — 5 buttons (A-E). First correct wins. All wrong → skip."""

    def __init__(self, correct_idx: int, players: dict[int, discord.Member]):
        super().__init__(timeout=25)
        self.correct_idx = correct_idx
        self.players = players
        self.answered: set[int] = set()
        self.winner: discord.Member = None
        self.all_wrong = False

        labels = ["A", "B", "C", "D", "E"]
        for i, lbl in enumerate(labels):
            btn = discord.ui.Button(label=lbl, style=discord.ButtonStyle.primary,
                                    custom_id=f"trv_{i}", row=0)
            btn.callback = self._make_cb(i)
            self.add_item(btn)

    def _make_cb(self, idx: int):
        async def cb(interaction: discord.Interaction):
            if interaction.user.id not in self.players:
                return await interaction.response.send_message(
                    "❌ You're not in this game!", ephemeral=True)

            if interaction.user.id in self.answered:
                return await interaction.response.send_message(
                    "❌ You already answered!", ephemeral=True)

            if self.winner is not None:
                return await interaction.response.send_message(
                    "⌛ Round ended!", ephemeral=True)

            if idx == self.correct_idx:
                self.winner = interaction.user
                self.stop()
                await interaction.response.send_message(
                    "✅ **Correct!** You got it! 🎉", ephemeral=True)
            else:
                self.answered.add(interaction.user.id)
                left = len(self.players) - len(self.answered)
                await interaction.response.send_message(
                    f"❌ Wrong! ({left} player(s) left)", ephemeral=True)

                if len(self.answered) >= len(self.players):
                    self.all_wrong = True
                    self.stop()
        return cb


# ═══════════════════════════════════════════════════════════════════
# ─── COG
# ═══════════════════════════════════════════════════════════════════

class Games(commands.Cog):
    """Games: trivia (MP), 8ball, roll, coinflip, poll, rps, slots, dice, guess"""

    def __init__(self, bot):
        self.bot = bot

    def _pick_question(self) -> tuple:
        q, correct, wrongs = random.choice(TRIVIA_BANK)
        choices = wrongs + [correct]
        random.shuffle(choices)
        return q, choices, choices.index(correct)

    # ═══════════════════════════════════════════════════════════
    # ─── MULTIPLAYER TRIVIA
    # ═══════════════════════════════════════════════════════════

    async def _run_trivia_game(self, channel: discord.abc.Messageable,
                               players: dict, host: discord.Member):
        TOTAL = 10
        ROUND_TIME = 20
        scores = {uid: 0 for uid in players}

        await channel.send(embed=discord.Embed(
            title="🎯 **Trivia Game Starting!**",
            description=(
                f"**{TOTAL}** questions ahead.\n"
                "First correct answer wins the round!\n"
                "⏱️ If everyone answers, we skip to next immediately!\n\n"
                "Good luck 🍀"
            ),
            color=discord.Color.green(),
        ))
        await asyncio.sleep(2)

        used_indices = set()
        letters = ["A", "B", "C", "D", "E"]

        for q_num in range(1, TOTAL + 1):
            idx = None
            for _ in range(60):
                cand = random.randrange(len(TRIVIA_BANK))
                if cand not in used_indices:
                    idx = cand
                    used_indices.add(cand)
                    break
            if idx is None:
                idx = random.randrange(len(TRIVIA_BANK))

            q, correct, wrongs = TRIVIA_BANK[idx]
            choices = wrongs + [correct]
            random.shuffle(choices)
            correct_idx = choices.index(correct)

            def build_embed(seconds_left, revealed=False, winner=None):
                filled = max(0, min(15, int((seconds_left / ROUND_TIME) * 15)))
                bar = "🟩" * filled + "⬛" * (15 - filled)
                desc = "\n".join(f"**{letters[i]}.** {c}" for i, c in enumerate(choices))

                embed = discord.Embed(
                    title=f"❓ Question {q_num}/{TOTAL}",
                    description=f"**{q}**\n\n{desc}",
                    color=discord.Color.blurple(),
                )

                if not revealed:
                    embed.add_field(
                        name="⏱️ Time Remaining",
                        value=f"{bar}\n**`{seconds_left}s`** left",
                        inline=False,
                    )
                else:
                    if winner:
                        embed.color = discord.Color.green()
                        embed.add_field(
                            name="🎉 Winner",
                            value=f"{winner.mention} got it first! ⚡",
                            inline=False,
                        )
                    else:
                        embed.color = discord.Color.red()
                        embed.add_field(
                            name="😬 Round Over",
                            value="Nobody got it!",
                            inline=False,
                        )
                    embed.add_field(
                        name="✅ Correct Answer",
                        value=f"`{letters[correct_idx]}) {correct}`",
                        inline=False,
                    )

                embed.set_footer(text=f"Players: {len(players)} • Answer fast!")
                return embed

            view = TriviaQuestionView(correct_idx, players)
            msg = await channel.send(embed=build_embed(ROUND_TIME), view=view)

            async def countdown():
                try:
                    for remaining in range(ROUND_TIME - 1, -1, -1):
                        await asyncio.sleep(1)
                        if view.is_finished():
                            return
                        try:
                            await msg.edit(embed=build_embed(remaining))
                        except Exception:
                            pass
                except asyncio.CancelledError:
                    pass

            cd_task = asyncio.create_task(countdown())
            await view.wait()

            if not cd_task.done():
                cd_task.cancel()
                try:
                    await cd_task
                except asyncio.CancelledError:
                    pass

            for child in view.children:
                child.disabled = True

            if view.winner:
                scores[view.winner.id] += 1

            try:
                await msg.edit(
                    embed=build_embed(0, revealed=True, winner=view.winner),
                    view=view,
                )
            except Exception:
                pass

            await asyncio.sleep(2)

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (uid, sc) in enumerate(sorted_scores):
            member = players.get(uid)
            name = member.mention if member else f"User {uid}"
            prefix = medals[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{prefix} {name} — **{sc}** correct")

        final = discord.Embed(
            title="🏆 **Final Scoreboard**",
            description="\n".join(lines) or "—",
            color=discord.Color.gold(),
        )
        if sorted_scores and sorted_scores[0][1] > 0:
            final.add_field(
                name="🎉 Winner",
                value=f"{players[sorted_scores[0][0]].mention} with **{sorted_scores[0][1]}** correct!",
                inline=False,
            )
        await channel.send(embed=final)

    @app_commands.command(name="trivia", description="🎯 Multiplayer trivia (join + play with buttons)")
    async def trivia(self, interaction: discord.Interaction):
        view = TriviaLobbyView(interaction.user)
        await interaction.response.send_message(embed=view._lobby_embed(), view=view)
        msg = await interaction.original_response()
        view.message = msg
        await view.wait()
        if not view.started:
            try:
                return await msg.edit(view=None)
            except Exception:
                return
        try:
            await msg.edit(view=None)
        except Exception:
            pass
        await self._run_trivia_game(interaction.channel, view.players, interaction.user)

    @commands.command(name="trivia")
    async def trivia_prefix(self, ctx: commands.Context):
        """&trivia — Multiplayer trivia"""
        view = TriviaLobbyView(ctx.author)
        msg = await ctx.send(embed=view._lobby_embed(), view=view)
        view.message = msg
        await view.wait()
        if not view.started:
            try:
                return await msg.edit(view=None)
            except Exception:
                return
        try:
            await msg.edit(view=None)
        except Exception:
            pass
        await self._run_trivia_game(ctx.channel, view.players, ctx.author)

    # ═══════════════════════════════════════════════════════════
    # ─── 8BALL
    # ═══════════════════════════════════════════════════════════

    def _eightball_embed(self, question: str) -> discord.Embed:
        answer = random.choice(EIGHT_BALL)
        embed = discord.Embed(
            title="🎱 The Magic 8-Ball",
            color=discord.Color.dark_purple(),
        )
        embed.add_field(name="❓ Question", value=f"*{question}*", inline=False)
        embed.add_field(name="🔮 Answer", value=f"**{answer}**", inline=False)
        embed.set_footer(text="Ask again if you dare...")
        return embed

    @app_commands.command(name="8ball", description="S'el chi soual")
    async def eightball(self, interaction: discord.Interaction, question: str):
        await interaction.response.send_message(embed=self._eightball_embed(question))

    @commands.command(name="8ball")
    async def eightball_prefix(self, ctx: commands.Context, *, question: str):
        """&8ball <question>"""
        await ctx.send(embed=self._eightball_embed(question))

    # ═══════════════════════════════════════════════════════════
    # ─── ROLL
    # ═══════════════════════════════════════════════════════════

    def _roll_embed(self, sides: int, result: int) -> discord.Embed:
        pct = result / sides
        bars = int(pct * 20)
        bar = "█" * bars + "░" * (20 - bars)
        embed = discord.Embed(
            title=f"🎲 Rolled d{sides}",
            description=f"# **{result}**\n\n`{bar}` `{pct*100:.1f}%`",
            color=discord.Color.teal(),
        )
        return embed

    @app_commands.command(name="roll", description="Rmi dice")
    async def roll(self, interaction: discord.Interaction, sides: app_commands.Range[int, 2, 1000] = 6):
        result = random.randint(1, sides)
        await interaction.response.send_message(embed=self._roll_embed(sides, result))

    @commands.command(name="roll")
    async def roll_prefix(self, ctx: commands.Context, sides: int = 6):
        """&roll [sides]"""
        if sides < 2 or sides > 1000:
            return await ctx.send("❌ Between `2` and `1000`!")
        await ctx.send(embed=self._roll_embed(sides, random.randint(1, sides)))

    # ═══════════════════════════════════════════════════════════
    # ─── COINFLIP
    # ═══════════════════════════════════════════════════════════

    async def _play_coinflip(self, edit_func):
        result = random.choice(["HEADS", "TAILS"])
        emoji = "🪙" if result == "HEADS" else "🎭"
        color = discord.Color.gold() if result == "HEADS" else discord.Color.purple()

        frames = ["🌀", "🔄", "🌀", "🔄"]
        for f in frames:
            await asyncio.sleep(0.35)
            try:
                await edit_func(content=f"🪙 Flipping... {f}", embed=None)
            except Exception:
                pass

        final = discord.Embed(
            title=f"{emoji} **{result}**",
            description=f"# {result}",
            color=color,
        )
        final.set_footer(text="Flipped fairly 🎲")
        try:
            await edit_func(content=None, embed=final)
        except Exception:
            pass

    @app_commands.command(name="coinflip", description="Rmi coin (heads wla tails)")
    async def coinflip(self, interaction: discord.Interaction):
        await interaction.response.send_message("🪙 Flipping... 🌀")
        await self._play_coinflip(
            lambda content=None, embed=None: interaction.edit_original_response(content=content, embed=embed),
        )

    @commands.command(name="coinflip")
    async def coinflip_prefix(self, ctx: commands.Context):
        """&coinflip"""
        msg = await ctx.send("🪙 Flipping... 🌀")
        await self._play_coinflip(
            lambda content=None, embed=None: msg.edit(content=content, embed=embed),
        )

    # ═══════════════════════════════════════════════════════════
    # ─── POLL
    # ═══════════════════════════════════════════════════════════

    def _poll_embed(self, question: str, author: str) -> discord.Embed:
        embed = discord.Embed(
            title="📊 **Poll**",
            description=f"### {question}",
            color=discord.Color.orange(),
        )
        embed.set_footer(text=f"Par {author} • Vote with ✅ / ❌")
        return embed

    @app_commands.command(name="poll", description="Sondage")
    async def poll(self, interaction: discord.Interaction, question: str):
        await interaction.response.send_message(embed=self._poll_embed(question, interaction.user.name))
        msg = await interaction.original_response()
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

    @commands.command(name="poll")
    async def poll_prefix(self, ctx: commands.Context, *, question: str):
        """&poll <question>"""
        msg = await ctx.send(embed=self._poll_embed(question, ctx.author.name))
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

    # ═══════════════════════════════════════════════════════════
    # ─── RPS
    # ═══════════════════════════════════════════════════════════

    def _rps_embed(self, user_choice: str, bot_choice: str, result: str, user: discord.abc.User) -> discord.Embed:
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        if "won" in result.lower():
            color = discord.Color.green()
        elif "lost" in result.lower():
            color = discord.Color.red()
        else:
            color = discord.Color.greyple()
        embed = discord.Embed(title="⚔️ Rock Paper Scissors", color=color)
        embed.add_field(name=f"👤 {user.name}", value=f"# {emojis[user_choice]}", inline=True)
        embed.add_field(name="🆚", value="# ⚡", inline=True)
        embed.add_field(name="🤖 Bot", value=f"# {emojis[bot_choice]}", inline=True)
        embed.add_field(name="🎯 Result", value=f"## {result}", inline=False)
        return embed

    def _calc_rps(self, u: str, b: str) -> str:
        if u == b:
            return "🤝 Draw!"
        if (u == "rock" and b == "scissors") or (u == "paper" and b == "rock") or (u == "scissors" and b == "paper"):
            return "🎉 You won!"
        return "😢 You lost!"

    @app_commands.command(name="rps", description="Rock Paper Scissors")
    @app_commands.choices(choice=[
        app_commands.Choice(name="🪨 Rock", value="rock"),
        app_commands.Choice(name="📄 Paper", value="paper"),
        app_commands.Choice(name="✂️ Scissors", value="scissors"),
    ])
    async def rps(self, interaction: discord.Interaction, choice: app_commands.Choice[str]):
        bc = random.choice(["rock", "paper", "scissors"])
        u = choice.value
        result = self._calc_rps(u, bc)
        await interaction.response.send_message(embed=self._rps_embed(u, bc, result, interaction.user))

    @commands.command(name="rps")
    async def rps_prefix(self, ctx: commands.Context, choice: str):
        """&rps <rock|paper|scissors>"""
        choice = choice.lower()
        if choice not in ["rock", "paper", "scissors"]:
            return await ctx.send("❌ `rock`, `paper`, `scissors`")
        bc = random.choice(["rock", "paper", "scissors"])
        result = self._calc_rps(choice, bc)
        await ctx.send(embed=self._rps_embed(choice, bc, result, ctx.author))

    # ═══════════════════════════════════════════════════════════
    # ─── SLOTS
    # ═══════════════════════════════════════════════════════════

    def _slots_embed(self, res: list) -> discord.Embed:
        emoji_line = " ║ ".join(res)
        if res[0] == res[1] == res[2]:
            title = "🎰 **JACKPOT!** 🎉"
            desc = f"# {emoji_line}\n\n💎💎💎 **You hit the jackpot!**"
            color = discord.Color.gold()
        elif res[0] == res[1] or res[1] == res[2] or res[0] == res[2]:
            title = "🎰 **Two in a row!** ✨"
            desc = f"# {emoji_line}\n\n⭐ So close!"
            color = discord.Color.green()
        else:
            title = "🎰 **No match** 😢"
            desc = f"# {emoji_line}\n\nTry again!"
            color = discord.Color.dark_red()
        embed = discord.Embed(title=title, description=desc, color=color)
        return embed

    async def _spin_slots(self, msg: discord.Message):
        frames = 4
        emojis = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣"]
        for _ in range(frames):
            res = [random.choice(emojis) for _ in range(3)]
            try:
                await msg.edit(content=f"🎰 {res[0]} ║ {res[1]} ║ {res[2]}")
            except Exception:
                pass
            await asyncio.sleep(0.4)
        final_res = [random.choice(emojis) for _ in range(3)]
        try:
            await msg.edit(content=None, embed=self._slots_embed(final_res))
        except Exception:
            pass

    @app_commands.command(name="slots", description="Makanat l-haz")
    async def slots(self, interaction: discord.Interaction):
        await interaction.response.send_message("🎰 Spinning... 🎲")
        msg = await interaction.original_response()
        await self._spin_slots(msg)

    @commands.command(name="slots")
    async def slots_prefix(self, ctx: commands.Context):
        """&slots"""
        msg = await ctx.send("🎰 Spinning... 🎲")
        await self._spin_slots(msg)

    # ═══════════════════════════════════════════════════════════
    # ─── DICE
    # ═══════════════════════════════════════════════════════════

    def _dice_embed(self, results: list) -> discord.Embed:
        dice_emojis = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
        display = "  ".join(dice_emojis[r-1] for r in results)
        total = sum(results)
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"# {display}\n\n**Count:** `{len(results)}` • **Total:** `{total}`",
            color=discord.Color.blue(),
        )
        return embed

    @app_commands.command(name="dice", description="Zhar b emojis")
    async def dice(self, interaction: discord.Interaction, count: app_commands.Range[int, 1, 6] = 1):
        results = [random.randint(1, 6) for _ in range(count)]
        await interaction.response.send_message(embed=self._dice_embed(results))

    @commands.command(name="dice")
    async def dice_prefix(self, ctx: commands.Context, count: int = 1):
        """&dice [count]"""
        if count < 1 or count > 6:
            return await ctx.send("❌ Between `1` and `6`!")
        results = [random.randint(1, 6) for _ in range(count)]
        await ctx.send(embed=self._dice_embed(results))

    # ═══════════════════════════════════════════════════════════
    # ─── GUESS
    # ═══════════════════════════════════════════════════════════

    async def _play_guess(self, channel, user):
        number = random.randint(1, 100)
        embed = discord.Embed(
            title="🎯 Guess the Number!",
            description="I picked a number between **1** and **100**.\nYou have **5 attempts**.\n\nType your guess below!",
            color=discord.Color.blurple(),
        )
        await channel.send(embed=embed)

        def check(m):
            return m.channel == channel and m.author == user

        for attempt in range(5):
            try:
                msg = await self.bot.wait_for("message", timeout=30.0, check=check)
                try:
                    guess = int(msg.content.strip())
                except ValueError:
                    await channel.send("❌ Write a number!")
                    continue

                if guess == number:
                    win = discord.Embed(
                        title="🎉 **Correct!**",
                        description=f"You guessed `{number}` in **{attempt+1}** attempts! 🏆",
                        color=discord.Color.green(),
                    )
                    return await channel.send(embed=win)
                elif guess < number:
                    await channel.send(embed=discord.Embed(
                        title="⬆️ Higher!",
                        description=f"Attempt **{attempt+1}/5**",
                        color=discord.Color.orange(),
                    ))
                else:
                    await channel.send(embed=discord.Embed(
                        title="⬇️ Lower!",
                        description=f"Attempt **{attempt+1}/5**",
                        color=discord.Color.orange(),
                    ))
            except asyncio.TimeoutError:
                return await channel.send(embed=discord.Embed(
                    title="⏰ Time's up!",
                    description=f"The number was `{number}`",
                    color=discord.Color.red(),
                ))

        await channel.send(embed=discord.Embed(
            title="😢 **You lost!**",
            description=f"The number was `{number}`",
            color=discord.Color.red(),
        ))

    @commands.command(name="guess")
    async def guess_prefix(self, ctx: commands.Context):
        """&guess"""
        await self._play_guess(ctx.channel, ctx.author)


async def setup(bot):
    await bot.add_cog(Games(bot))