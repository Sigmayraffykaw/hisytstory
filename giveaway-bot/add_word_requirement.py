from pathlib import Path

path = Path(__file__).with_name("bot.py")
text = path.read_text(encoding="utf-8")

if "CREATE TABLE IF NOT EXISTS word_counts" in text:
    print("Word requirement is already installed.")
    raise SystemExit

# Add persistent per-server word counters.
marker = 'conn.execute("""\nCREATE TABLE IF NOT EXISTS boost_counts ('
code = '''conn.execute("""\nCREATE TABLE IF NOT EXISTS word_counts (\n    guild_id INTEGER NOT NULL,\n    user_id INTEGER NOT NULL,\n    words INTEGER NOT NULL DEFAULT 0,\n    PRIMARY KEY (guild_id, user_id)\n)\n""")\n\n'''
if marker not in text:
    raise RuntimeError("Could not find database table marker")
text = text.replace(marker, code + marker, 1)

# Helpers.
marker = 'def get_boost_count(guild_id: int, user_id: int) -> int:'
code = '''def get_word_count(guild_id: int, user_id: int) -> int:\n    row = conn.execute(\n        "SELECT words FROM word_counts WHERE guild_id = ? AND user_id = ?",\n        (guild_id, user_id),\n    ).fetchone()\n    return max(0, int(row[0])) if row else 0\n\n\ndef add_words(guild_id: int, user_id: int, amount: int) -> None:\n    if amount <= 0:\n        return\n    conn.execute("""\n        INSERT INTO word_counts (guild_id, user_id, words)\n        VALUES (?, ?, ?)\n        ON CONFLICT(guild_id, user_id)\n        DO UPDATE SET words = words + excluded.words\n    """, (guild_id, user_id, amount))\n    conn.commit()\n\n\n'''
if marker not in text:
    raise RuntimeError("Could not find helper marker")
text = text.replace(marker, code + marker, 1)

# Track words from normal member messages. Existing on_message already ignores bots.
marker = '    if message.guild and message.author and not message.author.bot:\n'
replacement = '''    if message.guild and message.author and not message.author.bot:\n        # Count whitespace-separated words for giveaway eligibility.\n        # Commands beginning with the bot prefix are excluded.\n        if message.content and not message.content.startswith("."):\n            add_words(message.guild.id, message.author.id, len(message.content.split()))\n'''
if marker not in text:
    raise RuntimeError("Could not find on_message marker")
text = text.replace(marker, replacement, 1)

# Entry requirement: 5 invites OR 2 boosts OR 2000 words.
old = '        qualifies = invites >= min_invites or boosts >= min_boosts\n'
new = '''        words = get_word_count(interaction.guild_id, interaction.user.id)\n        min_words = 2000\n        qualifies = invites >= min_invites or boosts >= min_boosts or words >= min_words\n'''
if old not in text:
    raise RuntimeError("Could not find eligibility check")
text = text.replace(old, new, 1)

old = '''                f"You need **{min_invites} valid invites OR {min_boosts} server boosts** to enter.\\n"\n                f"You currently have **{invites} invites** and **{boosts} tracked boosts**.",'''
new = '''                f"You need **{min_invites} valid invites OR {min_boosts} server boosts OR {min_words:,} words** to enter.\\n"\n                f"You currently have **{invites} invites**, **{boosts} tracked boosts**, and **{words:,} words**.",'''
if old not in text:
    raise RuntimeError("Could not find eligibility failure message")
text = text.replace(old, new, 1)

old = '            method = "boosts" if boosts >= min_boosts else "invites"\n'
new = '            method = "boosts" if boosts >= min_boosts else ("invites" if invites >= min_invites else "words")\n'
if old not in text:
    raise RuntimeError("Could not find entry method")
text = text.replace(old, new, 1)

# Display 2000 words on giveaway embeds.
old = '        value=f"**{min_invites} valid invites OR {min_boosts} server boosts**",\n'
new = '        value=f"**{min_invites} valid invites OR {min_boosts} server boosts OR 2,000 words**",\n'
if old not in text:
    raise RuntimeError("Could not find embed requirement")
text = text.replace(old, new, 1)

# Add public .words command before .boosts.
marker = '@bot.command(name="boosts")'
code = '''@bot.command(name="words")\nasync def dot_words(ctx: commands.Context, member: discord.Member | None = None):\n    if not ctx.guild:\n        return\n    target = member or ctx.author\n    words = get_word_count(ctx.guild.id, target.id)\n    await ctx.send(f"💬 {target.mention} has **{words:,} tracked words**.")\n\n\n'''
if marker not in text:
    raise RuntimeError("Could not find .boosts marker")
text = text.replace(marker, code + marker, 1)

# Add slash /giveaway_words before slash boost count command if present.
marker = '@bot.tree.command(name="giveaway_boosts"'
if marker in text:
    code = '''@bot.tree.command(name="giveaway_words", description="Check tracked giveaway words")\nasync def giveaway_words(interaction: discord.Interaction, member: discord.Member | None = None):\n    if not interaction.guild:\n        return await interaction.response.send_message("Use this in a server.", ephemeral=True)\n    target = member or interaction.user\n    words = get_word_count(interaction.guild_id, target.id)\n    await interaction.response.send_message(f"💬 {target.mention} has **{words:,} tracked words**.")\n\n\n'''
    text = text.replace(marker, code + marker, 1)

# Add to .ghelp if exact line exists.
help_line = '"`.boosts [@member]`\\n"'
if help_line in text:
    text = text.replace(help_line, '"`.boosts [@member]`\\n"\n        "`.words [@member]` — tracked word count\\n"', 1)

path.write_text(text, encoding="utf-8")
print("Added 2,000-word giveaway eligibility and word tracking to bot.py")
