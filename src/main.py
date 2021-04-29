import discord
from discord.ext import commands
import aiosqlite
import asyncio

query2 = """CREATE TABLE IF NOT EXISTS ticket_creation_category (
    guild_id INT(18) PRIMARY KEY,
    category_id INT(18)
);"""

query4 = """CREATE TABLE IF NOT EXISTS ticket_log_channel (
    guild_id INT(18) PRIMARY KEY,
    channel_id INT(18)
);"""

query3 = """CREATE TABLE IF NOT EXISTS user_ticket (
    guild_id INT(18),
    user_id INT(18) PRIMARY KEY,
    channel_id INT(18)
);"""

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "t!", intents = intents)
bot.remove_command("help")

@bot.event
async def on_ready():
    print("The Bot is online")

@bot.command()
async def help(ctx):
    embed = discord.Embed(title = "**Ticket Bot Lol**" , description = "prefix : `t!`" , colour = discord.Colour.blue() , timestamp = ctx.message.created_at)
    embed.add_field(name = "Setup bot :", value = "`t!ticket_setup`", inline = False)
    embed.add_field(name = "Make a new ticket :", value = "`t!report`", inline = False)
    embed.add_field(name = "Add a member :", value = "`t!add_member`", inline = False)
    embed.set_thumbnail(url = bot.user.avatar_url)
    embed.set_footer(text = ctx.guild, icon_url = ctx.guild.icon_url)
    await ctx.send(embed = embed)

@bot.command()
@commands.has_permissions(administrator = True)
async def ticket_setup(ctx):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        embed = discord.Embed(title = "**Bot Setup!**", description = "**Please Mention the category ID for making tickets**", color = discord.Colour.blue(), timestamp = ctx.message.created_at)
        embed.set_footer(text = ctx.guild, icon_url = ctx.guild.icon_url)
        await ctx.send(embed = embed)

        msg = await bot.wait_for('message', timeout=100.0, check=check)

        category_id = int(msg.content)

        query_ticket_setup = f"""INSERT INTO ticket_creation_category(guild_id,category_id)
        VALUES({str(ctx.guild.id)},{str(category_id)})"""

        async with aiosqlite.connect('database.db') as conn:
            await conn.execute(query2)
            await conn.execute(query_ticket_setup)
            await conn.commit()

        embed = discord.Embed(title = "**Bot Setup!**", description = "**Please Mention the channel for ticket logs**", color = discord.Colour.blue(), timestamp = ctx.message.created_at)
        embed.set_footer(text = ctx.guild, icon_url = ctx.guild.icon_url)
        await ctx.send(embed = embed)

        msg2 = await bot.wait_for('message', timeout=100.0, check=check)

        channel = bot.get_channel(int(msg2.content[2:-1]))

        query_ticket_log = f"""INSERT INTO ticket_log_channel(guild_id,channel_id)
        VALUES({str(ctx.guild.id)},{str(channel.id)})"""

        async with aiosqlite.connect('database.db') as conn:
            await conn.execute(query4)
            await conn.execute(query_ticket_log)
            await conn.commit()

        await ctx.send("Setup Complete!")

    except:
        await ctx.send(f"You didnt answer properly in time.")

@ticket_setup.error
async def ticket_setup_error(ctx,error):
    if isinstance(error, commands.MissingPermissions):
        em = discord.Embed(description = ":x: You do not have the permission to use this commmand!", color=discord.Colour.red())
        await ctx.send(embed=em)

