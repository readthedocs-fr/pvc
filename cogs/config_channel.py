from discord.ext import commands
import discord
from utils import update_data, update_json, config_help_embed


def format_time(t: int):
    minutes, seconds = divmod(t, 60)
    text = str(seconds)
    if minutes:
        text = f"{minutes} minutes and {seconds}"
    return f"You are going too fast ! Please wait {text} seconds before retry it."


class ConfigChannel(commands.Cog):
    def __init__(self, bot, data, logger):
        self.bot = bot
        self.data = data
        self.logger = logger

    def perm(self, ctx):
        if not ctx.author.voice or str(ctx.author.voice.channel.id) not in self.data[str(ctx.guild.id)]["channels"].keys():
            return 'You must be in your voice channel.'
        if ctx.author.id != self.data[str(ctx.guild.id)]['channels'][str(ctx.author.voice.channel.id)]:
            return "You don't have permission to do this !"

    @commands.group(name="set")
    async def _set(self, ctx):
        update_data(self.data)
        content = ctx.message.content.split()
        keywords = ["private", "public", "owner", "places", "name", "hide", "reveal", "invite", "kick", "ban", "unban"]
        if len(content) <= 1 or content[1] not in keywords:
            await ctx.send(embed=config_help_embed(ctx.author))

    @commands.cooldown(1, 300, commands.BucketType.member)
    @_set.command()
    async def name(self, ctx):
        perm = self.perm(ctx)
        if perm:
            return await ctx.send(perm)
        update_data(self.data)
        content = ctx.message.content.split()
        voice = ctx.author.voice
        guild_id = str(ctx.guild.id)

        if not voice:
            return self.name.reset_cooldown(ctx)

        chan = voice.channel
        voice_id = str(voice.channel.id)

        if voice_id not in self.data[guild_id]['channels'].keys():
            return self.name.reset_cooldown(ctx)

        if ctx.author.id != self.data[guild_id]['channels'][voice_id]:
            return self.name.reset_cooldown(ctx)

        if len(content) > 2:
            await chan.edit(name=" ".join(content[2:]))
            await ctx.message.channel.send("Name successfully changed.")
        else:
            return self.name.reset_cooldown(ctx)

    @_set.command()
    async def owner(self, ctx):
        perm = self.perm(ctx)
        if perm:
            return await ctx.send(perm)
        update_data(self.data)
        guild_id = str(ctx.guild.id)
        if len(ctx.message.mentions):
            self.data[guild_id]['channels'][str(ctx.author.voice.channel.id)] = ctx.message.mentions[0].id
            await ctx.message.channel.send(f"Owner successfully changed to {ctx.message.mentions[0].name}.")

        update_json(self.data)

    @_set.command()
    async def places(self, ctx):
        perm = self.perm(ctx)
        if perm:
            return await ctx.send(perm)
        content = ctx.message.content.split()
        if not content[2].isdigit() or not 0 <= int(content[2]) < 100:
            await ctx.send("Please use a number between 0 and 99.")
            return

        await ctx.author.voice.channel.edit(user_limit=int(content[2]))
        await ctx.send("Number of places successfully changed.")

    @_set.command()
    async def reveal(self, ctx):
        perm = self.perm(ctx)
        if perm:
            return await ctx.send(perm)
        await ctx.author.voice.channel.set_permissions(ctx.guild.default_role, view_channel=True)
        await ctx.send("The channel is now visible.")

    @_set.command()
    async def hide(self, ctx):
        perm = self.perm(ctx)
        if perm:
            return await ctx.send(perm)
        await ctx.author.voice.channel.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.send("The channel is now hidden.")

    @_set.command()
    async def public(self, ctx):
        perm = self.perm(ctx)
        if perm:
            return await ctx.send(perm)
        await ctx.author.voice.channel.set_permissions(ctx.guild.default_role, connect=True)
        await ctx.send("Channel defined as public.")

    @_set.command()
    async def private(self, ctx):
        perm = self.perm(ctx)
        if perm:
            return await ctx.send(perm)
        await ctx.author.voice.channel.set_permissions(ctx.guild.default_role, connect=False)
        await ctx.send("Channel defined as private.")

    @_set.command()
    async def invite(self, ctx):
        perm = self.perm(ctx)
        if perm:
            return await ctx.send(perm)
        if len(ctx.message.content.split()) < 2 or not len(ctx.message.mentions):
            await ctx.send("Please mention a valid user.")
            return

        await ctx.author.voice.channel.set_permissions(ctx.message.mentions[0], connect=True, view_channel=True)
        await ctx.send(f"{ctx.message.mentions[0]} is now allowed to connect to the channel.")

    @_set.command()
    async def kick(self, ctx, mention: discord.Member = None):
        perm = self.perm(ctx)
        if perm:
            return await ctx.send(perm)
        if not mention.voice or mention.voice.channel != ctx.author.voice.channel:
            await ctx.send("User must be in your channel.")
            return
        await mention.move_to(None)

    @_set.command()
    async def ban(self, ctx, mention: discord.Member = None):
        perm = self.perm(ctx)
        await ctx.author.voice.channel.set_permissions(mention, connect=False)
        await ctx.send(f"{mention} has been banned from {ctx.author.voice.channel}")
        if perm:
            return await ctx.send(perm)
       
        await mention.move_to(None)

    @_set.command()
    async def unban(self, ctx, mention: discord.Member = None):
        perm = self.perm(ctx)
        if perm:
            return await ctx.send(perm)
        await ctx.author.voice.channel.set_permissions(mention, connect=True)
        await ctx.send(f"{mention} has been unbanned from {ctx.author.voice.channel}")
        if perm:
            return await ctx.send(perm)
        

        
       
    @name.error
    async def on_command_error(self, ctx, error):
        self.logger.error(f"Error occured: {error}")
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(format_time(round(error.retry_after)))
