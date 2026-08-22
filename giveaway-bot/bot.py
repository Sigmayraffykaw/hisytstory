import os
import random
import sqlite3
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
DB_PATH = os.getenv("DB_PATH", "giveaways.db")
MIN_ACCOUNT_AGE_DAYS = int(os.getenv("MIN_ACCOUNT_AGE_DAYS", "7"))
INVITE_CREDIT_DELAY_MINUTES = int(os.getenv("INVITE_CREDIT_DELAY_MINUTES", "10"))

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.invites = True
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")

conn.execute("""
CREATE TABLE IF NOT EXISTS invite_counts (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    valid_invites INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS boost_counts (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    boosts INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS processed_boost_messages (
    message_id INTEGER PRIMARY KEY
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS giveaways (
    message_id INTEGER PRIMARY KEY,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    host_id INTEGER NOT NULL,
    prize TEXT NOT NULL,
    min_invites INTEGER NOT NULL,
    min_boosts INTEGER NOT NULL DEFAULT 2,
    winners INTEGER NOT NULL,
    ends_at INTEGER NOT NULL,
    ended INTEGER NOT NULL DEFAULT 0,
    required_role_id INTEGER,
    bonus_every_invites INTEGER NOT NULL DEFAULT 0,
    bonus_entries INTEGER NOT NULL DEFAULT 0
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS entries (
    message_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (message_id, user_id)
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS blacklist (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    reason TEXT,
    PRIMARY KEY (guild_id, user_id)
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS invite_joins (
    guild_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    inviter_id INTEGER NOT NULL,
    joined_at INTEGER NOT NULL,
    credited INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (guild_id, member_id)
)
""")
conn.commit()

for statement in [
    "ALTER TABLE giveaways ADD COLUMN required_role_id INTEGER",
    "ALTER TABLE giveaways ADD COLUMN bonus_every_invites INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE giveaways ADD COLUMN bonus_entries INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE giveaways ADD COLUMN min_boosts INTEGER NOT NULL DEFAULT 2",
]:
    try:
        conn.execute(statement)
        conn.commit()
    except sqlite3.OperationalError:
        pass

invite_cache: dict[int, dict[str, int]] = {}