@bot.command()
async def report(ctx):
    try:
        ticket_check_query = f"SELECT channel_id FROM user_ticket WHERE user_id = {str(ctx.author.id)};"

        async with aiosqlite.connect("database.db") as conn:
            result4 = await conn.execute(ticket_check_query)
            fetch4 = await result4.fetchone()

        channel = discord.utils.get(ctx.guild.channels , id = fetch4[0])

        em4 = discord.Embed(description = ":x: you already have an active ticket!", color = discord.Color.red())
        await ctx.send(embed = em4)

        await channel.send(f"{ctx.author.mention} the ticket is already active here! Do not create another ticket!")
    
    except:
        new_ticket_query = f"SELECT category_id FROM ticket_creation_category WHERE guild_id = {str(ctx.guild.id)};"
        async with aiosqlite.connect('database.db') as conn:
            result = await conn.execute(new_ticket_query)
            fetch = await result.fetchone()

        category = discord.utils.get(ctx.guild.channels, id = fetch[0])

        overwrites = {
            ctx.author: discord.PermissionOverwrite(read_messages=True),
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }

        channel = await ctx.guild.create_text_channel(name = f"issue - {str(ctx.author.id)}", category = category)
        await channel.edit(overwrites=overwrites)
        await ctx.author.send(f"New ticket created - <#{str(channel.id)}>")

        welcome_embed = discord.Embed(title = f"Welcome {ctx.author.display_name}! Please state your issue" , description = "If you have no issue you may close the ticket by using `t!close`" , color = discord.Colour.green(), timestamp = ctx.message.created_at)
        await channel.send(embed = welcome_embed)

        whose_ticket_query = f"""INSERT INTO user_ticket(guild_id,user_id,channel_id)
        VALUES({str(ctx.guild.id)},{str(ctx.author.id)},{str(channel.id)})"""

        async with aiosqlite.connect('database.db') as conn:
            await conn.execute(query3)
            await conn.execute(whose_ticket_query)
            await conn.commit()

        ticket_log_category_query = f"SELECT channel_id FROM ticket_log_channel WHERE guild_id = {str(ctx.guild.id)};"

        async with aiosqlite.connect('database.db') as conn:
            result2 = await conn.execute(ticket_log_category_query)
            fetch2 = await result2.fetchone()

        channel2 = discord.utils.get(ctx.guild.channels, id = fetch2[0])
        
        em2 = discord.Embed(title = "New Ticket opened", color = discord.Colour.blue(), timestamp = ctx.message.created_at)
        em2.add_field(name = "Command run by :", value = f"`{ctx.author.display_name}`", inline = False)
        em2.add_field(name = "Channel name :", value = f"`#{channel.name}`", inline = False)
        em2.add_field(name = "Action :", value = "`t!report`", inline = False)
        em2.set_thumbnail(url = ctx.author.avatar_url)
        await channel2.send(embed = em2)


@report.error
async def report_error(ctx,error):
    if isinstance(error, commands.CommandInvokeError):
        em = discord.Embed(description = ":x: You have not run the setup! Try `t!ticket_setup`", color=discord.Colour.red())
        await ctx.send(embed=em)

@bot.command()
@commands.has_permissions(administrator = True)
async def add_member(ctx, member : discord.Member = None):
    member_get_query = f"SELECT user_id FROM user_ticket WHERE channel_id = {str(ctx.channel.id)};"
    if member == None:
        em = discord.Embed(description = ":x: You did mention the member", color=discord.Colour.red())
        await ctx.send(embed=em)
    else:
        async with aiosqlite.connect('database.db') as conn:
            result2 = await conn.execute(member_get_query)
            fetch2 = await result2.fetchone()

        member2 = discord.utils.get(ctx.guild.members , id = fetch2[0])

        overwrites = {
            member: discord.PermissionOverwrite(read_messages=True),
            member2: discord.PermissionOverwrite(read_messages=True),
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }

        await ctx.channel.edit(overwrites = overwrites)
        
        em = discord.Embed(description = f":speech_balloon: ***{member.display_name} added in the ticket!***", color = discord.Colour.green())
        await ctx.send(embed = em)

        ticket_log_category_query = f"SELECT channel_id FROM ticket_log_channel WHERE guild_id = {str(ctx.guild.id)};"

        async with aiosqlite.connect('database.db') as conn:
            result3 = await conn.execute(ticket_log_category_query)
            fetch3 = await result3.fetchone()

        channel3 = discord.utils.get(ctx.guild.channels, id = fetch3[0])
        
        em2 = discord.Embed(title = "Member Added", color = discord.Colour.green(), timestamp = ctx.message.created_at)
        em2.add_field(name = "Command run by :", value = f"`{ctx.author.display_name}`", inline = False)
        em2.add_field(name = "Channel name :", value = f"`#{ctx.channel.name}`", inline = False)
        em2.add_field(name = "Action :", value = f"`t!add_member {member.display_name}`", inline = False)
        em2.set_thumbnail(url = ctx.author.avatar_url)
        await channel3.send(embed = em2)

