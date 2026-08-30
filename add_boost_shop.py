from pathlib import Path

root = Path(__file__).resolve().parent
bot_path = root / 'bot.py'
module_path = root / 'boost_shop.py'

module_code = r'''import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

PAGE_SIZE = 5

def setup_boost_shop(bot: commands.Bot, conn: sqlite3.Connection):
    conn.execute("CREATE TABLE IF NOT EXISTS boost_shop_config (guild_id INTEGER PRIMARY KEY, booster_role_id INTEGER NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS boost_shop_roles (guild_id INTEGER NOT NULL, role_id INTEGER NOT NULL, category TEXT NOT NULL, emoji TEXT, position INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (guild_id, role_id))")
    conn.commit()

    def booster_role_id(gid):
        r = conn.execute("SELECT booster_role_id FROM boost_shop_config WHERE guild_id=?", (gid,)).fetchone()
        return int(r[0]) if r else None

    def categories_for(gid):
        return [r[0] for r in conn.execute("SELECT category, MIN(position) FROM boost_shop_roles WHERE guild_id=? GROUP BY category ORDER BY MIN(position), category COLLATE NOCASE", (gid,)).fetchall()]

    def roles_for(gid, category):
        return conn.execute("SELECT role_id, emoji FROM boost_shop_roles WHERE guild_id=? AND category=? ORDER BY position, role_id", (gid, category)).fetchall()

    def shop_ids(gid):
        return {int(r[0]) for r in conn.execute("SELECT role_id FROM boost_shop_roles WHERE guild_id=?", (gid,)).fetchall()}

    def has_booster(member):
        rid = booster_role_id(member.guild.id)
        return bool(rid and member.get_role(rid))

    class Claim(discord.ui.Button):
        def __init__(self, role, row):
            super().__init__(label=f"🎁 Get {role.name[:60]}", style=discord.ButtonStyle.success, row=row)
            self.role_id = role.id
        async def callback(self, interaction):
            view = self.view
            if interaction.user.id != view.user_id:
                return await interaction.response.send_message("This shop session belongs to someone else.", ephemeral=True)
            if not isinstance(interaction.user, discord.Member) or not has_booster(interaction.user):
                return await interaction.response.send_message("💎 You need the server booster role.", ephemeral=True)
            role = interaction.guild.get_role(self.role_id)
            me = interaction.guild.me
            if not role:
                return await interaction.response.send_message("That role no longer exists.", ephemeral=True)
            if not me or role >= me.top_role:
                return await interaction.response.send_message("Move my bot role above the shop roles first.", ephemeral=True)
            old = [r for r in interaction.user.roles if r.id in shop_ids(interaction.guild_id) and r.id != role.id and r < me.top_role]
            try:
                if old:
                    await interaction.user.remove_roles(*old, reason="Booster shop switch")
                await interaction.user.add_roles(role, reason="Booster shop claim")
            except discord.Forbidden:
                return await interaction.response.send_message("I can't manage that role.", ephemeral=True)
            await interaction.response.send_message(f"✅ You now have {role.mention}.", ephemeral=True)

    class CatSelect(discord.ui.Select):
        def __init__(self, shop):
            cats = categories_for(shop.guild_id)
            super().__init__(placeholder="Choose a category", options=[discord.SelectOption(label=c[:100], value=c, default=(c==shop.category)) for c in cats[:25]], row=0)
        async def callback(self, interaction):
            v = self.view
            if interaction.user.id != v.user_id:
                return await interaction.response.send_message("This shop session belongs to someone else.", ephemeral=True)
            v.category = self.values[0]
            v.page = 0
            v.rebuild(interaction.guild)
            await interaction.response.edit_message(embed=v.make_embed(interaction.guild), view=v)

    class Nav(discord.ui.Button):
        def __init__(self, label, action, disabled=False):
            super().__init__(label=label, emoji={'prev':'◀️','home':'🏠','next':'▶️'}[action], style=discord.ButtonStyle.secondary, row=4, disabled=disabled)
            self.action = action
        async def callback(self, interaction):
            v = self.view
            if interaction.user.id != v.user_id:
                return await interaction.response.send_message("This shop session belongs to someone else.", ephemeral=True)
            if self.action == 'prev': v.page = max(0, v.page-1)
            elif self.action == 'next': v.page += 1
            else:
                cats = categories_for(v.guild_id)
                v.category = cats[0] if cats else None
                v.page = 0
            v.rebuild(interaction.guild)
            await interaction.response.edit_message(embed=v.make_embed(interaction.guild), view=v)

    class ShopView(discord.ui.View):
        def __init__(self, guild, user_id):
            super().__init__(timeout=300)
            self.guild_id = guild.id
            self.user_id = user_id
            cats = categories_for(guild.id)
            self.category = cats[0] if cats else None
            self.page = 0
            self.rebuild(guild)
        def make_embed(self, guild):
            cats = categories_for(guild.id)
            if not cats:
                return discord.Embed(title="⭐ Booster Role Shop ⭐", description="No shop roles have been added yet.", color=discord.Color.from_rgb(255,95,210))
            if self.category not in cats: self.category = cats[0]
            rows = roles_for(guild.id, self.category)
            total = max(1, (len(rows)+PAGE_SIZE-1)//PAGE_SIZE)
            self.page = max(0, min(self.page, total-1))
            lines=[]
            for role_id, emoji in rows[self.page*PAGE_SIZE:(self.page+1)*PAGE_SIZE]:
                role = guild.get_role(int(role_id))
                if role: lines.append(f"{emoji or '💎'} {role.mention} — **FREE**")
            e=discord.Embed(title="⭐ Booster Role Shop ⭐", description=f"**{self.category} • Page {self.page+1} of {total}**\n\n" + ("\n\n".join(lines) if lines else "No roles on this page."), color=discord.Color.from_rgb(255,95,210))
            e.set_footer(text="Boost the server to unlock these roles • one shop role at a time")
            return e
        def rebuild(self, guild):
            self.clear_items()
            cats=categories_for(guild.id)
            if not cats: return
            if self.category not in cats: self.category=cats[0]
            self.add_item(CatSelect(self))
            rows=roles_for(guild.id,self.category)
            total=max(1,(len(rows)+PAGE_SIZE-1)//PAGE_SIZE)
            self.page=max(0,min(self.page,total-1))
            for i,(rid,_) in enumerate(rows[self.page*PAGE_SIZE:(self.page+1)*PAGE_SIZE]):
                role=guild.get_role(int(rid))
                if role: self.add_item(Claim(role,1+i//2))
            self.add_item(Nav('Prev','prev',self.page<=0))
            self.add_item(Nav('Home','home'))
            self.add_item(Nav('Next','next',self.page>=total-1))

    class OpenView(discord.ui.View):
        def __init__(self): super().__init__(timeout=120)
        @discord.ui.button(label="Open Booster Role Shop", emoji="⭐", style=discord.ButtonStyle.primary)
        async def open_shop(self, interaction, button):
            if not isinstance(interaction.user, discord.Member) or not has_booster(interaction.user):
                return await interaction.response.send_message("💎 You need the server booster role.", ephemeral=True)
            v=ShopView(interaction.guild,interaction.user.id)
            await interaction.response.send_message(embed=v.make_embed(interaction.guild),view=v,ephemeral=True)

    @bot.tree.command(name="boostshop", description="Open the private booster role shop")
    async def slash_shop(interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Use this in a server.", ephemeral=True)
        if not booster_role_id(interaction.guild_id):
            return await interaction.response.send_message("The booster shop has not been configured yet.", ephemeral=True)
        if not has_booster(interaction.user):
            return await interaction.response.send_message("💎 You need the server booster role.", ephemeral=True)
        v=ShopView(interaction.guild,interaction.user.id)
        await interaction.response.send_message(embed=v.make_embed(interaction.guild),view=v,ephemeral=True)

    @bot.tree.command(name="boostshop_setup", description="Set the booster role required for the shop")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def slash_setup(interaction: discord.Interaction, booster_role: discord.Role):
        conn.execute("INSERT INTO boost_shop_config (guild_id,booster_role_id) VALUES (?,?) ON CONFLICT(guild_id) DO UPDATE SET booster_role_id=excluded.booster_role_id",(interaction.guild_id,booster_role.id)); conn.commit()
        await interaction.response.send_message(f"✅ Booster role set to {booster_role.mention}.",ephemeral=True)

    @bot.tree.command(name="boostshop_add", description="Add a role to the booster shop")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def slash_add(interaction: discord.Interaction, category: str, role: discord.Role, emoji: str="💎"):
        pos=conn.execute("SELECT COALESCE(MAX(position),0) FROM boost_shop_roles WHERE guild_id=?",(interaction.guild_id,)).fetchone()[0]
        conn.execute("INSERT INTO boost_shop_roles (guild_id,role_id,category,emoji,position) VALUES (?,?,?,?,?) ON CONFLICT(guild_id,role_id) DO UPDATE SET category=excluded.category,emoji=excluded.emoji",(interaction.guild_id,role.id,category[:80],emoji[:20],int(pos)+1)); conn.commit()
        await interaction.response.send_message(f"✅ Added {role.mention} to **{category}**.",ephemeral=True)

    @bot.tree.command(name="boostshop_remove", description="Remove a role from the booster shop")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def slash_remove(interaction: discord.Interaction, role: discord.Role):
        conn.execute("DELETE FROM boost_shop_roles WHERE guild_id=? AND role_id=?",(interaction.guild_id,role.id)); conn.commit()
        await interaction.response.send_message(f"✅ Removed {role.mention}.",ephemeral=True)

    @bot.command(name="boostshop")
    async def prefix_shop(ctx):
        if ctx.guild: await ctx.send("⭐ **Booster Role Shop**",view=OpenView(),delete_after=120)

    @bot.command(name="boostshopsetup")
    @commands.has_guild_permissions(manage_guild=True)
    async def prefix_setup(ctx, booster_role: discord.Role):
        conn.execute("INSERT INTO boost_shop_config (guild_id,booster_role_id) VALUES (?,?) ON CONFLICT(guild_id) DO UPDATE SET booster_role_id=excluded.booster_role_id",(ctx.guild.id,booster_role.id)); conn.commit()
        await ctx.send(f"✅ Booster role set to {booster_role.mention}.")

    @bot.command(name="boostshopadd")
    @commands.has_guild_permissions(manage_guild=True)
    async def prefix_add(ctx, category: str, role: discord.Role, emoji: str="💎"):
        pos=conn.execute("SELECT COALESCE(MAX(position),0) FROM boost_shop_roles WHERE guild_id=?",(ctx.guild.id,)).fetchone()[0]
        conn.execute("INSERT INTO boost_shop_roles (guild_id,role_id,category,emoji,position) VALUES (?,?,?,?,?) ON CONFLICT(guild_id,role_id) DO UPDATE SET category=excluded.category,emoji=excluded.emoji",(ctx.guild.id,role.id,category[:80],emoji[:20],int(pos)+1)); conn.commit()
        await ctx.send(f"✅ Added {role.mention} to **{category}**.")

    @bot.command(name="boostshopremove")
    @commands.has_guild_permissions(manage_guild=True)
    async def prefix_remove(ctx, role: discord.Role):
        conn.execute("DELETE FROM boost_shop_roles WHERE guild_id=? AND role_id=?",(ctx.guild.id,role.id)); conn.commit()
        await ctx.send(f"✅ Removed {role.mention}.")

    @bot.command(name="boostshoplist")
    async def prefix_list(ctx):
        if not ctx.guild: return
        cats=categories_for(ctx.guild.id)
        if not cats: return await ctx.send("No booster shop roles configured.")
        parts=[]
        for cat in cats:
            names=[]
            for rid,emoji in roles_for(ctx.guild.id,cat):
                role=ctx.guild.get_role(int(rid))
                if role: names.append(f"{emoji or '💎'} {role.mention}")
            parts.append(f"**{cat}**\n"+(" • ".join(names) if names else "None"))
        await ctx.send(("\n\n".join(parts))[:1900])
'''

module_path.write_text(module_code, encoding='utf-8')
text = bot_path.read_text(encoding='utf-8')
if 'from boost_shop import setup_boost_shop' not in text:
    text = text.replace('from dotenv import load_dotenv', 'from dotenv import load_dotenv\nfrom boost_shop import setup_boost_shop', 1)
if 'setup_boost_shop(bot, conn)' not in text:
    marker = 'invite_cache: dict[int, dict[str, int]] = {}'
    if marker not in text:
        raise RuntimeError('Could not find invite_cache marker in bot.py')
    text = text.replace(marker, 'setup_boost_shop(bot, conn)\n\n' + marker, 1)
bot_path.write_text(text, encoding='utf-8')
print('Installed Booster Role Shop successfully.')
print('Restart with: py -3.13 bot.py')