def get_invite_count(guild_id: int, user_id: int) -> int:
    row = conn.execute(
        "SELECT valid_invites FROM invite_counts WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    ).fetchone()
    return max(0, int(row[0])) if row else 0


def add_invite(guild_id: int, user_id: int, amount: int = 1) -> None:
    conn.execute("""
        INSERT INTO invite_counts (guild_id, user_id, valid_invites)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id, user_id)
        DO UPDATE SET valid_invites = MAX(0, valid_invites + excluded.valid_invites)
    """, (guild_id, user_id, amount))
    conn.commit()


def get_boost_count(guild_id: int, user_id: int) -> int:
    row = conn.execute(
        "SELECT boosts FROM boost_counts WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    ).fetchone()
    return max(0, int(row[0])) if row else 0


def set_boost_count(guild_id: int, user_id: int, amount: int) -> None:
    amount = max(0, amount)
    conn.execute("""
        INSERT INTO boost_counts (guild_id, user_id, boosts)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id, user_id)
        DO UPDATE SET boosts = excluded.boosts
    """, (guild_id, user_id, amount))
    conn.commit()


def add_boost(guild_id: int, user_id: int, amount: int = 1) -> None:
    conn.execute("""
        INSERT INTO boost_counts (guild_id, user_id, boosts)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id, user_id)
        DO UPDATE SET boosts = MAX(0, boosts + excluded.boosts)
    """, (guild_id, user_id, amount))
    conn.commit()


def is_blacklisted(guild_id: int, user_id: int) -> bool:
    return conn.execute(
        "SELECT 1 FROM blacklist WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    ).fetchone() is not None


def entry_weight(guild_id: int, user_id: int, every: int, bonus: int) -> int:
    if every <= 0 or bonus <= 0:
        return 1
    invites = get_invite_count(guild_id, user_id)
    return 1 + (invites // every) * bonus


async def snapshot_invites(guild: discord.Guild) -> dict[str, int]:
    try:
        invites = await guild.invites()
        return {invite.code: invite.uses or 0 for invite in invites}
    except discord.Forbidden:
        return {}


def giveaway_embed(*, prize: str, winners: int, min_invites: int, min_boosts: int,
                   ends_at: int, host: discord.abc.User | None,
                   required_role_id: int | None, bonus_every_invites: int,
                   bonus_entries: int, ended: bool = False) -> discord.Embed:
    title = "🎉 GIVEAWAY ENDED" if ended else "🎉 MIAMIDIAN GIVEAWAY"
    color = discord.Color.dark_grey() if ended else discord.Color.blurple()
    role_line = f"<@&{required_role_id}>" if required_role_id else "None"
    bonus_line = (
        f"+{bonus_entries} entr{'y' if bonus_entries == 1 else 'ies'} every {bonus_every_invites} valid invites"
        if bonus_every_invites > 0 and bonus_entries > 0 else "None"
    )
    embed = discord.Embed(
        title=title,
        description=f"## {prize}\n{'Entries are closed.' if ended else 'Press **Enter Giveaway** below to enter.'}",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="🏆 Winners", value=str(winners), inline=True)
    embed.add_field(
        name="✅ Entry requirement",
        value=f"**{min_invites} valid invites OR {min_boosts} server boosts**",
        inline=False,
    )
    embed.add_field(name="🎭 Required role", value=role_line, inline=True)
    embed.add_field(name="✨ Bonus entries", value=bonus_line, inline=False)
    embed.add_field(name="⏰ Ends", value=f"<t:{ends_at}:F>\n<t:{ends_at}:R>", inline=False)
    if host:
        embed.set_footer(text=f"Hosted by {host}")
    return embed


class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Enter Giveaway",
        style=discord.ButtonStyle.success,
        emoji="🎉",
        custom_id="giveaway_enter_v3",
    )
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        row = conn.execute("""
            SELECT min_invites, min_boosts, ended, required_role_id,
                   bonus_every_invites, bonus_entries
            FROM giveaways WHERE message_id = ?
        """, (interaction.message.id,)).fetchone()

        if not row:
            return await interaction.response.send_message("I couldn't find this giveaway.", ephemeral=True)

        min_invites, min_boosts, ended, required_role_id, bonus_every, bonus_entries = row

        if ended:
            return await interaction.response.send_message("This giveaway has already ended.", ephemeral=True)
        if is_blacklisted(interaction.guild_id, interaction.user.id):
            return await interaction.response.send_message("⛔ You are blacklisted from giveaways in this server.", ephemeral=True)

        if required_role_id and isinstance(interaction.user, discord.Member):
            if interaction.user.get_role(required_role_id) is None:
                return await interaction.response.send_message(
                    f"You need the <@&{required_role_id}> role to enter.", ephemeral=True
                )

        invites = get_invite_count(interaction.guild_id, interaction.user.id)
        boosts = get_boost_count(interaction.guild_id, interaction.user.id)

        qualifies = invites >= min_invites or boosts >= min_boosts
        if not qualifies:
            return await interaction.response.send_message(
                f"You need **{min_invites} valid invites OR {min_boosts} server boosts** to enter.\n"
                f"You currently have **{invites} invites** and **{boosts} tracked boosts**.",
                ephemeral=True,
            )

        try:
            conn.execute(
                "INSERT INTO entries (message_id, user_id) VALUES (?, ?)",
                (interaction.message.id, interaction.user.id),
            )
            conn.commit()
            weight = entry_weight(interaction.guild_id, interaction.user.id, bonus_every, bonus_entries)
            method = "boosts" if boosts >= min_boosts else "invites"
            await interaction.response.send_message(
                f"✅ You're entered using your **{method}**! You have **{weight} weighted entr{'y' if weight == 1 else 'ies'}**.",
                ephemeral=True,
            )
        except sqlite3.IntegrityError:
            await interaction.response.send_message("You're already entered in this giveaway.", ephemeral=True)


async def pick_weighted_winners(message_id: int, winner_count: int) -> list[int]:
    row = conn.execute(
        "SELECT guild_id, bonus_every_invites, bonus_entries FROM giveaways WHERE message_id = ?",
        (message_id,),
    ).fetchone()
    if not row:
        return []
    guild_id, every, bonus = row
    users = [
        r[0] for r in conn.execute(
            "SELECT user_id FROM entries WHERE message_id = ?", (message_id,)
        ).fetchall() if not is_blacklisted(guild_id, r[0])
    ]
    winners: list[int] = []
    pool = users[:]
    while pool and len(winners) < winner_count:
        weights = [entry_weight(guild_id, uid, every, bonus) for uid in pool]
        pick = random.choices(pool, weights=weights, k=1)[0]
        winners.append(pick)
        pool.remove(pick)
    return winners


async def finish_giveaway(message_id: int, force: bool = False):
    row = conn.execute("""
        SELECT guild_id, channel_id, host_id, prize, min_invites, min_boosts,
               winners, ends_at, ended, required_role_id,
               bonus_every_invites, bonus_entries
        FROM giveaways WHERE message_id = ?
    """, (message_id,)).fetchone()
    if not row:
        return

    (guild_id, channel_id, host_id, prize, min_invites, min_boosts,
     winner_count, ends_at, ended, role_id, every, bonus) = row

    if ended and not force:
        return

    channel = bot.get_channel(channel_id)
    guild = bot.get_guild(guild_id)
    if not channel or not guild:
        return

    conn.execute("UPDATE giveaways SET ended = 1 WHERE message_id = ?", (message_id,))
    conn.commit()

    host = guild.get_member(host_id)
    try:
        message = await channel.fetch_message(message_id)
        await message.edit(
            embed=giveaway_embed(
                prize=prize, winners=winner_count, min_invites=min_invites,
                min_boosts=min_boosts, ends_at=ends_at, host=host,
                required_role_id=role_id, bonus_every_invites=every,
                bonus_entries=bonus, ended=True,
            ),
            view=None,
        )
    except (discord.NotFound, discord.Forbidden):
        pass

    picks = await pick_weighted_winners(message_id, winner_count)
    if not picks:
        await channel.send(f"🎉 Giveaway ended for **{prize}** — no eligible entries.")
        return

    mentions = " ".join(f"<@{uid}>" for uid in picks)
    await channel.send(f"🎉 Congratulations {mentions}! You won **{prize}**!")

    for uid in picks:
        try:
            user = guild.get_member(uid) or await bot.fetch_user(uid)
            await user.send(
                f"🏆 **You won a giveaway in {guild.name}!**\n\n"
                f"**Prize:** {prize}\nGo back to the server to claim your prize."
            )
        except (discord.Forbidden, discord.HTTPException):
            pass


async def create_giveaway_message(channel: discord.abc.Messageable, guild_id: int,
                                  channel_id: int, host: discord.abc.User,
                                  prize: str, minutes: int, min_invites: int = 5,
                                  winners: int = 1, min_boosts: int = 2,
                                  required_role: discord.Role | None = None,
                                  bonus_every_invites: int = 0,
                                  bonus_entries: int = 0):
    ends_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    unix = int(ends_at.timestamp())
    role_id = required_role.id if required_role else None

    embed = giveaway_embed(
        prize=prize, winners=winners, min_invites=min_invites,
        min_boosts=min_boosts, ends_at=unix, host=host,
        required_role_id=role_id, bonus_every_invites=bonus_every_invites,
        bonus_entries=bonus_entries,
    )

    message = await channel.send(embed=embed, view=GiveawayView())
    conn.execute("""
        INSERT INTO giveaways
        (message_id, guild_id, channel_id, host_id, prize, min_invites,
         min_boosts, winners, ends_at, ended, required_role_id,
         bonus_every_invites, bonus_entries)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
    """, (
        message.id, guild_id, channel_id, host.id, prize, min_invites,
        min_boosts, winners, unix, role_id, bonus_every_invites, bonus_entries,
    ))
    conn.commit()
    return message


@bot.event
async def on_ready():
    bot.add_view(GiveawayView())
    for guild in bot.guilds:
        invite_cache[guild.id] = await snapshot_invites(guild)
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Slash command sync failed: {e}")
    if not giveaway_watcher.is_running():
        giveaway_watcher.start()
    if not invite_validation_watcher.is_running():
        invite_validation_watcher.start()
    print(f"Logged in as {bot.user}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    invite_cache[guild.id] = await snapshot_invites(guild)


@bot.event
async def on_message(message: discord.Message):
    if message.guild and message.author and not message.author.bot:
        # Discord's normal "X just boosted the server!" system message.
        if message.type == discord.MessageType.premium_guild_subscription:
            already = conn.execute(
                "SELECT 1 FROM processed_boost_messages WHERE message_id = ?",
                (message.id,),
            ).fetchone()
            if not already:
                add_boost(message.guild.id, message.author.id, 1)
                conn.execute(
                    "INSERT INTO processed_boost_messages (message_id) VALUES (?)",
                    (message.id,),
                )
                conn.commit()
                print(f"Tracked boost from {message.author} in {message.guild.name}")

    await bot.process_commands(message)


@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild
    before = invite_cache.get(guild.id, {})
    after = await snapshot_invites(guild)
    used_invite = None

    try:
        invites = await guild.invites()
        for invite in invites:
            if (invite.uses or 0) > before.get(invite.code, 0):
                used_invite = invite
                break
    except discord.Forbidden:
        pass

    invite_cache[guild.id] = after

    if not used_invite or not used_invite.inviter or member.bot:
        return
    if used_invite.inviter.id == member.id:
        return

    if datetime.now(timezone.utc) - member.created_at < timedelta(days=MIN_ACCOUNT_AGE_DAYS):
        return

    conn.execute("""
        INSERT INTO invite_joins (guild_id, member_id, inviter_id, joined_at, credited, active)
        VALUES (?, ?, ?, ?, 0, 1)
        ON CONFLICT(guild_id, member_id)
        DO UPDATE SET inviter_id = excluded.inviter_id,
                      joined_at = excluded.joined_at,
                      credited = 0,
                      active = 1
    """, (
        guild.id, member.id, used_invite.inviter.id,
        int(datetime.now(timezone.utc).timestamp()),
    ))
    conn.commit()


@bot.event
async def on_member_remove(member: discord.Member):
    row = conn.execute(
        "SELECT inviter_id, credited FROM invite_joins WHERE guild_id = ? AND member_id = ? AND active = 1",
        (member.guild.id, member.id),
    ).fetchone()
    if row:
        inviter_id, credited = row
        if credited:
            add_invite(member.guild.id, inviter_id, -1)
        conn.execute(
            "UPDATE invite_joins SET active = 0 WHERE guild_id = ? AND member_id = ?",
            (member.guild.id, member.id),
        )
        conn.commit()


# ---------------- Slash commands ----------------

@bot.tree.command(name="invites", description="Check valid invites for yourself or another member")
async def invites_cmd(interaction: discord.Interaction, member: discord.Member | None = None):
    target = member or interaction.user
    count = get_invite_count(interaction.guild_id, target.id)
    boosts = get_boost_count(interaction.guild_id, target.id)
    await interaction.response.send_message(
        f"📨 {target.mention}: **{count} valid invites** | 🚀 **{boosts} tracked boosts**"
    )


@bot.tree.command(name="giveaway_create", description="Create an advanced giveaway")
@app_commands.checks.has_permissions(manage_guild=True)
async def giveaway_create(
    interaction: discord.Interaction,
    prize: str,
    minutes: app_commands.Range[int, 1, 43200],
    min_invites: app_commands.Range[int, 0, 1000] = 5,
    winners: app_commands.Range[int, 1, 20] = 1,
    min_boosts: app_commands.Range[int, 0, 20] = 2,
    required_role: discord.Role | None = None,
    bonus_every_invites: app_commands.Range[int, 0, 1000] = 0,
    bonus_entries: app_commands.Range[int, 0, 50] = 0,
):
    await interaction.response.send_message("Creating giveaway...", ephemeral=True)
    message = await create_giveaway_message(
        interaction.channel, interaction.guild_id, interaction.channel_id,
        interaction.user, prize, minutes, min_invites, winners, min_boosts,
        required_role, bonus_every_invites, bonus_entries,
    )
    await interaction.edit_original_response(content=f"✅ Giveaway created: {message.jump_url}")


@bot.tree.command(name="giveaway_end", description="End a giveaway immediately")
@app_commands.checks.has_permissions(manage_guild=True)
async def giveaway_end(interaction: discord.Interaction, message_id: str):
    if not message_id.isdigit():
        return await interaction.response.send_message("Invalid message ID.", ephemeral=True)
    await finish_giveaway(int(message_id))
    await interaction.response.send_message("✅ Giveaway ended.", ephemeral=True)


@bot.tree.command(name="giveaway_reroll", description="Reroll winners from an ended giveaway")
@app_commands.checks.has_permissions(manage_guild=True)
async def giveaway_reroll(interaction: discord.Interaction, message_id: str,
                          winners: app_commands.Range[int, 1, 20] = 1):
    if not message_id.isdigit():
        return await interaction.response.send_message("Invalid message ID.", ephemeral=True)
    picks = await pick_weighted_winners(int(message_id), winners)
    if not picks:
        return await interaction.response.send_message("No eligible entries found.", ephemeral=True)
    await interaction.response.send_message("🎲 New winner(s): " + " ".join(f"<@{uid}>" for uid in picks))


@bot.tree.command(name="giveaway_blacklist", description="Blacklist a member from giveaways")
@app_commands.checks.has_permissions(manage_guild=True)
async def giveaway_blacklist(interaction: discord.Interaction, member: discord.Member,
                             reason: str = "No reason provided"):
    conn.execute(
        "INSERT OR REPLACE INTO blacklist (guild_id, user_id, reason) VALUES (?, ?, ?)",
        (interaction.guild_id, member.id, reason[:300]),
    )
    conn.commit()
    await interaction.response.send_message(f"⛔ {member.mention} is now blacklisted.\nReason: {reason}")


@bot.tree.command(name="giveaway_unblacklist", description="Remove a member from the giveaway blacklist")
@app_commands.checks.has_permissions(manage_guild=True)
async def giveaway_unblacklist(interaction: discord.Interaction, member: discord.Member):
    conn.execute("DELETE FROM blacklist WHERE guild_id = ? AND user_id = ?", (interaction.guild_id, member.id))
    conn.commit()
    await interaction.response.send_message(f"✅ {member.mention} was removed from the giveaway blacklist.")


@bot.tree.command(name="giveaway_blacklist_check", description="Check whether a member is giveaway-blacklisted")
@app_commands.checks.has_permissions(manage_guild=True)
async def giveaway_blacklist_check(interaction: discord.Interaction, member: discord.Member):
    row = conn.execute(
        "SELECT reason FROM blacklist WHERE guild_id = ? AND user_id = ?",
        (interaction.guild_id, member.id),
    ).fetchone()
    if row:
        await interaction.response.send_message(f"⛔ {member.mention} is blacklisted.\nReason: {row[0]}", ephemeral=True)
    else:
        await interaction.response.send_message(f"✅ {member.mention} is not blacklisted.", ephemeral=True)


@bot.tree.command(name="giveaway_set_boosts", description="Set a member's tracked giveaway boost count")
@app_commands.checks.has_permissions(manage_guild=True)
async def giveaway_set_boosts(interaction: discord.Interaction, member: discord.Member,
                              boosts: app_commands.Range[int, 0, 50]):
    set_boost_count(interaction.guild_id, member.id, boosts)
    await interaction.response.send_message(
        f"🚀 Set {member.mention}'s tracked boost count to **{boosts}**."
    )


# ---------------- Dot commands ----------------

@bot.command(name="ghelp", aliases=["giveawayhelp"])
async def dot_help(ctx: commands.Context):
    embed = discord.Embed(title="🎉 Giveaway Bot Commands", color=discord.Color.blurple())
    embed.description = (
        "`.giveaway <minutes> <min_invites> <winners> <prize>`\n"
        "Default eligibility: **5 invites OR 2 boosts**\n\n"
        "`.gend <message_id>`\n"
        "`.greroll <message_id> [winners]`\n"
        "`.invites [@member]`\n"
        "`.boosts [@member]`\n"
        "`.setboosts @member <amount>` (Manage Server)\n"
        "`.gblacklist @member [reason]`\n"
        "`.gunblacklist @member`\n"
        "`.gblacklistcheck @member`"
    )
    await ctx.send(embed=embed)


@bot.command(name="invites")
async def dot_invites(ctx: commands.Context, member: discord.Member | None = None):
    if not ctx.guild:
        return
    target = member or ctx.author
    invites = get_invite_count(ctx.guild.id, target.id)
    boosts = get_boost_count(ctx.guild.id, target.id)
    await ctx.send(f"📨 {target.mention}: **{invites} valid invites** | 🚀 **{boosts} tracked boosts**")


@bot.command(name="boosts")
async def dot_boosts(ctx: commands.Context, member: discord.Member | None = None):
    if not ctx.guild:
        return
    target = member or ctx.author
    boosts = get_boost_count(ctx.guild.id, target.id)
    await ctx.send(f"🚀 {target.mention} has **{boosts} tracked server boost{'s' if boosts != 1 else ''}**.")


@bot.command(name="setboosts")
@commands.has_guild_permissions(manage_guild=True)
async def dot_setboosts(ctx: commands.Context, member: discord.Member, amount: int):
    if not ctx.guild:
        return
    amount = max(0, min(amount, 50))
    set_boost_count(ctx.guild.id, member.id, amount)
    await ctx.send(f"🚀 Set {member.mention}'s tracked boost count to **{amount}**.")


@bot.command(name="giveaway", aliases=["gcreate"])
@commands.has_guild_permissions(manage_guild=True)
async def dot_giveaway(ctx: commands.Context, minutes: int, min_invites: int,
                       winners: int, *, prize: str):
    if not ctx.guild:
        return
    if not 1 <= minutes <= 43200 or not 0 <= min_invites <= 1000 or not 1 <= winners <= 20:
        return await ctx.send("❌ Use: `.giveaway <minutes> <min_invites> <winners> <prize>`")
    message = await create_giveaway_message(
        ctx.channel, ctx.guild.id, ctx.channel.id, ctx.author,
        prize, minutes, min_invites, winners, 2,
    )
    await ctx.send(f"✅ Giveaway created: {message.jump_url}", delete_after=10)


@bot.command(name="gend", aliases=["giveawayend"])
@commands.has_guild_permissions(manage_guild=True)
async def dot_end(ctx: commands.Context, message_id: int):
    await finish_giveaway(message_id)
    await ctx.send("✅ Giveaway ended.")


@bot.command(name="greroll", aliases=["giveawayreroll"])
@commands.has_guild_permissions(manage_guild=True)
async def dot_reroll(ctx: commands.Context, message_id: int, winners: int = 1):
    winners = max(1, min(winners, 20))
    picks = await pick_weighted_winners(message_id, winners)
    if not picks:
        return await ctx.send("No eligible entries found.")
    await ctx.send("🎲 New winner(s): " + " ".join(f"<@{uid}>" for uid in picks))


@bot.command(name="gblacklist")
@commands.has_guild_permissions(manage_guild=True)
async def dot_blacklist(ctx: commands.Context, member: discord.Member,
                        *, reason: str = "No reason provided"):
    conn.execute(
        "INSERT OR REPLACE INTO blacklist (guild_id, user_id, reason) VALUES (?, ?, ?)",
        (ctx.guild.id, member.id, reason[:300]),
    )
    conn.commit()
    await ctx.send(f"⛔ {member.mention} is now blacklisted.\nReason: {reason}")


@bot.command(name="gunblacklist")
@commands.has_guild_permissions(manage_guild=True)
async def dot_unblacklist(ctx: commands.Context, member: discord.Member):
    conn.execute("DELETE FROM blacklist WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
    conn.commit()
    await ctx.send(f"✅ {member.mention} was removed from the giveaway blacklist.")


@bot.command(name="gblacklistcheck")
@commands.has_guild_permissions(manage_guild=True)
async def dot_blacklist_check(ctx: commands.Context, member: discord.Member):
    row = conn.execute(
        "SELECT reason FROM blacklist WHERE guild_id = ? AND user_id = ?",
        (ctx.guild.id, member.id),
    ).fetchone()
    if row:
        await ctx.send(f"⛔ {member.mention} is blacklisted.\nReason: {row[0]}")
    else:
        await ctx.send(f"✅ {member.mention} is not blacklisted.")


@dot_giveaway.error
@dot_end.error
@dot_reroll.error
@dot_blacklist.error
@dot_unblacklist.error
@dot_blacklist_check.error
@dot_setboosts.error
async def dot_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need **Manage Server** to use that command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing something. Use `.ghelp` to see the command format.")
    elif isinstance(error, (commands.BadArgument, commands.MemberNotFound)):
        await ctx.send("I couldn't understand one of those values. Use `.ghelp` for examples.")
    else:
        print(f"Prefix command error: {error}")
        await ctx.send("Something went wrong while running that command.")


@giveaway_create.error
@giveaway_end.error
@giveaway_reroll.error
@giveaway_blacklist.error
@giveaway_unblacklist.error
@giveaway_blacklist_check.error
@giveaway_set_boosts.error
async def command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        message = "You need **Manage Server** to use that command."
    else:
        print(f"Command error: {error}")
        message = "Something went wrong while running that command."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


@tasks.loop(seconds=20)
async def giveaway_watcher():
    now = int(datetime.now(timezone.utc).timestamp())
    rows = conn.execute(
        "SELECT message_id FROM giveaways WHERE ended = 0 AND ends_at <= ?", (now,)
    ).fetchall()
    for (message_id,) in rows:
        try:
            await finish_giveaway(message_id)
        except Exception as e:
            print(f"Failed to end giveaway {message_id}: {e}")


@tasks.loop(minutes=1)
async def invite_validation_watcher():
    cutoff = int((datetime.now(timezone.utc) - timedelta(minutes=INVITE_CREDIT_DELAY_MINUTES)).timestamp())
    rows = conn.execute("""
        SELECT guild_id, member_id, inviter_id
        FROM invite_joins
        WHERE active = 1 AND credited = 0 AND joined_at <= ?
    """, (cutoff,)).fetchall()

    for guild_id, member_id, inviter_id in rows:
        guild = bot.get_guild(guild_id)
        if not guild:
            continue
        member = guild.get_member(member_id)
        inviter = guild.get_member(inviter_id)
        if not member or not inviter or member.bot:
            conn.execute(
                "UPDATE invite_joins SET active = 0 WHERE guild_id = ? AND member_id = ?",
                (guild_id, member_id),
            )
            conn.commit()
            continue
        if datetime.now(timezone.utc) - member.created_at < timedelta(days=MIN_ACCOUNT_AGE_DAYS):
            conn.execute(
                "UPDATE invite_joins SET active = 0 WHERE guild_id = ? AND member_id = ?",
                (guild_id, member_id),
            )
            conn.commit()
            continue
        add_invite(guild_id, inviter_id, 1)
        conn.execute(
            "UPDATE invite_joins SET credited = 1 WHERE guild_id = ? AND member_id = ?",
            (guild_id, member_id),
        )
        conn.commit()


@giveaway_watcher.before_loop
@invite_validation_watcher.before_loop
async def before_watchers():
    await bot.wait_until_ready()


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Put it in your environment variables.")

bot.run(TOKEN)
