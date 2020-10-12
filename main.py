import discord
from discord.ext import commands
import os
import json

bot = commands.Bot(command_prefix="$")
bot.remove_command('help')


def update_json(db: dict):
    with open("bdd.json", "w") as file:
        json.dump(db, file, indent=4)


def update_bdd(db: dict):
    with open("bdd.json", "r") as file:
        for key, value in json.load(file).items():
            db[key] = value


def get_token():
    with open("config.json", "r") as file:
        return json.load(file)["BOT_TOKEN"]


bdd = {}


@bot.event
async def on_ready():
    update_bdd(bdd)

    print(f"Bot logged as {bot.user.name}")
    for guild in bot.guilds:
        if str(guild.id) not in bdd.keys():
            bdd[str(guild.id)] = {"main": None, "channels": {}}
    game = discord.Game(f"Manage {len(bot.guilds)} servers")
    await bot.change_presence(activity=game)

    update_json(bdd)


@bot.event
async def on_guild_join(guild):
    update_bdd(bdd)

    bdd[str(guild.id)] = {
        "main": None,
        "channels": {}
    }
    game = discord.Game(f"Manage {len(bot.guilds)} servers")
    await bot.change_presence(activity=game)

    update_json(bdd)


@bot.command(name="help")
async def _help(ctx):
    embed = discord.Embed(
        title="Help",
        color=discord.Color(5027441)
    )
    embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=1024")
    embed.add_field(
        name="__help__",
        value="**Description:** Show you this message.\n**Usage:**: `help`",
        inline=False
    )
    embed.add_field(
        name="__setchannel__",
        value="**Description:** allows you to assign a main channel.\n**Usage:**: `setchannel [channel_id]`",
        inline=False
    )
    embed.add_field(
        name="__unsetchannel__",
        value="**Description:** reset the main channel.\n**Usage:**: `unsetchannel`",
        inline=False
    )
    embed.add_field(
        name="__set__",
        value="**Description:** allows you to modify your channel once inside.\n**Usage:**: `set [arg]`",
        inline=False
    )
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def setchannel(ctx):
    content = ctx.message.content.split()

    if len(content) <= 1:
        await ctx.send("Please specify a channel id.")
        return

    if not content[1].isdigit():
        await ctx.send("Please use a valid id.")
        return

    channel = bot.get_channel(int(content[1]))

    if not channel:
        await ctx.send("Please use a valid id.")
        return

    if not isinstance(channel, discord.VoiceChannel):
        await ctx.send("Please use a voice channel id.")
        return

    bdd[str(ctx.guild.id)]['main'] = channel.id
    await ctx.send("Main channel set.")

    update_json(bdd)
    update_bdd(bdd)


@bot.command()
@commands.has_permissions(administrator=True)
async def unsetchannel(ctx):
    bdd[str(ctx.guild.id)]['main'] = None
    await ctx.send("Main channel reset.")

    update_json(bdd)
    update_bdd(bdd)


def help_embed(member):
    embed = discord.Embed(
        title="Setings help",
        color=discord.Color(5027441)
    )
    embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{member.id}/{member.avatar}.png?size=1024")
    embed.add_field(
        name="__owner__",
        value="**Description:** allows you to change the owner\n"
              "**Usage:**: `set owner [mention]`",
        inline=False
    )
    embed.add_field(
        name="__name__",
        value="**Description:** allows you to change the channel's name\n"
              "**Usage:**: `set name [name]`",
        inline=False
    )
    embed.add_field(
        name="__places__",
        value="**Description:** allows you to change the number of places in the channel.\n"
              "Take a number between 0 to 99, 0 mean no limit.\n"
              "**Usage:**: `set places [int]`",
        inline=False
    )
    embed.add_field(
        name="__public/private__",
        value="**Description:** allows you to define the channel as public or private\n"
              "**Usage:**: `set private` or `set public`",
        inline=False
    )
    embed.add_field(
        name="__help__",
        value="**Description:** Show you this embed\n"
              "**Usage:**: `set help`",
        inline=False
    )
    return embed


