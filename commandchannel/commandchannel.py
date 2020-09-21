from contextlib import suppress

import discord
from redbot.core import Config, checks
from redbot.core.commands import commands, Context

BaseCog = getattr(commands, "Cog", object)


class CommandChannel(BaseCog):
    """This cog offers to create channels where only commands are allowed."""

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, 97432092322309)
        default_guild_settings = {
            "channel_ids": [],
            "prefixes": []
        }
        self.settings.register_guild(**default_guild_settings)

    @commands.group(name='commandchannel')
    @checks.admin_or_permissions(manage_guild=True)
    async def _command_channel(self, ctx: Context):
        """Manage the command channels."""
        pass

    @_command_channel.command(name='add')
    async def _command_channel_add(self, ctx: Context, channel: discord.TextChannel):
        """Add a command only channel."""
        command_channel_ids = await self.settings.guild(ctx.guild).channel_ids()
        if channel.id in command_channel_ids:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'This channel is already a command only channel.\n' \
                                f'> Channel: {channel.mention}'
            return await ctx.send(embed=embed)
        command_channel_ids.add(channel.id)
        await self.settings.guild(ctx.guild).channel_ids.set(command_channel_ids)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'The command channel has been successfully added.\n' \
                            f'> Channel: {channel.mention}'
        return await ctx.send(embed=embed)

    @_command_channel.command(name='remove')
    async def _command_channel_remove(self, ctx: Context, channel: discord.TextChannel):
        """Removes a command only channel."""
        command_channel_ids = await self.settings.guild(ctx.guild).channel_ids()
        if channel.id not in command_channel_ids:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'This channel is no command only channel.\n' \
                                f'> Channel: {channel.mention}'
            return await ctx.send(embed=embed)
        command_channel_ids.remove(channel.id)
        await self.settings.guild(ctx.guild).channel_ids.set(command_channel_ids)
        embed = discord.Embed(colour=discord.Colour.dark_blue())
        embed.description = f'The command channel has been successfully removed.\n' \
                            f'> Channel: {channel.mention}'
        return await ctx.send(embed=embed)

    @_command_channel.command(name='list')
    async def _command_channel_list(self, ctx: Context):
        """List all command only channel."""
        command_channel_ids = await self.settings.guild(ctx.guild).channel_ids()
        if len(command_channel_ids) == 0:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'There is no command channel setup up for this server.'
            return await ctx.send(embed=embed)
        embed = discord.Embed(colour=discord.Colour.dark_magenta())
        channels = []
        for channel_id in command_channel_ids:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue
            channels.append(channel.mention)
        embed.description = ','.join(channels)
        return await ctx.send(embed=embed)

    @_command_channel.group(name='prefixes')
    @checks.admin_or_permissions(manage_guild=True)
    async def _command_channel_prefixes(self, ctx: Context):
        """Manage the command channels prefixes."""
        pass

    @_command_channel_prefixes.command(name='add')
    async def _command_channel_prefixes_add(self, ctx: Context, prefix: str):
        """Add a command prefix."""
        prefix = prefix.lower()
        command_prefixes = await self.settings.guild(ctx.guild).prefixes()
        if prefix in command_prefixes:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'This prefix is already in the list.\n' \
                                f'> Prefix: `{prefix}`'
            return await ctx.send(embed=embed)
        command_prefixes.add(prefix)
        await self.settings.guild(ctx.guild).prefixes.set(command_prefixes)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'The prefix has been successfully added.\n' \
                            f'> Prefix: `{prefix}`'
        return await ctx.send(embed=embed)

    @_command_channel_prefixes.command(name='remove')
    async def _command_channel_prefixes_remove(self, ctx: Context, prefix: str):
        """Remove a command prefix."""
        prefix = prefix.lower()
        command_prefixes = await self.settings.guild(ctx.guild).prefixes()
        if prefix not in command_prefixes:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'This prefix is not in the list.\n' \
                                f'> Prefix: `{prefix}`'
            return await ctx.send(embed=embed)
        command_prefixes.remove(prefix)
        await self.settings.guild(ctx.guild).prefixes.set(command_prefixes)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'The prefix has been successfully removed.\n' \
                            f'> Prefix: `{prefix}`'
        return await ctx.send(embed=embed)

    @_command_channel_prefixes.command(name='list')
    async def _command_channel_prefixes_list(self, ctx: Context):
        """List all command prefixes."""
        command_prefixes = await self.settings.guild(ctx.guild).prefixes()
        if len(command_prefixes) == 0:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'There is no prefix setup up for this server.'
            return await ctx.send(embed=embed)
        embed = discord.Embed(colour=discord.Colour.dark_magenta())
        embed.description = '`' + '`, `'.join(command_prefixes) + '`'
        return await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not isinstance(message.channel, discord.TextChannel) or message.author.bot:
            return
        if await self.bot.is_automod_immune(message.author):
            return
        command_channel_ids = await self.settings.guild(message.guild).channel_ids()
        if message.channel.id not in command_channel_ids:
            return
        command_prefixes = await self.settings.guild(message.guild).prefixes()
        for prefix in command_prefixes:
            if message.content.lower().startswith(prefix):
                return
        with suppress(discord.Forbidden, discord.NotFound):
            await message.delete()

