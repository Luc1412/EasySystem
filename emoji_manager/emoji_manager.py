import discord
from redbot.core import Config, checks
from redbot.core.commands import commands, Context
from redbot.core.utils.chat_formatting import pagify

from update.update import BaseCog


class EmojiManager(BaseCog):
    """This cog manages emoji on bot-owned guild, to don't waste your support server slots."""

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, 782392998)
        default_global_settings = {
            "emoji_server_ids": []
        }
        self.settings.register_global(**default_global_settings)

    async def _get_guild(self, animated: bool) -> discord.Guild:
        guild_ids = await self.settings.emoji_server_ids()
        for guild_id in guild_ids:
            guild = self.bot.get_guild(guild_id)
            emojis = len([e.id for e in guild.emojis if not e.animated])
            animated_emojis = len([e.id for e in guild.emojis if e.animated])
            if (animated_emojis if animated else emojis) < 50:
                return guild

    async def _get_emoji_names(self):
        guild_ids = await self.settings.emoji_server_ids()
        names = []
        for guild_id in guild_ids:
            guild = self.bot.get_guild(guild_id)
            for emoji in guild.emojis:
                names.append(emoji.name.lower())

    @commands.group(name='emoji')
    @checks.is_owner()
    async def _emoji(self, ctx: Context):
        """Manage the emoji on all linked guilds."""
        pass

    @_emoji.command(name='add')
    async def _emoji_add(self, ctx: Context, name: str):
        """Add a emoji to one emoji server."""
        if len(ctx.message.attachments) != 1:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'You need to provide a attachment with the emoji image.'
            return await ctx.send(embed=embed)
        attachment = ctx.message.attachments[0]
        is_animated = None
        for image_type in ['.png', 'jpg', '.jpeg']:
            if not attachment.filename.endswith(image_type):
                continue
            is_animated = False
            break
        for image_type in ['.gif']:
            if not attachment.filename.endswith(image_type):
                continue
            is_animated = True
            break
        if is_animated is None:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The file has to be a `.png`, `.jpg`, `.jpeg` and `.gif`'
            return await ctx.send(embed=embed)
        if name.lower() in await self._get_emoji_names():
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'A emoji with the name already exits.\n' \
                                f'> **Name:** {name}'
            return await ctx.send(embed=embed)
        image = await attachment.read()
        emoji_guild = await self._get_guild(is_animated)
        try:
            emoji = await emoji_guild.create_custom_emoji(name=name, image=image)
        except discord.HTTPException as e:
            return await ctx.bot.send_error(ctx, f'An error occurred: {e.text}')

        message = discord.Embed(colour=discord.Color.green())
        message.set_thumbnail(url=emoji.url)
        message.description = f'Successfully added emoji.\n' \
                              f'> **Name:** {emoji.name}\n' \
                              f'> **ID:** {emoji.id}'
        await ctx.send(embed=message)

    @_emoji.command(name='remove')
    async def _emoji_remove(self, ctx: Context, id_: int):
        """Remove a emoji to one emoji server."""
        emoji = ctx.bot.get_emoji(id_)
        if not emoji:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The emoji wasn\'t found.'
            return await ctx.send(embed=embed)
        guild_ids = await self.settings.emoji_server_ids()
        if emoji.guild.id in guild_ids:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The emoji isn\'t owned by a Emoji Server.'
            return await ctx.send(embed=embed)
        await emoji.delete()

        message = discord.Embed(colour=discord.Colour.dark_blue())
        message.set_thumbnail(url=emoji.url)
        message.description = f'Successfully deleted emoji.\n' \
                              f'> **Name:** {emoji.name}\n' \
                              f'> **ID:** {emoji.id}'
        await ctx.send(embed=message)

    @_emoji.command(name='list')
    async def _emoji_list(self, ctx: Context):
        """List all emojis on all emoji servers."""
        embed = discord.Embed(colour=discord.Color.dark_magenta())
        embed.title = 'Emojis'
        for guild_id in await self.settings.emoji_server_ids():
            guild = ctx.bot.get_guild(guild_id)
            text = '\n'.join([f'{e} • `{e.id}`' for e in guild.emojis])
            for i, page in enumerate(pagify(text, page_length=1000, shorten_by=0)):
                title = f'**{guild}**:' if i == 0 else f'**{guild}** (continued):'
                embed.add_field(name=title, value=page, inline=False)
        await ctx.send(embed=embed)

    @commands.group(name='emojiset')
    @checks.is_owner()
    async def _emojiset(self, ctx: Context):
        """Setup the cog."""
        pass

    @_emojiset.command(name='add')
    async def _emojiset_add(self, ctx: Context, guild_id: int):
        """Add a emoji guild."""
        guild = ctx.bot.get_guild(guild_id)
        if not guild:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The bot isn\'t on the guild.'
            return await ctx.send(embed=embed)
        guild_ids = await self.settings.emoji_server_ids()
        if guild.id in guild_ids:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The guild is already a emoji server.'
            return await ctx.send(embed=embed)

        guild_ids.append(guild.id)
        await self.settings.emoji_server_ids.set(guild_ids)

        message = discord.Embed(colour=discord.Colour.green())
        message.description = f'Successfully added guild as emoji server.\n' \
                              f'> **Name:** {guild.name}\n' \
                              f'> **ID:** {guild.id}'
        await ctx.send(embed=message)


    @_emojiset.command(name='remove')
    async def _emojiset_remove(self, ctx: Context, guild_id: int):
        """Remove a emoji guild."""
        guild = ctx.bot.get_guild(guild_id)
        if not guild:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The bot isn\'t on the guild.'
            return await ctx.send(embed=embed)
        guild_ids = await self.settings.emoji_server_ids()
        if guild_id not in guild_ids:
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

    @_emojiset.command(name='list')
    async def _emojiset_list(self, ctx: Context):
        """List all emoji guilds."""
        guild_ids = await self.settings.emoji_server_ids()
        guilds = [ctx.bot.get_guild(gid) for gid in guild_ids]
        embed = discord.Embed(colour=discord.Color.dark_magenta())
        embed.title = 'Emoji Server'
        embed.description = '\n'.join([f'{g.name} • `{g.id}`' for g in guilds])
        await ctx.send(embed=embed)