@add_member.error
async def add_member_error(ctx,error):
    if isinstance(error, commands.MemberNotFound):
        em = discord.Embed(description = ":x: User Not Found, try again!", color=discord.Colour.red())
        await ctx.send(embed=em)
    elif isinstance(error, commands.MissingPermissions):
        em = discord.Embed(description = ":x: You do not have the permission to use this commmand!", color=discord.Colour.red())
        await ctx.send(embed=em)
    elif isinstance(error, commands.CommandInvokeError):
        em = discord.Embed(description = ":x: Ticket not found , make one using `t!report`", color=discord.Colour.red())
        await ctx.send(embed=em)


@bot.command()
async def close(ctx):
    member_get_query = f"SELECT user_id FROM user_ticket WHERE channel_id = {str(ctx.channel.id)};"

    async with aiosqlite.connect('database.db') as conn:
        result2 = await conn.execute(member_get_query)
        fetch2 = await result2.fetchone()

    member = discord.utils.get(ctx.guild.members , id = fetch2[0])

    channel_selection_query = f"SELECT channel_id FROM user_ticket WHERE user_id = {str(member.id)};"

    async with aiosqlite.connect('database.db') as conn:
        result = await conn.execute(channel_selection_query)
        fetch = await result.fetchone()

    overwrites = {
        member: discord.PermissionOverwrite(read_messages=False),
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
    }
    channel = bot.get_channel(fetch[0])
    await channel.edit(overwrites = overwrites)

    embed = discord.Embed(title = "Options" , description = "`t!reopen` : to reopen the ticket\n`t!delete` : to delete the ticket\n`t!save` : to save transcript" , color = discord.Colour.green())
    await ctx.send(embed = embed)

    ticket_log_category_query = f"SELECT channel_id FROM ticket_log_channel WHERE guild_id = {str(ctx.guild.id)};"

    async with aiosqlite.connect('database.db') as conn:
        result3 = await conn.execute(ticket_log_category_query)
        fetch3 = await result3.fetchone()

    channel3 = discord.utils.get(ctx.guild.channels, id = fetch3[0])
    
    em2 = discord.Embed(title = "Ticket Closed", color = 0xffff00, timestamp = ctx.message.created_at)
    em2.add_field(name = "Command run by :", value = f"`{ctx.author.display_name}`", inline = False)
    em2.add_field(name = "Channel name :", value = f"`#{ctx.channel.name}`", inline = False)
    em2.add_field(name = "Action :", value = "`t!close`", inline = False)
    em2.set_thumbnail(url = ctx.author.avatar_url)
    await channel3.send(embed = em2)

@close.error
async def close_error(ctx,error):
    if isinstance(error, commands.CommandInvokeError):
        em = discord.Embed(description = ":x: There is nothing to close", color=discord.Colour.red())
        await ctx.send(embed=em)

@bot.command()
@commands.has_permissions(administrator = True)
async def reopen(ctx):
    member_get_query = f"SELECT user_id FROM user_ticket WHERE channel_id = {str(ctx.channel.id)};"

    async with aiosqlite.connect('database.db') as conn:
        result2 = await conn.execute(member_get_query)
        fetch2 = await result2.fetchone()

    member = discord.utils.get(ctx.guild.members , id = fetch2[0])

    channel_selection_query = f"SELECT channel_id FROM user_ticket WHERE user_id = {str(member.id)};"

    async with aiosqlite.connect('database.db') as conn:
        result = await conn.execute(channel_selection_query)
        fetch = await result.fetchone()

    overwrites = {
        member: discord.PermissionOverwrite(read_messages=True),
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
    }

    channel = bot.get_channel(fetch[0])
    await channel.edit(overwrites = overwrites)

    embed = discord.Embed(description = f"***:unlock: Ticket Reopened by {ctx.author.display_name}***" , color = discord.Colour.green())
    await ctx.send(embed = embed)

    ticket_log_category_query = f"SELECT channel_id FROM ticket_log_channel WHERE guild_id = {str(ctx.guild.id)};"

    async with aiosqlite.connect('database.db') as conn:
        result3 = await conn.execute(ticket_log_category_query)
        fetch3 = await result3.fetchone()

    channel3 = discord.utils.get(ctx.guild.channels, id = fetch3[0])
    
    em2 = discord.Embed(title = "Ticket Reopened", color = discord.Colour.green() , timestamp = ctx.message.created_at)
    em2.add_field(name = "Command run by :", value = f"`{ctx.author.display_name}`", inline = False)
    em2.add_field(name = "Channel name :", value = f"`#{ctx.channel.name}`", inline = False)
    em2.add_field(name = "Action :", value = "`t!reopen`", inline = False)
    em2.set_thumbnail(url = ctx.author.avatar_url)
    await channel3.send(embed = em2)

