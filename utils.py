import json
import os
import sys
import logging
import discord

PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(PATH, "data.json")
LOG_PATH = os.path.join(PATH, ".logs")


def update_json(data: dict):
    with open(DATA_PATH, "w") as file:
        json.dump(data, file, indent=4)


def update_data(data: dict):
    with open(DATA_PATH, "r") as file:
        for key, value in json.load(file).items():
            data[key] = value


def create_logger():
    logger = logging.getLogger("pvc bot")
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(LOG_PATH, "a")
    file_handler.setFormatter(logging.Formatter(r"%(asctime)s - [%(levelname)s] ~ %(message)s"))
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(r"[%(levelname)s] ~ %(message)s"))
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def config_help_embed(member):
    embed = discord.Embed(
        title="Settings help",
        color=discord.Color(5027441)
    )
    embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{member.id}/{member.avatar}.png?size=1024")
    embed.add_field(
        name="__owner__",
        value="**Description:** allows you to change the owner\n"
              "**Usage**: `set owner [mention]`",
        inline=False
    )
    embed.add_field(
        name="__name__",
        value="**Description:** allows you to change the channel's name\n"
              "**Usage**: `set name [name]`",
        inline=False
    )
    embed.add_field(
        name="__places__",
        value="**Description:** allows you to change the number of places in the channel.\n"
              "Take a number between 0 to 99, 0 mean no limit.\n"
              "**Usage**: `set places [int]`",
        inline=False
    )
    embed.add_field(
        name="__public/private__",
        value="**Description:** allows you to define the channel as public or private\n"
              "**Usage**: `set private` or `set public`",
        inline=False
    )
    embed.add_field(
        name="__hide/reveal__",
        value="**Description:** allows you to define the channel as hidden or visible\n"
              "**Usage**: `set hide` or `set reveal`",
        inline=False
    )
    embed.add_field(
        name="__invite/kick__",
        value="**Description:** allows you to invite or kick somebody from the channel\n"
              "**Usage**: `set invite [mention]` or `set kick [mention]`",
        inline=False
    )
    embed.add_field(
        name="__help__",
        value="**Description:** Show you this embed\n"
              "**Usage**: `set help`",
        inline=False
    )
    return embed


def help_embed(bot):
    embed = discord.Embed(
        title="Help",
        color=discord.Color(5027441)
    )
    embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=1024")
    embed.add_field(
        name="__help__",
        value="**Description:** Show you this message.\n**Usage**: `help`",
        inline=False
    )
    embed.add_field(
        name="__setchannel__",
        value="**Description:** allows you to assign a main channel.\n**Usage**: `setchannel [channel_id]`",
        inline=False
    )
    embed.add_field(
        name="__unsetchannel__",
        value="**Description:** reset the main channel.\n**Usage**: `unsetchannel`",
        inline=False
    )
    embed.add_field(
        name="__set__",
        value="**Description:** allows you to modify your channel once inside.\n**Usage**: `set [arg]`",
        inline=False
    )
    return embed
