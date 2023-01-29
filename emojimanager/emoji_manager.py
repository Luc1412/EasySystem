from typing import List, Optional

import discord
from discord import app_commands
from redbot.core import Config, checks
from redbot.core.commands import commands, Context
from redbot.core.utils.chat_formatting import pagify


class EmojiManager(commands.Cog):
    """This cog manages emojimanager on bot-owned guild, to don't waste your support server slots."""

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, 782392998)
        default_global_settings = {
            'emoji_server_ids': []
        }
        self.settings.register_global(**default_global_settings)

    async def _get_guild(self, for_animated: bool) -> discord.Guild:
        guild_ids = await self.settings.emoji_server_ids()
        for guild_id in guild_ids:
            guild = self.bot.get_guild(guild_id)
            emojis = len([e.id for e in guild.emojis if not e.animated])
            animated_emojis = len([e.id for e in guild.emojis if e.animated])
            if (animated_emojis if for_animated else emojis) < 50:
                return guild

    async def _get_emoji_names(self):
        guild_ids = await self.settings.emoji_server_ids()
        names = []
        for guild_id in guild_ids:
            guild = self.bot.get_guild(guild_id)
            for emoji in guild.emojis:
                names.append(emoji.name.lower())
        return names

    @commands.hybrid_group(name='emoji')
    @app_commands.default_permissions()
    async def _emoji(self, ctx: Context):
        """Manage the emoji on all linked guilds."""
        pass

    @_emoji.command(name='add', description='Add an emoji to one of the emoji servers.')
    @app_commands.describe(name='The name of the emoji.', description='The name of the emojimanager.')
    async def _emoji_add(self, ctx: Context, name: str, icon: discord.Attachment):
        """Add an emoji to one of the emoji servers."""
        is_animated = icon.filename.endswith('.gif')

        if name.lower() in await self._get_emoji_names():
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'A emojimanager with the name already exits.\n' \
                                f'> **Name:** {name}'
            return await ctx.send(embed=embed)
        emoji_guild = await self._get_guild(is_animated)
        if not emoji_guild:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'There was no free emoji guild found.'
            return await ctx.send(embed=embed)
        try:
            emoji = await emoji_guild.create_custom_emoji(name=name, image=await icon.read())
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
        message.description = f'Successfully added emojimanager.\n' \
                              f'> **Name:** {emoji.name}\n' \
                              f'> **ID:** {emoji.id}'
        await ctx.send(embed=message)

    @_emoji.command(name='remove')
    async def _emoji_remove(self, ctx: Context, id_: int):
        """Remove an emoji from an emoji server."""
        emoji = ctx.bot.get_emoji(id_)
        if not emoji:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The emojimanager wasn\'t found.'
            return await ctx.send(embed=embed)
        guild_ids = await self.settings.emoji_server_ids()
        if emoji.guild.id in guild_ids:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The emojimanager isn\'t owned by a Emoji Server.'
            return await ctx.send(embed=embed)
        await emoji.delete()

        message = discord.Embed(colour=discord.Colour.dark_blue())
        message.set_thumbnail(url=emoji.url)
        message.description = f'Successfully deleted emojimanager.\n' \
                              f'> **Name:** {emoji.name}\n' \
                              f'> **ID:** {emoji.id}'
        await ctx.send(embed=message)

    @_emoji.command(name='list')
    async def _emoji_list(self, ctx: Context):
        """List all emojis on all emojimanager servers."""
        embed = discord.Embed(colour=discord.Color.dark_magenta())
        embed.title = 'Emojis'
        for guild_id in await self.settings.emoji_server_ids():
            guild = ctx.bot.get_guild(guild_id)
            text = '\n'.join([f'{e} • `{e.id}`' for e in guild.emojis])
            for i, page in enumerate(pagify(text, page_length=1000, shorten_by=0)):
                title = f'**{guild}**:' if i == 0 else f'**{guild}** (continued):'
                embed.add_field(name=title, value=page, inline=False)
        await ctx.send(embed=embed)

    @commands.group(name='emoji-settings')
    @app_commands.default_permissions()
    async def _emoji_settings(self, ctx: Context):
        """Set up the emoji manager."""
        pass

    @_emoji_settings.command(name='add-server')
    async def _emoji_settings_add_server(
            self,
            ctx: Context,
            guild: app_commands.Transform[Optional[discord.Guild], "GuildAddTransformer"]
    ):
        """Add a emoji guild."""
        if not guild:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The guild wasn\'t found or is already a emoji server.'
            return await ctx.send(embed=embed)

        guild_ids = await self.settings.emoji_server_ids()
        guild_ids.append(guild.id)
        await self.settings.emoji_server_ids.set(guild_ids)

        message = discord.Embed(colour=discord.Colour.green())
        message.description = f'Successfully added guild as emojimanager server.\n' \
                              f'> **Name:** {guild.name}\n' \
                              f'> **ID:** {guild.id}'
        await ctx.send(embed=message)

    @_emoji_settings.command(name='remove')
    @app_commands.describe(guild_id='The ID of the guild.')
    @app_commands.rename(guild_id='guild-id')
    async def _emoji_settings_remove_guild(self, ctx: Context, guild_id: str):
        """Remove a emojimanager guild."""
        guild = ctx.bot.get_guild(guild_id)
        if not guild:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The bot isn\'t on the guild.'
            return await ctx.send(embed=embed)
        guild_ids = await self.settings.emoji_server_ids()
        if guild_id not in guild_ids:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The guild is no emojimanager server.'
            return await ctx.send(embed=embed)

        guild_ids.remove(guild.id)
        await self.settings.emoji_server_ids.set(guild_ids)

        message = discord.Embed(colour=discord.Colour.green())
        message.description = f'Successfully removed guild as emojimanager server.\n' \
                              f'> **Name:** {guild.name}\n' \
                              f'> **ID:** {guild.id}'
        await ctx.send(embed=message)

    @_emojiset.command(name='list')
    async def _emojiset_list(self, ctx: Context):
        """List all emojimanager guilds."""
        guild_ids = await self.settings.emoji_server_ids()
        guilds = [ctx.bot.get_guild(gid) for gid in guild_ids]
        embed = discord.Embed(colour=discord.Color.dark_magenta())
        embed.title = 'Emoji Server'
        embed.description = '\n'.join([f'{g.name} • `{g.id}`' for g in guilds])
        await ctx.send(embed=embed)


