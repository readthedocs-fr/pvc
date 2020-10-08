from discord.ext import commands
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
                    await ctx.send("Channel principal configuré")
                else:
                    await ctx.send("Veuillez envoyer une id valide")
            else:
                await ctx.send("Veuillez envoyer une id valide")
        else:
            await ctx.send("Veuillez spécifier un channel id")
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
