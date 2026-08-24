from pathlib import Path

path = Path(__file__).with_name("bot.py")
text = path.read_text(encoding="utf-8")

if '@bot.command(name="boosterperks")' in text:
    print("Booster perks commands are already installed.")
    raise SystemExit

slash_marker = '# ---------------- Dot commands ----------------'
slash_code = '''@bot.tree.command(name="booster_perks", description="Post the server booster perks embed")
@app_commands.checks.has_permissions(manage_guild=True)
async def booster_perks(
    interaction: discord.Interaction,
    booster_role: discord.Role,
    chat_channel: discord.TextChannel | None = None,
):
    embed = discord.Embed(
        title="💎 Server Booster Benefits",
        description=(
            "**Thank you to all members who support our server!**\\n"
            "As a Server Booster, you gain access to exclusive benefits:\\n\\n"
            f"• **Exclusive Booster Role:** {booster_role.mention}\\n"
            "A special role with a unique appearance on the server\\n\\n"
            "• **Image Permissions:** Permission to send images\\n\\n"
            "• **GIF Permissions:** Permission to send GIFs\\n\\n"
            "• **Exclusive Role Color & Icon:** A unique color & icon for your booster role\\n\\n"
            "• **Reactions:** Ability to add reactions to messages\\n\\n"
            "• **Set Voice Channel Status:** Ability to set the status of the voice channel\\n\\n"
            "• **Use External Sounds:** Ability to use external sounds on the server\\n\\n"
            "• **Create Polls:** Permission to create polls on the server\\n\\n"
            "• **Nickname Changes:** Ability to change your nickname"
        ),
        color=discord.Color.from_rgb(255, 85, 200),
    )
    embed.set_footer(text="Thanks for supporting the server 💎")

    view = None
    if chat_channel:
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="Go to chat",
            style=discord.ButtonStyle.link,
            url=f"https://discord.com/channels/{interaction.guild_id}/{chat_channel.id}",
            emoji="➡️",
        ))

    await interaction.response.send_message("Posting booster perks...", ephemeral=True)
    msg = await interaction.channel.send(embed=embed, view=view)
    for emoji in ["💎", "🔥", "😭", "🤓", "👍"]:
        try:
            await msg.add_reaction(emoji)
        except discord.HTTPException:
            pass
    await interaction.edit_original_response(content=f"✅ Booster perks posted: {msg.jump_url}")


'''
if slash_marker not in text:
    raise RuntimeError("Could not find dot-command section")
text = text.replace(slash_marker, slash_code + slash_marker, 1)

dot_marker = '@bot.command(name="ghelp", aliases=["giveawayhelp"])'
dot_code = '''@bot.command(name="boosterperks")
@commands.has_guild_permissions(manage_guild=True)
async def dot_booster_perks(ctx: commands.Context, booster_role: discord.Role, chat_channel: discord.TextChannel | None = None):
    embed = discord.Embed(
        title="💎 Server Booster Benefits",
        description=(
            "**Thank you to all members who support our server!**\\n"
            "As a Server Booster, you gain access to exclusive benefits:\\n\\n"
            f"• **Exclusive Booster Role:** {booster_role.mention}\\n"
            "A special role with a unique appearance on the server\\n\\n"
            "• **Image Permissions:** Permission to send images\\n\\n"
            "• **GIF Permissions:** Permission to send GIFs\\n\\n"
            "• **Exclusive Role Color & Icon:** A unique color & icon for your booster role\\n\\n"
            "• **Reactions:** Ability to add reactions to messages\\n\\n"
            "• **Set Voice Channel Status:** Ability to set the status of the voice channel\\n\\n"
            "• **Use External Sounds:** Ability to use external sounds on the server\\n\\n"
            "• **Create Polls:** Permission to create polls on the server\\n\\n"
            "• **Nickname Changes:** Ability to change your nickname"
        ),
        color=discord.Color.from_rgb(255, 85, 200),
    )
    embed.set_footer(text="Thanks for supporting the server 💎")

    view = None
    if chat_channel:
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="Go to chat",
            style=discord.ButtonStyle.link,
            url=f"https://discord.com/channels/{ctx.guild.id}/{chat_channel.id}",
            emoji="➡️",
        ))

    msg = await ctx.send(embed=embed, view=view)
    for emoji in ["💎", "🔥", "😭", "🤓", "👍"]:
        try:
            await msg.add_reaction(emoji)
        except discord.HTTPException:
            pass


'''
if dot_marker not in text:
    raise RuntimeError("Could not find ghelp command")
text = text.replace(dot_marker, dot_code + dot_marker, 1)

help_marker = 'embed.description = ('
idx = text.find(help_marker)
if idx != -1:
    insert_at = text.find('\n', idx) + 1
    text = text[:insert_at] + '        "`.boosterperks @BoosterRole [#chat]` — post booster perks\\n"\n' + text[insert_at:]

path.write_text(text, encoding="utf-8")
print("Added .boosterperks and /booster_perks to bot.py")
