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

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.invites = True

bot = commands.Bot(command_prefix="!", intents=intents)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute(
    """
    CREATE TABLE IF NOT EXISTS invite_counts (
        guild_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        valid_invites INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (guild_id, user_id)
    )
    """
)
conn.execute(
    """
    CREATE TABLE IF NOT EXISTS giveaways (
        message_id INTEGER PRIMARY KEY,
        guild_id INTEGER NOT NULL,
        channel_id INTEGER NOT NULL,
        host_id INTEGER NOT NULL,
        prize TEXT NOT NULL,
        min_invites INTEGER NOT NULL,
        winners INTEGER NOT NULL,
        ends_at INTEGER NOT NULL,
        ended INTEGER NOT NULL DEFAULT 0
    )
    """
)
conn.execute(
    """
    CREATE TABLE IF NOT EXISTS entries (
        message_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        PRIMARY KEY (message_id, user_id)
    )
    """
)
conn.commit()

invite_cache: dict[int, dict[str, int]] = {}


def get_invite_count(guild_id: int, user_id: int) -> int:
    row = conn.execute(
        "SELECT valid_invites FROM invite_counts WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    ).fetchone()
    return int(row[0]) if row else 0


def add_invite(guild_id: int, user_id: int, amount: int = 1) -> None:
    conn.execute(
        """
        INSERT INTO invite_counts (guild_id, user_id, valid_invites)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id, user_id)
        DO UPDATE SET valid_invites = valid_invites + excluded.valid_invites
        """,
        (guild_id, user_id, amount),
    )
    conn.commit()


async def snapshot_invites(guild: discord.Guild) -> dict[str, int]:
    try:
        invites = await guild.invites()
        return {invite.code: invite.uses or 0 for invite in invites}
    except discord.Forbidden:
        return {}


class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Enter Giveaway",
        style=discord.ButtonStyle.success,
        emoji="🎉",
        custom_id="giveaway_enter_v1",
    )
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        row = conn.execute(
            "SELECT min_invites, ended FROM giveaways WHERE message_id = ?",
            (interaction.message.id,),
        ).fetchone()

        if not row:
            return await interaction.response.send_message(
                "I couldn't find this giveaway.", ephemeral=True
            )

        min_invites, ended = row
        if ended:
            return await interaction.response.send_message(
                "This giveaway has already ended.", ephemeral=True
            )

        current = get_invite_count(interaction.guild_id, interaction.user.id)
        if current < min_invites:
            return await interaction.response.send_message(
                f"You need **{min_invites} valid invites** to enter. You currently have **{current}**.",
                ephemeral=True,
            )

        try:
            conn.execute(
                "INSERT INTO entries (message_id, user_id) VALUES (?, ?)",
                (interaction.message.id, interaction.user.id),
            )
            conn.commit()
            await interaction.response.send_message(
                "✅ You're entered! Good luck.", ephemeral=True
            )
        except sqlite3.IntegrityError:
            await interaction.response.send_message(
                "You're already entered in this giveaway.", ephemeral=True
            )