class GuildAddTransformer(app_commands.Transformer):

    async def autocomplete(self, interaction: discord.Interaction, current: str, /) -> List[app_commands.Choice[str]]:
        emoji_manager_cog: "EmojiManager" = interaction.client.get_cog('EmojiManager')
        guild_ids = await emoji_manager_cog.settings.emoji_server_ids()
        return [
            app_commands.Choice(name=g.name, value=g.id)
            for g in interaction.client.guilds
            if g.id not in guild_ids and g.name.startswith(current)
        ]

    async def transform(self, interaction: discord.Interaction, value: str, /) -> Optional[discord.Guild]:
        emoji_manager_cog: "EmojiManager" = interaction.client.get_cog('EmojiManager')
        guild_ids = await emoji_manager_cog.settings.emoji_server_ids()

        try:
            guild_id = int(value)
            if guild_id in guild_ids:
                return None
            return interaction.client.get_guild(guild_id)
        except ValueError:
            return None

class GuildRemoveTransformer(app_commands.Transformer):

    async def autocomplete(self, interaction: discord.Interaction, current: str, /) -> List[app_commands.Choice[str]]:
        emoji_manager_cog: "EmojiManager" = interaction.client.get_cog('EmojiManager')
        guild_ids = await emoji_manager_cog.settings.emoji_server_ids()
        return [
            app_commands.Choice(name=g.name, value=g.id)
            for g in interaction.client.guilds
            if g.id not in guild_ids and g.name.startswith(current) or
        ]

    async def transform(self, interaction: discord.Interaction, value: str, /) -> Optional[discord.Guild]:
        emoji_manager_cog: "EmojiManager" = interaction.client.get_cog('EmojiManager')
        guild_ids = await emoji_manager_cog.settings.emoji_server_ids()

        try:
            guild_id = int(value)
            if guild_id in guild_ids:
                return None
            return interaction.client.get_guild(guild_id)
        except ValueError:
            return None
