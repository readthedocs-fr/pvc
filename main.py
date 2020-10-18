import discord
from discord.ext import commands
from cogs.set_channel import SetChannel
from cogs.config_channel import ConfigChannel
import json
import os
import sys
from utils import update_json, update_data, create_logger, help_embed


PATH = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(PATH, "config.json")

data = {}
bot = commands.Bot(command_prefix="!", help_command=None)

logger = create_logger()


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
    logger.warning(f"Ignoring discord error {event}: \"{sys.exc_info()[1]}\"")


@bot.event
async def on_command_error(ctx, error):
    logger.warning(f"Ignoring discord error: {error}")


@bot.command(name="help")
async def _help(ctx):
    await ctx.send(embed=help_embed)


@bot.event
async def on_voice_state_update(member, before, after):
    # if the user connects to the set voice channel...
    if after.channel and after.channel.id == data[str(member.guild.id)]['main']:
        category = bot.get_channel(after.channel.category_id)
        # create a new channel, named after the member name, set permissions, and move the member to it
        overwrite = discord.PermissionOverwrite(manage_permissions=True, connect=True,
                                                manage_channels=True, view_channel=True, move_members=True)
        change = await member.guild.create_voice_channel(f"{member.name}'s channel",
                                                         overwrites={bot.user: overwrite}, category=category)
        await change.set_permissions(member, view_channel=True, connect=True)
        await member.move_to(change)

        logger.info(f"{member.name} joined and was moved to \"{member.name}'s channel\"")
        # update the data
        data[str(member.guild.id)]["channels"][str(change.id)] = member.id

    # if the user disconnects from a personnal voice channel
    if before.channel and str(before.channel.id) in data[str(member.guild.id)]["channels"]:
        if not len(before.channel.members):  # if there is no more users in the voice channel, delete it
            data[str(member.guild.id)]['channels'].pop(str(before.channel.id))
            await before.channel.delete(reason='Last member leave')
            logger.info(f"Personnal voice channel \"{before.channel.name}\" is empty so it has been deleted.")

    update_json(data)
    update_data(data)


bot.add_cog(SetChannel(bot, data, logger))
bot.add_cog(ConfigChannel(bot, data, logger))

try:
    bot.run(get_token())
except discord.errors.LoginFailure:
    logger.error("Could not connect: invalid token error.")