async def finish_giveaway(message_id: int, force: bool = False):
    row = conn.execute(
        """
        SELECT guild_id, channel_id, prize, winners, ended
        FROM giveaways WHERE message_id = ?
        """,
        (message_id,),
    ).fetchone()
    if not row:
        return

    guild_id, channel_id, prize, winner_count, ended = row
    if ended and not force:
        return

    channel = bot.get_channel(channel_id)
    if not channel:
        return

    entries = [
        r[0]
        for r in conn.execute(
            "SELECT user_id FROM entries WHERE message_id = ?", (message_id,)
        ).fetchall()
    ]

    conn.execute("UPDATE giveaways SET ended = 1 WHERE message_id = ?", (message_id,))
    conn.commit()

    if not entries:
        await channel.send(f"🎉 Giveaway ended for **{prize}** — no eligible entries.")
        return

    picks = random.sample(entries, min(winner_count, len(entries)))
    mentions = " ".join(f"<@{uid}>" for uid in picks)
    await channel.send(f"🎉 Congratulations {mentions}! You won **{prize}**!")


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
    print(f"Logged in as {bot.user}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    invite_cache[guild.id] = await snapshot_invites(guild)


@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild
    before = invite_cache.get(guild.id, {})
    after = await snapshot_invites(guild)

    used_invite = None
    try:
        invites = await guild.invites()
        for invite in invites:
            previous_uses = before.get(invite.code, 0)
            current_uses = invite.uses or 0
            if current_uses > previous_uses:
                used_invite = invite
                break
    except discord.Forbidden:
        pass

    invite_cache[guild.id] = after

    if used_invite and used_invite.inviter and not member.bot:
        add_invite(guild.id, used_invite.inviter.id, 1)


@bot.event
async def on_member_remove(member: discord.Member):
    # Leaving members are not automatically deducted because Discord does not
    # provide a reliable historical invite relationship after departure.
    pass


@bot.tree.command(name="invites", description="Check valid invites for yourself or another member")
@app_commands.describe(member="Member to check")
async def invites_cmd(interaction: discord.Interaction, member: discord.Member | None = None):
    target = member or interaction.user
    count = get_invite_count(interaction.guild_id, target.id)
    await interaction.response.send_message(
        f"📨 {target.mention} has **{count} valid invite{'s' if count != 1 else ''}**."
    )


@bot.tree.command(name="giveaway_create", description="Create a giveaway with an invite requirement")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(
    prize="Prize being given away",
    minutes="How many minutes the giveaway lasts",
    min_invites="Valid invites required to enter",
    winners="Number of winners",
)
async def giveaway_create(
    interaction: discord.Interaction,
    prize: str,
    minutes: app_commands.Range[int, 1, 43200],
    min_invites: app_commands.Range[int, 0, 1000] = 5,
    winners: app_commands.Range[int, 1, 20] = 1,
):
    ends_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    unix = int(ends_at.timestamp())

    embed = discord.Embed(
        title="🎉 GIVEAWAY",
        description=(
            f"**Prize:** {prize}\n\n"
            f"**Winners:** {winners}\n"
            f"**Invite requirement:** {min_invites} valid invites\n"
            f"**Ends:** <t:{unix}:R>\n\n"
            "Press **Enter Giveaway** below to enter."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text=f"Hosted by {interaction.user}")

    await interaction.response.send_message("Creating giveaway...", ephemeral=True)
    message = await interaction.channel.send(embed=embed, view=GiveawayView())

    conn.execute(
        """
        INSERT INTO giveaways
        (message_id, guild_id, channel_id, host_id, prize, min_invites, winners, ends_at, ended)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            message.id,
            interaction.guild_id,
            interaction.channel_id,
            interaction.user.id,
            prize,
            min_invites,
            winners,
            unix,
        ),
    )
    conn.commit()

    await interaction.edit_original_response(
        content=f"✅ Giveaway created: {message.jump_url}"
    )


@bot.tree.command(name="giveaway_end", description="End a giveaway immediately")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(message_id="Giveaway message ID")
async def giveaway_end(interaction: discord.Interaction, message_id: str):
    if not message_id.isdigit():
        return await interaction.response.send_message("Invalid message ID.", ephemeral=True)
    await finish_giveaway(int(message_id))
    await interaction.response.send_message("✅ Giveaway ended.", ephemeral=True)


@bot.tree.command(name="giveaway_reroll", description="Reroll winners from an ended giveaway")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(message_id="Giveaway message ID", winners="Number of winners to reroll")
async def giveaway_reroll(
    interaction: discord.Interaction,
    message_id: str,
    winners: app_commands.Range[int, 1, 20] = 1,
):
    if not message_id.isdigit():
        return await interaction.response.send_message("Invalid message ID.", ephemeral=True)

    entries = [
        r[0]
        for r in conn.execute(
            "SELECT user_id FROM entries WHERE message_id = ?", (int(message_id),)
        ).fetchall()
    ]
    if not entries:
        return await interaction.response.send_message(
            "No entries found for that giveaway.", ephemeral=True
        )

    picks = random.sample(entries, min(winners, len(entries)))
    mentions = " ".join(f"<@{uid}>" for uid in picks)
    await interaction.response.send_message(f"🎲 New winner(s): {mentions}")


@giveaway_create.error
@giveaway_end.error
@giveaway_reroll.error
async def command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        message = "You need **Manage Server** to use that command."
    else:
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


@giveaway_watcher.before_loop
async def before_watcher():
    await bot.wait_until_ready()


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Put it in your environment variables.")

bot.run(TOKEN)
