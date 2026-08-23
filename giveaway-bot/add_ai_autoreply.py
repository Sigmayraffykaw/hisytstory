from pathlib import Path
import re

path = Path(__file__).with_name("bot.py")
text = path.read_text(encoding="utf-8")

if "CREATE TABLE IF NOT EXISTS ai_check_config" in text:
    print("AI auto-reply checker is already installed.")
    raise SystemExit

# Persistent config table.
marker = 'conn.execute("""\nCREATE TABLE IF NOT EXISTS giveaways ('
config_table = '''conn.execute("""\nCREATE TABLE IF NOT EXISTS ai_check_config (\n    guild_id INTEGER PRIMARY KEY,\n    channel_id INTEGER NOT NULL\n)\n""")\n\n'''
if marker not in text:
    raise RuntimeError("Could not find database marker")
text = text.replace(marker, config_table + marker, 1)

# Heuristic AI-likeness scorer. This is deliberately probabilistic, not a claim of proof.
helper_marker = 'async def snapshot_invites(guild: discord.Guild) -> dict[str, int]:'
helper_code = '''def ai_likeness_score(content: str) -> tuple[int, list[str]]:\n    text = content.strip()\n    if len(text) < 80:\n        return 0, []\n\n    score = 0\n    reasons = []\n    lower = text.lower()\n    words = re.findall(r"[A-Za-z']+", text)\n    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]\n\n    formal_phrases = [\n        "in conclusion", "furthermore", "moreover", "it is important to note",\n        "overall", "in summary", "on the other hand", "additionally",\n        "this highlights", "this demonstrates", "a key aspect",\n    ]\n    hits = [p for p in formal_phrases if p in lower]\n    if len(hits) >= 2:\n        score += 30\n        reasons.append("many polished transition phrases")\n    elif hits:\n        score += 12\n        reasons.append("formal transition phrasing")\n\n    if len(sentences) >= 4:\n        lengths = [len(re.findall(r"[A-Za-z']+", s)) for s in sentences]\n        avg = sum(lengths) / len(lengths)\n        variance = sum((n - avg) ** 2 for n in lengths) / len(lengths)\n        if 10 <= avg <= 24 and variance < 35:\n            score += 25\n            reasons.append("very even sentence structure")\n\n    if len(words) >= 80:\n        unique_ratio = len(set(w.lower() for w in words)) / max(1, len(words))\n        if 0.45 <= unique_ratio <= 0.7:\n            score += 15\n            reasons.append("consistent vocabulary distribution")\n\n    if text.count(";") >= 2 or text.count(":") >= 3:\n        score += 8\n        reasons.append("highly structured punctuation")\n\n    if re.search(r"(?:^|\\n)\\s*(?:1\\.|2\\.|3\\.|[-•])", text):\n        score += 10\n        reasons.append("structured list formatting")\n\n    if not re.search(r"\\b(?:lol|lmao|idk|imo|ngl|bro|bruh|rn|tbh)\\b", lower) and len(words) > 120:\n        score += 8\n        reasons.append("very polished long-form tone")\n\n    return min(score, 100), reasons\n\n\ndef get_ai_check_channel(guild_id: int) -> int | None:\n    row = conn.execute(\n        "SELECT channel_id FROM ai_check_config WHERE guild_id = ?",\n        (guild_id,),\n    ).fetchone()\n    return int(row[0]) if row else None\n\n\n'''
if helper_marker not in text:
    raise RuntimeError("Could not find helper marker")
text = text.replace(helper_marker, helper_code + helper_marker, 1)

# Hook into existing on_message before command processing.
on_message_marker = '    await bot.process_commands(message)\n'
on_message_code = '''    if message.guild and message.author and not message.author.bot:\n        ai_channel_id = get_ai_check_channel(message.guild.id)\n        if ai_channel_id == message.channel.id and message.content and not message.content.startswith("."):\n            score, reasons = ai_likeness_score(message.content)\n            if score >= 55:\n                reason_text = ", ".join(reasons[:3]) if reasons else "writing-pattern signals"\n                await message.reply(\n                    f"🤖 **AI-writing check:** this looks **possibly AI-written** ({score}/100). "\n                    f"Signals: {reason_text}. This is only an estimate, not proof.",\n                    mention_author=False,\n                )\n\n'''
if on_message_marker not in text:
    raise RuntimeError("Could not find bot.process_commands marker")
text = text.replace(on_message_marker, on_message_code + on_message_marker, 1)

# Add prefix commands before .giveaway.
cmd_marker = '@bot.command(name="giveaway", aliases=["gcreate"])'
cmd_code = '''@bot.command(name="setaicheck")\n@commands.has_guild_permissions(manage_guild=True)\nasync def dot_setaicheck(ctx: commands.Context, channel: discord.TextChannel):\n    if not ctx.guild:\n        return\n    conn.execute(\n        "INSERT OR REPLACE INTO ai_check_config (guild_id, channel_id) VALUES (?, ?)",\n        (ctx.guild.id, channel.id),\n    )\n    conn.commit()\n    await ctx.send(f"🤖 AI-writing auto-check enabled in {channel.mention}.")\n\n\n@bot.command(name="aicheckoff")\n@commands.has_guild_permissions(manage_guild=True)\nasync def dot_aicheckoff(ctx: commands.Context):\n    if not ctx.guild:\n        return\n    conn.execute("DELETE FROM ai_check_config WHERE guild_id = ?", (ctx.guild.id,))\n    conn.commit()\n    await ctx.send("✅ AI-writing auto-check disabled.")\n\n\n@bot.command(name="aicheck")\nasync def dot_aicheck(ctx: commands.Context, *, text_to_check: str):\n    score, reasons = ai_likeness_score(text_to_check)\n    if score >= 55:\n        label = "possibly AI-written"\n    elif score >= 30:\n        label = "unclear / mixed"\n    else:\n        label = "not strongly AI-like"\n    reason_text = ", ".join(reasons[:4]) if reasons else "no strong AI-writing patterns detected"\n    await ctx.send(\n        f"🤖 **AI-writing check:** **{label}** ({score}/100)\\n"\n        f"Signals: {reason_text}\\n"\n        "*This is only an estimate and cannot prove authorship.*"\n    )\n\n\n'''
if cmd_marker not in text:
    raise RuntimeError("Could not find command insertion marker")
text = text.replace(cmd_marker, cmd_code + cmd_marker, 1)

# Add help lines if ghelp block exists.
help_line = '"`.gblacklistcheck @member`"'
help_replacement = '"`.gblacklistcheck @member`\\n"\n        "`.setaicheck #channel` — enable AI-writing auto replies\\n"\n        "`.aicheckoff` — disable AI-writing auto replies\\n"\n        "`.aicheck <text>` — manual AI-writing estimate"'
if help_line in text:
    text = text.replace(help_line, help_replacement, 1)

path.write_text(text, encoding="utf-8")
print("Added configurable AI-writing auto-reply checker to bot.py")
