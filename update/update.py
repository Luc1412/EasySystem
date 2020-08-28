from typing import Union

import discord
from redbot.core import Config
from redbot.core.commands import commands, Context

BaseCog = getattr(commands, "Cog", object)


class Update(BaseCog):
    """

    """

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, 200912392)
        default_guild_settings = {

        }
        default_channel_settings = {
            "name": None,
            "icon_url": None,
            "role_id": None,
            "footer_icon_url": None,
            "footer_text": None
        }
        self.settings.register_guild(**default_guild_settings)
        self.settings.register_channel(**default_channel_settings)

    @commands.command(name='update')
    async def _update(self, ctx: Context):
        pass

    @commands.group(name='updateset')
    async def _update_set(self, ctx: Context):
        """Update configuration options."""
        pass

    @_update_set.command(name='add')
    # TODO: Permissions Check
    async def _update_set_add(self, ctx: Context, channel: discord.TextChannel, *, name: str):
        """Add a update channel"""
        existing_name = await self.settings.channel(channel).name()
        if existing_name:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The channel is already a update channel.\n' \
                                f'> **Channel:** {channel.mention}' \
                                f'> **Name:** {existing_name}'
            return await ctx.send(embed=embed)
        await self.settings.channel(channel).name.set(name)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'The channel has been successfully added as a update channel.\n' \
                            f'> **Channel:** {channel.mention}' \
                            f'> **Name:** {name}'
        return await ctx.send(embed=embed)

    @_update_set.command(name='remove')
    async def _update_set_remove(self, ctx: Context, channel: discord.TextChannel):
        """Remove a update channel"""
        existing_name = await self.settings.channel(channel).name()
        if not existing_name:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The channel is no update channel.\n' \
                                f'> **Channel:** {channel.mention}'
            return await ctx.send(embed=embed)
        await self.settings.channel(channel).clear()
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.description = f'The channel has been successfully removed as a update channel.\n' \
                            f'> **Channel:** {channel.mention}' \
                            f'> **Name:** {existing_name}'
        return await ctx.send(embed=embed)

    @_update_set.command(name='list')
    async def _update_set_list(self, ctx: Context):
        """List all update channels"""
        for channel_id, data in (await self.settings.all_channels()).items():
            channel = ctx.guild.get_channel(channel_id)
            if not channel:
                continue

    @_update_set.command(name='icon')
    async def _update_set_icon(self, ctx: Context, channel: discord.TextChannel, url: str):
        """Set a icon url. Use 'reset' to remove the icon."""
        existing_name = await self.settings.channel(channel).name()
        if not existing_name:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The channel is no update channel.\n' \
                                f'> **Channel:** {channel.mention}'
            return await ctx.send(embed=embed)
        if url.lower() == 'reset':
            await self.settings.channel(channel).icon_url.set(None)
            embed = discord.Embed(colour=discord.Colour.blue())
            embed.description = f'The icon url for the channel has been successfully reset.\n' \
                                f'> **Channel:** {channel.mention}'
            return await ctx.send(embed=embed)
        await self.settings.channel(channel).icon_url.set(url)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'The icon url for the channel has been successfully set.\n' \
                            f'> **Channel:** {channel.mention}'
        embed.set_thumbnail(url=url)
        return await ctx.send(embed=embed)

    @_update_set.command(name='role')
    async def _update_set_role(self, ctx: Context, channel: discord.TextChannel, *, role: Union[discord.Role, str]):
        """Set a role which get mentioned. Use 'reset' to remove the role."""
        existing_name = await self.settings.channel(channel).name()
        if not existing_name:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The channel is no update channel.\n' \
                                f'> **Chanel:** {channel.mention}'
            return await ctx.send(embed=embed)
        if isinstance(role, str):
            if role.lower() != 'reset':
                embed = discord.Embed(colour=discord.Colour.dark_red())
                embed.description = f'The role is invalid.'
                return await ctx.send(embed=embed)
            await self.settings.channel(channel).role_id.set(None)
            embed = discord.Embed(colour=discord.Colour.gold())
            embed.description = f'The mention role for the channel has been reset.\n' \
                                f'> **Channel:** {channel.mention}'
            return await ctx.send(embed=embed)
        await self.settings.channel(channel).role_id.set(role.id)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'The mention role for the channel has been successfully set.\n' \
                            f'> **Channel:** {channel.mention}\n' \
                            f'> **Role:** {role.mention}'
        return await ctx.send(embed=embed)

    @_update_set.group(name='footer')
    async def _update_set_footer(self, ctx: Context):
        """Set the footer of the update message."""
        pass

    @_update_set_footer.command(name='icon')
    async def _update_set_footer_icon(self, ctx: Context, channel: discord.TextChannel, url: str):
        """Set a footer icon url. This only work if a text is set. Use 'reset' to remove the icon."""
        existing_name = await self.settings.channel(channel).name()
        if not existing_name:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The footer channel is no update channel.\n' \
                                f'> **Channel:** {channel.mention}'
            return await ctx.send(embed=embed)
        if not await self.settings.channel(channel).footer_text():
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'You can\'t set a footer icon. You need to set the text before with ' \
                                f'`{ctx.prefix}updateset footer text <Channel> <Text>`.\n' \
                                f'> **Channel:** {channel.mention}'
            return await ctx.send(embed=embed)
        if url.lower() == 'reset':
            await self.settings.channel(channel).footer_icon_url.set(None)
            embed = discord.Embed(colour=discord.Colour.blue())
            embed.description = f'The footer icon url for the channel has been successfully reset.\n' \
                                f'> **Channel:** {channel.mention}'
            return await ctx.send(embed=embed)
        await self.settings.channel(channel).footer_icon_url.set(url)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'The footer icon url for the channel has been successfully set.\n' \
                            f'> **Channel:** {channel.mention}'
        embed.set_thumbnail(url=url)
        return await ctx.send(embed=embed)

    @_update_set_footer.command(name='text')
    async def _update_set_footer_icon(self, ctx: Context, channel: discord.TextChannel, text: str):
        """Set a footer text. Use 'reset' to remove the text."""
        existing_name = await self.settings.channel(channel).name()
        if not existing_name:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The footer channel is no update channel.\n' \
                                f'> **Channel:** {channel.mention}'
            return await ctx.send(embed=embed)
        if text.lower() == 'reset':
            await self.settings.channel(channel).footer_icon_url.set(None)
            await self.settings.channel(channel).footer_icon_text.set(None)
            embed = discord.Embed(colour=discord.Colour.blue())
            embed.description = f'The footer text and footer icon url for the channel has been successfully reset.\n' \
                                f'> **Channel:** {channel.mention}'
            return await ctx.send(embed=embed)
        await self.settings.channel(channel).footer_icon_url.set(text)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'The footer icon url for the channel has been successfully set.\n' \
                            f'> **Channel:** {channel.mention}\n' \
                            f'> **Text:** {text}'
        return await ctx.send(embed=embed)