@reopen.error
async def reopen_error(ctx,error):
    if isinstance(error, commands.MissingPermissions):
        em = discord.Embed(description = ":x: You do not have the permission to use this commmand!", color=discord.Colour.red())
        await ctx.send(embed=em)
    elif isinstance(error, commands.CommandInvokeError):
        em = discord.Embed(description = ":x: There is in an error in the data try running `t!ticket_setup`", color=discord.Colour.red())
        await ctx.send(embed=em)

@bot.command()
@commands.has_permissions(administrator = True)
async def delete(ctx):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    member_get_query = f"SELECT user_id FROM user_ticket WHERE channel_id = {str(ctx.channel.id)};"

    async with aiosqlite.connect('database.db') as conn:
        result2 = await conn.execute(member_get_query)
        fetch2 = await result2.fetchone()

    member = discord.utils.get(ctx.guild.members , id = fetch2[0])

    channel_selection_query = f"SELECT channel_id FROM user_ticket WHERE user_id = {str(member.id)};"

    async with aiosqlite.connect('database.db') as conn:
        result = await conn.execute(channel_selection_query)
        fetch = await result.fetchone()

    overwrites = {
        member: discord.PermissionOverwrite(read_messages=False),
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
    }

    channel = bot.get_channel(fetch[0])
    await channel.edit(overwrites = overwrites)

    try:
        embed = discord.Embed(description = "***:no_entry: Are you sure you want to delete this? (N/Y)***" , color = discord.Colour.red())
        await ctx.send(embed = embed)

        possible_yes_answers = ["yes","Yes","y","Y","ye","Ye","Yep","yep","yus","Yus","Yos","yos","Yeah","yeah"]
        possible_no_answers = ["no","No","Nope","nope","n","N","nah","Nah"]

        msg = await bot.wait_for('message', timeout=100.0, check=check)

        if msg.content in possible_yes_answers:
            delete_data_query = f"DELETE FROM user_ticket WHERE channel_id = {str(channel.id)};"
            async with aiosqlite.connect('database.db') as conn:
                await conn.execute(delete_data_query)
                await conn.commit()
            embed2 = discord.Embed(description = ":wastebasket: deleting channel in 5 seconds" , color = discord.Colour.red())
            await ctx.send(embed = embed2)
            await asyncio.sleep(5)
            await channel.delete()

            ticket_log_category_query = f"SELECT channel_id FROM ticket_log_channel WHERE guild_id = {str(ctx.guild.id)};"

            async with aiosqlite.connect('database.db') as conn:
                result3 = await conn.execute(ticket_log_category_query)
                fetch3 = await result3.fetchone()

            channel3 = discord.utils.get(ctx.guild.channels, id = fetch3[0])
            
            em2 = discord.Embed(title = "Ticket Deleted", color = discord.Colour.red() , timestamp = ctx.message.created_at)
            em2.add_field(name = "Command run by :", value = f"`{ctx.author.display_name}`", inline = False)
            em2.add_field(name = "Channel name :", value = f"`#{ctx.channel.name}`", inline = False)
            em2.add_field(name = "Action :", value = "`t!delete`", inline = False)
            em2.set_thumbnail(url = ctx.author.avatar_url)
            await channel3.send(embed = em2)

        elif msg.content in possible_no_answers:
            embed = discord.Embed(title = "Options" , description = "`t!reopen` : to reopen the ticket\n`t!delete` : to delete the ticket\n`t!save` : to save transcript" , color = discord.Colour.green())
            await ctx.send(embed = embed)
        else:
            await ctx.send("The Answer was not proper! Try `t!delete` again!")

    except:
        await ctx.send(f"You didnt answer in time , try again!")

