from discord.ext import commands
from utils import update_json, update_data
import discord


class SetChannel(commands.Cog):
    def __init__(self, bot, data, logger):
        self.bot = bot
        self.data = data
        self.logger = logger

    @commands.command(name="setchannel")
    @commands.has_permissions(administrator=True)
    async def set_channel(self, ctx):
        content = ctx.message.content.split()

        if len(content) <= 1:
            await ctx.send("Please specify a channel id.")
            return

        if not content[1].isdigit():
            await ctx.send("Please use a valid id.")
            return

        channel = self.bot.get_channel(int(content[1]))

        if not channel:
            await ctx.send("Please use a valid id.")
            return

        if not isinstance(channel, discord.VoiceChannel):
            await ctx.send("Please use a voice channel id.")
            return

        if self.data[str(ctx.guild.id)]["main"] is not None:
            self.logger.warning(f"Channel already set {self.data[str(ctx.guild.id)]['main']}.")
        self.logger.info(f"Set main channel <{channel.name}.{channel.id}>")

        self.data[str(ctx.guild.id)]['main'] = channel.id
        await ctx.send("Main channel set.")

        update_json(self.data)
        update_data(self.data)

    @commands.command(name="unsetchannel")
    @commands.has_permissions(administrator=True)
    async def unset_channel(self, ctx):
        self.data[str(ctx.guild.id)]['main'] = None
        await ctx.send("Main channel reset.")

        self.logger.info("Main channel reset.")

        update_json(self.data)
        update_data(self.data)
