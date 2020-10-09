from discord.ext import commands
import discord
import os
import json

bot = commands.Bot(command_prefix="%")


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


@bot.command()
async def setchannel(ctx):
    content = ctx.message.content.split()
    if not bdd[str(ctx.guild.id)]['main']:
        if len(content) > 1:
            if content[1].isdigit():
                chan = bot.get_channel(int(content[1]))
                if chan:
                    bdd[str(ctx.guild.id)]['main'] = chan.id
                    await ctx.send("Channel principal configuré.")
                else:
                    await ctx.send("Veuillez envoyer une id valide.")
            else:
                await ctx.send("Veuillez envoyer une id valide.")
        else:
            await ctx.send("Veuillez spécifier un channel id.")
    update_json(bdd)
    update_bdd(bdd)


def help_embed(member):
    embed = discord.Embed(
        title="Config help",
        color=discord.Color(5027441)
        # f"https://cdn.discordapp.com/avatars/{member.id}/{member.avatar}.png?size=1024"
    )
    embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=1024")
    embed.add_field(
        name="__owner__",
        value="**Description:** allows you to change the owner\n**Usage:**: `config owner [mention]`",
        inline=False
    )
    embed.add_field(
        name="__name__",
        value="**Description:** allows you to change the channel's name\n**Usage:**: `config name [name]`",
        inline=False
    )
    embed.add_field(
        name="__places__",
        value="**Description:** allows you to change the number of places in the channel. "
              "Take a number between 0 to 99, 0 mean no limit.\n**Usage:**: `config places [int]`",
        inline=False
    )
    embed.add_field(
        name="__public/private__",
        value="**Description:** allows you to define the channel as public or private\n"
              "**Usage:**: `config private` or `config public`",
        inline=False
    )
    embed.add_field(
        name="__help__",
        value="**Description:** Show you this embed\n**Usage:**: `config help`",
        inline=False
    )
    return embed


@bot.command()
async def config(ctx):
    content = ctx.message.content.split()
    voice = ctx.author.voice
    member_id = ctx.author.id
    guild_id = str(ctx.guild.id)
    keywords = ["private", "public", "owner", "places", "name", "help"]
    if voice:
        chan = voice.channel
        voice = str(voice.channel.id)
        if voice in bdd[guild_id]['channels'].keys():
            if member_id == bdd[guild_id]['channels'][voice]["owner"]:
                if len(content) > 1 and content[1] in keywords:
                    if content[1] == 'name' and len(content) > 2:
                        await chan.edit(name=" ".join(content[2:]))
                        await ctx.message.channel.send("Nom changé avec succés")
                        bdd[guild_id]['channels'][voice]["name"] = " ".join(content[2:])
                    if content[1] == "owner" and len(ctx.message.mentions):
                        bdd[guild_id]['channels'][voice]["owner"] = ctx.message.mentions[0].id
                else:
                    await ctx.message.channel.send(embed=help_embed(ctx.author))

            else:
                await ctx.message.channel.send("Vous n'avez pas la permission !")
        else:
            await ctx.message.channel.send('Vous devez être dans votre channel vocal.')
    else:
        await ctx.message.channel.send('Vous devez être dans votre channel vocal.')
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
                "places": 2
            }
    if before.channel and str(before.channel.id) in bdd[str(member.guild.id)]["channels"] \
            and not len(before.channel.members):
        bdd[str(member.guild.id)]['channels'].pop(str(before.channel.id))
        await before.channel.delete(reason='Last member leave')
    update_json(bdd)
    update_bdd(bdd)


bot.run(os.environ["BOT_TOKEN"])
