from typing import List, Optional, TYPE_CHECKING

import discord
from discord import app_commands
from redbot.core import Config
from redbot.core.commands import commands, Context
from redbot.core.utils.chat_formatting import pagify

from emojimanager.transformers import GuildTransformer, EmojiTransformer

if TYPE_CHECKING:
    from redbot.core.bot import Red


class EmojiManager(commands.Cog):
    """This cog manages emoji on bot-owned guild, to don't waste your support server slots."""

    def __init__(self, bot: "Red"):
        self.bot: "Red" = bot
        self.settings: Config = Config.get_conf(self, 782392998)
        default_global_settings = {
            'emoji_server_ids': []
        }
        self.settings.register_global(**default_global_settings)

    @commands.hybrid_group(name='emoji', description='Manage emoji on all managed guilds.')
    @app_commands.default_permissions()
    async def _emoji(self, ctx: Context):
        pass

    @_emoji.command(name='add', description='Add an emoji to one of the emoji servers.')
    @app_commands.describe(name='The name of the emoji.', image='The emoji image file')
    async def _emoji_add(self, ctx: Context, name: str, image: discord.Attachment):
        if image.content_type not in ('image/png', 'image/jpeg', 'image/gif'):
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The image has to be a png, jpg or gif.'
            return await ctx.send(embed=embed)

        is_animated = image.content_type == 'image/gif'

        if name.lower() in await self._get_emoji_names():
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'A emoji with the name already exits.'
            return await ctx.send(embed=embed)
        emoji_guild = await self._get_guild(is_animated)
        if not emoji_guild:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'There was no free emoji guild found.'
            return await ctx.send(embed=embed)
        try:
            emoji = await emoji_guild.create_custom_emoji(name=name, image=await image.read())
        except discord.HTTPException as e:
            if e.code == 50035:
                embed = discord.Embed(colour=discord.Colour.dark_red())
                embed.description = f'The image has to be smaller than 256KB.'
                return await ctx.send(embed=embed)
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'An unknown error occurred {e.text}'
            return await ctx.send(embed=embed)

        message = discord.Embed(colour=discord.Color.green())
        message.set_thumbnail(url=emoji.url)
        message.description = f'Successfully added emoji.\n' \
                              f'> **Name:** {emoji.name}\n' \
                              f'> **ID:** {emoji.id}'
        await ctx.send(embed=message)

    @_emoji.command(name='remove', description='Remove an emoji from one of the emoji servers.')
    @app_commands.describe(emoji='The emoji to remove.')
    async def _emoji_remove(
            self,
            ctx: Context,
            emoji: app_commands.Transform[Optional[discord.Emoji], EmojiTransformer]
    ):
        if not emoji:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The emoji wasn\'t found.'
            return await ctx.send(embed=embed)
        guild_ids = await self.settings.emoji_server_ids()
        if emoji.guild.id not in guild_ids:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The emoji isn\'t an emoji managed by this server.'
            return await ctx.send(embed=embed)
        await emoji.delete()

        message = discord.Embed(colour=discord.Colour.dark_blue())
        message.set_thumbnail(url=emoji.url)
        message.description = f'Successfully deleted emoji.\n' \
                              f'> **Name:** {emoji.name}\n' \
                              f'> **ID:** {emoji.id}'
        await ctx.send(embed=message)

    @_emoji.command(name='list', description='List all emojis on all emoji servers.')
    async def _emoji_list(self, ctx: Context):
        embed = discord.Embed(colour=discord.Color.dark_magenta())
        embed.title = 'Emojis'
        for guild_id in await self.settings.emoji_server_ids():
            guild = ctx.bot.get_guild(guild_id)
            text = '\n'.join([f'{e} • `{e.id}`' for e in guild.emojis])
            for i, page in enumerate(pagify(text, page_length=1024, shorten_by=0)):
                title = f'**{guild}**:' if i == 0 else f'**{guild}** (continued):'
                embed.add_field(name=title, value=page)
        await ctx.send(embed=embed)

    @commands.hybrid_group(name='emoji-settings', description='Manage emoji settings.')
    @app_commands.default_permissions()
    async def _emoji_settings(self, ctx: Context):
        """Set up the emoji manager."""
        pass

    @_emoji_settings.command(name='add', description='Add a guild as emoji server.')
    @app_commands.describe(guild='The guild to add as emoji server.')
    async def _emoji_settings_add(
            self,
            ctx: Context,
            guild: app_commands.Transform[Optional[discord.Guild], GuildTransformer]
    ):
        if not guild:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The guild wasn\'t found or is already a emoji server.'
            return await ctx.send(embed=embed)

        guild_ids = await self.settings.emoji_server_ids()
        guild_ids.append(guild.id)
        await self.settings.emoji_server_ids.set(guild_ids)

        message = discord.Embed(colour=discord.Colour.green())
        message.description = f'Successfully added guild as emoji server.\n' \
                              f'> **Name:** {guild.name}\n' \
                              f'> **ID:** {guild.id}'
        await ctx.send(embed=message)

    @_emoji_settings.command(name='remove', description='Remove a guild from the emoji servers.')
    @app_commands.describe(guild='The guild to remove.')
    async def _emoji_settings_remove(
            self,
            ctx: Context,
            guild: app_commands.Transform[Optional[discord.Guild], GuildTransformer]
    ):
        if not guild:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The bot isn\'t on the guild.'
            return await ctx.send(embed=embed)
        guild_ids = await self.settings.emoji_server_ids()
        if guild.id not in guild_ids:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The guild is no emoji server.'
            return await ctx.send(embed=embed)

        guild_ids.remove(guild.id)
        await self.settings.emoji_server_ids.set(guild_ids)

        message = discord.Embed(colour=discord.Colour.green())
        message.description = f'Successfully removed guild as emoji server.\n' \
                              f'> **Name:** {guild.name}\n' \
                              f'> **ID:** {guild.id}'
        await ctx.send(embed=message)

    @_emoji_settings.command(name='list', description='List all emoji servers.')
    async def _emoji_settings_list(self, ctx: Context):
        guild_ids = await self.settings.emoji_server_ids()
        guilds = [ctx.bot.get_guild(gid) for gid in guild_ids]
        embed = discord.Embed(colour=discord.Color.dark_magenta())
        embed.title = 'Emoji Server'
        embed.description = '\n'.join([
            f'{g.name} • `{g.id}` '
            f'[{len([e for e in g.emojis if not e.animated])}/50 | {len([e for e in g.emojis if e.animated])}/50]'
            for g in guilds
        ])
        await ctx.send(embed=embed)

    async def _get_guild(self, for_animated: bool) -> discord.Guild:
        guild_ids = await self.settings.emoji_server_ids()
        for guild_id in guild_ids:
            guild = self.bot.get_guild(guild_id)
            emojis = len([e.id for e in guild.emojis if not e.animated])
            animated_emojis = len([e.id for e in guild.emojis if e.animated])
            if (animated_emojis if for_animated else emojis) < 50:
                return guild

    async def _get_emoji_names(self) -> List[str]:
        guild_ids = await self.settings.emoji_server_ids()
        names = []
        for guild_id in guild_ids:
            guild = self.bot.get_guild(guild_id)
            for emoji in guild.emojis:
                names.append(emoji.name.lower())
        return names
