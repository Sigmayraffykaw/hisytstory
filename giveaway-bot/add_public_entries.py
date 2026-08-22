from pathlib import Path

path = Path(__file__).with_name("bot.py")
text = path.read_text(encoding="utf-8")

if 'name="giveaway_entries"' in text or '@bot.command(name="gentries")' in text:
    print("Public entries commands are already installed.")
    raise SystemExit

slash_marker = '# ---------------- Dot commands ----------------'
slash_code = '''@bot.tree.command(name="giveaway_entries", description="Show everyone entered in a giveaway")
async def giveaway_entries(interaction: discord.Interaction, message_id: str):
    if not interaction.guild or not message_id.isdigit():
        return await interaction.response.send_message("Invalid giveaway message ID.")

    giveaway_id = int(message_id)
    row = conn.execute(
        "SELECT guild_id, prize FROM giveaways WHERE message_id = ?",
        (giveaway_id,),
    ).fetchone()
    if not row or row[0] != interaction.guild_id:
        return await interaction.response.send_message("I couldn't find that giveaway in this server.")

    user_ids = [r[0] for r in conn.execute(
        "SELECT user_id FROM entries WHERE message_id = ? ORDER BY user_id",
        (giveaway_id,),
    ).fetchall()]

    if not user_ids:
        return await interaction.response.send_message(f"🎟️ **{row[1]}** currently has **0 entries**.")

    mentions = [f"<@{uid}>" for uid in user_ids]
    chunks = [mentions[i:i + 40] for i in range(0, len(mentions), 40)]
    await interaction.response.send_message(
        f"🎟️ **{row[1]} — {len(user_ids)} entered**\\n" + " ".join(chunks[0])
    )
    for chunk in chunks[1:]:
        await interaction.followup.send(" ".join(chunk))


'''

if slash_marker not in text:
    raise RuntimeError("Could not find dot-command section in bot.py")
text = text.replace(slash_marker, slash_code + slash_marker, 1)

dot_marker = '@bot.command(name="gend", aliases=["giveawayend"])'
dot_code = '''@bot.command(name="gentries", aliases=["entries"])
async def dot_entries(ctx: commands.Context, message_id: int):
    if not ctx.guild:
        return

    row = conn.execute(
        "SELECT guild_id, prize FROM giveaways WHERE message_id = ?",
        (message_id,),
    ).fetchone()
    if not row or row[0] != ctx.guild.id:
        return await ctx.send("I couldn't find that giveaway in this server.")

    user_ids = [r[0] for r in conn.execute(
        "SELECT user_id FROM entries WHERE message_id = ? ORDER BY user_id",
        (message_id,),
    ).fetchall()]

    if not user_ids:
        return await ctx.send(f"🎟️ **{row[1]}** currently has **0 entries**.")

    mentions = [f"<@{uid}>" for uid in user_ids]
    await ctx.send(f"🎟️ **{row[1]} — {len(user_ids)} entered**")
    for i in range(0, len(mentions), 40):
        await ctx.send(" ".join(mentions[i:i + 40]))


'''

if dot_marker not in text:
    raise RuntimeError("Could not find .gend command in bot.py")
text = text.replace(dot_marker, dot_code + dot_marker, 1)

help_old = '"`.boosts [@member]`\\n"'
help_new = '"`.boosts [@member]`\\n"\n        "`.gentries <message_id>` — public entrant list\\n"'
if help_old in text:
    text = text.replace(help_old, help_new, 1)

path.write_text(text, encoding="utf-8")
print("Added public .gentries and /giveaway_entries commands to bot.py")