@delete.error
async def delete_error(ctx,error):
    if isinstance(error, commands.MissingPermissions):
        em = discord.Embed(description = ":x: You do not have the permission to use this commmand!", color=discord.Colour.red())
        await ctx.send(embed=em)
    elif isinstance(error, commands.CommandInvokeError):
        em = discord.Embed(description = ":x: There is in an error in the data try running `t!ticket_setup`", color=discord.Colour.red())
        await ctx.send(embed=em)

@bot.command()
@commands.has_permissions(administrator = True)
async def save(ctx):
    ticket_log_category_query = f"SELECT channel_id FROM ticket_log_channel WHERE guild_id = {str(ctx.guild.id)};"

    async with aiosqlite.connect('database.db') as conn:
        result = await conn.execute(ticket_log_category_query)
        fetch = await result.fetchone()

    channel = discord.utils.get(ctx.guild.channels, id = fetch[0])

    with open('logs.txt','w') as f:
        async for message in ctx.channel.history(limit = 500, oldest_first = True):
            embeds = message.embeds
            if embeds == []:
                f.write(f"{message.author.display_name} : {str(message.content)}\n")
            else:
                for embed in embeds:
                    f.write(f"{message.author.display_name} : {str(embed.to_dict())}\n")
    
    await channel.send(file=discord.File('logs.txt'))

    with open('logs.txt','w') as f:
        f.truncate(0)
        f.close()

    em = discord.Embed(description = "***:bookmark_tabs: Saved transcript succesfully***" , color = discord.Colour.green())
    await ctx.send(embed = em)

    member_get_query = f"SELECT user_id FROM user_ticket WHERE channel_id = {str(ctx.channel.id)};"

    async with aiosqlite.connect('database.db') as conn:
        result5 = await conn.execute(member_get_query)
        fetch5 = await result5.fetchone()

    member = discord.utils.get(ctx.guild.members , id = fetch5[0])

    channel_selection_query = f"SELECT channel_id FROM user_ticket WHERE user_id = {str(member.id)};"

    async with aiosqlite.connect('database.db') as conn:
        result4 = await conn.execute(channel_selection_query)
        fetch4 = await result4.fetchone()

    channel2 = bot.get_channel(fetch4[0])

    delete_data_query = f"DELETE FROM user_ticket WHERE channel_id = {str(channel2.id)};"
    async with aiosqlite.connect('database.db') as conn:
        await conn.execute(delete_data_query)
        await conn.commit()

    embed2 = discord.Embed(description = ":wastebasket: deleting channel in 5 seconds" , color = discord.Colour.red())
    await ctx.send(embed = embed2)
    await asyncio.sleep(5)
    await ctx.channel.delete()

    ticket_log_category_query2 = f"SELECT channel_id FROM ticket_log_channel WHERE guild_id = {str(ctx.guild.id)};"

    async with aiosqlite.connect('database.db') as conn:
        result3 = await conn.execute(ticket_log_category_query2)
        fetch3 = await result3.fetchone()

    channel3 = discord.utils.get(ctx.guild.channels, id = fetch3[0])
    
    em2 = discord.Embed(title = "Transcript saved", color = 0x800080 , timestamp = ctx.message.created_at)
    em2.add_field(name = "Command run by :", value = f"`{ctx.author.display_name}`", inline = False)
    em2.add_field(name = "Channel name :", value = f"`#{ctx.channel.name}`", inline = False)
    em2.add_field(name = "Action :", value = "`t!save`", inline = False)
    em2.set_thumbnail(url = ctx.author.avatar_url)
    await channel3.send(embed = em2)

@save.error
async def save_error(ctx,error):
    if isinstance(error, commands.MissingPermissions):
        em = discord.Embed(description = ":x: You do not have the permission to use this commmand!", color=discord.Colour.red())
        await ctx.send(embed=em)
    elif isinstance(error, commands.CommandInvokeError):
        em = discord.Embed(description = ":x: There is in an error in the data try running `t!ticket_setup`", color=discord.Colour.red())
        await ctx.send(embed=em)

bot.run("your bot token here")