@bot.group()
async def set(ctx):
    content = ctx.message.content.split()
    voice = ctx.author.voice
    member_id = ctx.author.id
    guild_id = str(ctx.guild.id)
    keywords = ["private", "public", "owner", "places", "name"]

    if not voice:
        await ctx.send('You must be in your voice channel.')
        return

    chan = voice.channel
    voice = str(voice.channel.id)

    if not voice in bdd[guild_id]['channels'].keys():
        await ctx.send('You must be in your voice channel.')
        return

    if member_id != bdd[guild_id]['channels'][voice]["owner"]:
        await ctx.send("You don't have permission to do this !")
        return

    if len(content) <= 1 or content[1] not in keywords:
        await ctx.send(embed=help_embed(ctx.author))
        return

    if content[1] == "name":
    	return

    elif content[1] == "owner" and len(ctx.message.mentions):
        bdd[guild_id]['channels'][voice]["owner"] = ctx.message.mentions[0].id
        await ctx.message.channel.send(f"Owner successfully changed to {ctx.message.mentions[0].name}.")

    elif content[1] == "places":
        if not content[2].isdigit() or not 0 <= int(content[2]) < 100:
            await ctx.send("Please use a number between 0 and 99.")
            return

        places_count = int(content[2])

        await chan.edit(user_limit = places_count)
        await ctx.send("Number of places successfully changed.")
        bdd[guild_id]['channels'][voice]["places"] = places_count

    elif content[1] == "public":
        await chan.set_permissions(ctx.guild.default_role, view_channel=True)
        await ctx.send("Channel defined as public.")
        bdd[guild_id]['channels'][voice]["public"] = True

    else:
        await chan.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.send("Channel defined as private.")
        bdd[guild_id]['channels'][voice]["public"] = False

    update_json(bdd)
    update_bdd(bdd)

@commands.cooldown(1,300,commands.BucketType.member)
@set.command()
async def name(ctx):
    content = ctx.message.content.split()
    voice = ctx.author.voice
    member_id = ctx.author.id
    guild_id = str(ctx.guild.id)
    
    if not voice:
    	return name.reset_cooldown(ctx)

    chan = voice.channel
    voice = str(voice.channel.id)
    
    if not voice in bdd[guild_id]['channels'].keys():
        return name.reset_cooldown(ctx)
    
    if member_id != bdd[guild_id]['channels'][voice]["owner"]:
        return name.reset_cooldown(ctx)
    
    if len(content) > 2:
        await chan.edit(name=" ".join(content[2:]))
        await ctx.message.channel.send("Name successfully changed.")
        bdd[guild_id]['channels'][voice]["name"] = " ".join(content[2:])
    else:
    	return name.reset_cooldown(ctx)
@name.error
async def on_command_error(ctx,error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"You are going too fast ! Please wait {round(error.retry_after)} seconds before retry it.")

# TODO Refactor it
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == bdd[str(member.guild.id)]['main']:
        if (before.channel and before.channel.id != bdd[str(member.guild.id)]['main']) or not before.channel:
            category = bot.get_channel(after.channel.category_id)
            change = await member.guild.create_voice_channel(f"{member.name}'s channel", category=category)
            await member.move_to(change)
            bdd[str(member.guild.id)]["channels"][str(change.id)] = {
                "owner": member.id,
                "name": change.name,
                "public": True,
                "places": 0
            }
    if before.channel and str(before.channel.id) in bdd[str(member.guild.id)]["channels"] \
            and not len(before.channel.members):
        bdd[str(member.guild.id)]['channels'].pop(str(before.channel.id))
        await before.channel.delete(reason='Last member leave')

    update_json(bdd)
    update_bdd(bdd)


# TODO Handle invalid token error in a better way for the user
bot.run(get_token())
