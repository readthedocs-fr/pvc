import discord
from discord.ext import commands
import json
import os, sys
import logging


PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(PATH, "data.json")
CONFIG_PATH = os.path.join(PATH, "config.json")
LOG_PATH = os.path.join(PATH, ".logs")

data = {}
bot = commands.Bot(command_prefix="$", help_command=None)

logger = logging.getLogger("pvc bot")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(LOG_PATH, "a")
file_handler.setFormatter(logging.Formatter(r"%(asctime)s - [%(levelname)s] ~ %(message)s"))
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter(r"[%(levelname)s] ~ %(message)s"))
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def format_time(t: int):
    minutes, seconds = divmod(t, 60)
    if minutes:
        return f"You are going too fast ! Please wait {minutes} minutes and {seconds} seconds before retry it."
    return f"You are going too fast ! Please wait {seconds} seconds before retry it."


def update_json(db: dict):
    with open(DATA_PATH, "w") as file:
        json.dump(db, file, indent=4)


def update_data(data: dict):
    with open(DATA_PATH, "r") as file:
        for key, value in json.load(file).items():
            data[key] = value


def get_token():
    with open(CONFIG_PATH, "r") as file:
        return json.load(file)["BOT_TOKEN"]


@bot.event
async def on_ready():
    update_data(data)

    logger.info(f"Bot logged as {bot.user.name}")
    for guild in bot.guilds:
        if str(guild.id) not in data.keys():
            data[str(guild.id)] = {"main": None, "channels": {}}
    game = discord.Game(f"Manage {len(bot.guilds)} servers")
    await bot.change_presence(activity=game)

    update_json(data)


@bot.event
async def on_guild_join(guild):
    update_data(data)

    data[str(guild.id)] = {
        "main": None,
        "channels": {}
    }
    game = discord.Game(f"Manage {len(bot.guilds)} servers")
    await bot.change_presence(activity=game)

    update_json(data)


@bot.event
async def on_guild_remove(guild):
    update_data(data)

    del data[str(guild.id)]
    game = discord.Game(f"Manage {len(bot.guilds)} servers")
    await bot.change_presence(activity=game)

    update_json(data)


@bot.event
async def on_error(event, *args, **kwargs):
    logger.warning(f"Ignoring discord error {event}")

@bot.event
async def on_command_error(ctx, error):
    logger.warning(f"Ignoring discord error: {error}")


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

    if data[str(ctx.guild.id)]["main"] is not None:
        logger.warning(f"Channel already set {data[str(ctx.guild.id)]['main']}.")
    logger.info(f"Set main channel <{channel.name}.{channel.id}>")

    data[str(ctx.guild.id)]['main'] = channel.id
    await ctx.send("Main channel set.")

    update_json(data)
    update_data(data)


@bot.command()
@commands.has_permissions(administrator=True)
async def unsetchannel(ctx):
    data[str(ctx.guild.id)]['main'] = None
    await ctx.send("Main channel reset.")

    logger.info("Main channel reset.")

    update_json(data)
    update_data(data)


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


@bot.group(name="set")
async def _set(ctx):
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

    if not voice in data[guild_id]['channels'].keys():
        await ctx.send('You must be in your voice channel.')
        return

    if member_id != data[guild_id]['channels'][voice]["owner"]:
        await ctx.send("You don't have permission to do this !")
        return

    if len(content) <= 1 or content[1] not in keywords:
        await ctx.send(embed=help_embed(ctx.author))
        return

    if content[1] == "name":
        return

    elif content[1] == "owner" and len(ctx.message.mentions):
        data[guild_id]['channels'][voice]["owner"] = ctx.message.mentions[0].id
        await ctx.message.channel.send(f"Owner successfully changed to {ctx.message.mentions[0].name}.")

    elif content[1] == "places":
        if not content[2].isdigit() or not 0 <= int(content[2]) < 100:
            await ctx.send("Please use a number between 0 and 99.")
            return

        places_count = int(content[2])

        await chan.edit(user_limit=places_count)
        await ctx.send("Number of places successfully changed.")
        data[guild_id]['channels'][voice]["places"] = places_count

    elif content[1] == "public":
        await chan.set_permissions(ctx.guild.default_role, view_channel=True)
        await ctx.send("Channel defined as public.")
        data[guild_id]['channels'][voice]["public"] = True

    else:
        await chan.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.send("Channel defined as private.")
        data[guild_id]['channels'][voice]["public"] = False

    update_json(data)
    update_data(data)


@commands.cooldown(1, 300, commands.BucketType.member)
@_set.command()
async def name(ctx):
    content = ctx.message.content.split()
    voice = ctx.author.voice
    member_id = ctx.author.id
    guild_id = str(ctx.guild.id)

    if not voice:
        return name.reset_cooldown(ctx)

    chan = voice.channel
    voice = str(voice.channel.id)

    if not voice in data[guild_id]['channels'].keys():
        return name.reset_cooldown(ctx)

    if member_id != data[guild_id]['channels'][voice]["owner"]:
        return name.reset_cooldown(ctx)

    if len(content) > 2:
        await chan.edit(name=" ".join(content[2:]))
        await ctx.message.channel.send("Name successfully changed.")
        data[guild_id]['channels'][voice]["name"] = " ".join(content[2:])
    else:
        return name.reset_cooldown(ctx)


@name.error
async def on_command_error(ctx, error):
    logger.error(f"Error occured: {error}")
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(format_time(round(error.retry_after)))


@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == data[str(member.guild.id)]['main']: # if the user connects to the set voice channel...
        category = bot.get_channel(after.channel.category_id)
        # create a new channel, named after the member name, and move the member to it
        change = await member.guild.create_voice_channel(f"{member.name}'s channel", category=category)
        await member.move_to(change)

        logger.info(f"{member.name} joined and was moved to \"{member.name}'s channel\"")
        # update the data
        data[str(member.guild.id)]["channels"][str(change.id)] = {
            "owner": member.id,
            "name": change.name,
            "public": True,
            "places": 0
        }
    if before.channel and str(before.channel.id) in data[str(member.guild.id)]["channels"]: # if the user disconnects from a personnal voice channel
        if not len(before.channel.members): # if there is no more users in the voice channel, delete it
            data[str(member.guild.id)]['channels'].pop(str(before.channel.id))
            await before.channel.delete(reason='Last member leave')
            logger.info(f"Personnal voice channel \"{before.channel.name}\" is empty so it has been deleted.")

    update_json(data)
    update_data(data)


try:
    bot.run(get_token())
except discord.errors.LoginFailure:
    logger.error("Could not connect: invalid token error.")