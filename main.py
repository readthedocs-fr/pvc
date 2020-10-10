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
    bdd[str(guild.id)] = {"main": None, "channels": {}}
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
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def setchannel(ctx):
    content = ctx.message.content.split()
    if len(content) > 1:
        if content[1].isdigit():
            chan = bot.get_channel(int(content[1]))
            if chan:
                if isinstance(chan, discord.VoiceChannel):
                    bdd[str(ctx.guild.id)]['main'] = chan.id
                    await ctx.send("Main channel set.")
                else:
                    await ctx.send("Please use a Vocal channel id.")
            else:
                await ctx.send("Please use a valid id.")
        else:
            await ctx.send("Please use a valid id.")
    else:
        await ctx.send("Please specify a channel id.")
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
        value="**Description:** allows you to change the owner\n**Usage:**: `set owner [mention]`",
        inline=False
    )
    embed.add_field(
        name="__name__",
        value="**Description:** allows you to change the channel's name\n**Usage:**: `set name [name]`",
        inline=False
    )
    embed.add_field(
        name="__places__",
        value="**Description:** allows you to change the number of places in the channel.\n"
              "Take a number between 0 to 99, 0 mean no limit.\n**Usage:**: `set places [int]`",
        inline=False
    )
    embed.add_field(
        name="__public/private__",
        value="**Description:** allows you to define the channel as public or private\n"
              "**Usage:**: `config private` or `set public`",
        inline=False
    )
    embed.add_field(
        name="__help__",
        value="**Description:** Show you this embed\n**Usage:**: `set help`",
        inline=False
    )
    return embed


@bot.command()
async def set(ctx):
    content = ctx.message.content.split()
    voice = ctx.author.voice
    member_id = ctx.author.id
    guild_id = str(ctx.guild.id)
    keywords = ["private", "public", "owner", "places", "name"]
    if voice:
        chan = voice.channel
        voice = str(voice.channel.id)
        if voice in bdd[guild_id]['channels'].keys():
            if member_id == bdd[guild_id]['channels'][voice]["owner"]:
                if len(content) > 1 and content[1] in keywords:
                    if content[1] == 'name' and len(content) > 2:
                        await chan.edit(name=" ".join(content[2:]))
                        await ctx.message.channel.send("Name successfully changed.")
                        bdd[guild_id]['channels'][voice]["name"] = " ".join(content[2:])
                    elif content[1] == "owner" and len(ctx.message.mentions):
                        bdd[guild_id]['channels'][voice]["owner"] = ctx.message.mentions[0].id
                        await ctx.message.channel.send(f"Owner successfully changed to {ctx.message.mentions[0].name}.")
                    elif content[1] == "places":
                        if content[2].isdigit():
                            if 0 <= int(content[2]) < 100:
                                await chan.edit(user_limit=int(content[2]))
                                await ctx.send("Number of places successfully changed.")
                                bdd[guild_id]['channels'][voice]["places"] = int(content[2])
                            else:
                                await ctx.send("Please use a number between 0 and 99.")
                        else:
                            await ctx.send("Please use a number between 0 and 99.")
                    elif content[1] == "public":
                        await chan.set_permissions(ctx.guild.default_role, view_channel=True)
                        await ctx.send("Channel defined as public.")
                        bdd[guild_id]['channels'][voice]["public"] = True
                    else:
                        await chan.set_permissions(ctx.guild.default_role, view_channel=False)
                        await ctx.send("Channel defined as private.")
                        bdd[guild_id]['channels'][voice]["public"] = False
                else:
                    await ctx.send(embed=help_embed(ctx.author))
            else:
                await ctx.send("You don't have permission to do this !")
        else:
            await ctx.send('You must be in your voice channel.')
    else:
        await ctx.send('You must be in your voice channel.')
    update_json(bdd)
    update_bdd(bdd)


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


bot.run(os.environ["BOT_TOKEN"])
