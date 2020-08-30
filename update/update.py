from contextlib import suppress
from typing import Union

import discord
from discord.ext.commands import PartialEmojiConverter
from redbot.core import Config
from redbot.core.commands import commands, Context

from update.selection import SelectionInterface, SelectionType, ReplacedText

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
            "emoji": None,
            "icon_url": None,
            "role_id": None,
            "footer_icon_url": None,
            "footer_text": None
        }
        self.settings.register_guild(**default_guild_settings)
        self.settings.register_channel(**default_channel_settings)

    def _get_emoji(self, emoji):
        try:
            emoji = int(emoji)
            emoji = self.bot.get_emoji(emoji)
            return emoji
        except ValueError:
            return emoji

    @commands.command(name='update')
    async def _update(self, ctx: Context):
        """Sends a update message to the selected channel with the selected parameters"""
        selection = SelectionInterface(ctx, timeout=600)

        update_channels = {}
        for cid, data in (await self.settings.all_channels()).items():
            if not ctx.guild.get_channel(cid):
                continue
            emoji = data['emoji']
            emoji = self._get_emoji(emoji)
            if not emoji:
                continue
            update_channels[emoji] = data

        if len(update_channels) < 1:
            embed = discord.Embed(color=discord.Colour.dark_red())
            embed.description = f'No update channel has been configured yet. Checkout `{ctx.prefix}updateset`'
            return await ctx.send(embed=embed)

        if len(update_channels) > 1:
            desc = '\n'.join([f'{str(e)} **-** {data["name"]}' for e, (cid, data) in update_channels.items()])

            type_selection = selection.set_base_selection(
                SelectionType.REACTION,
                'Select Update Channel',
                f'**To which channel should the update message be sent?**\n\n{desc}',
                reactions=update_channels.keys())
            title_selection = type_selection.add_result('*', SelectionType.TEXT, 'Select Title',
                                                        '**Please enter the update title.**')
        else:
            title_selection = selection.set_base_selection(SelectionType.TEXT, 'Select Title',
                                                           '**Please enter the update title.**')

        message_selection = title_selection.add_result('*', SelectionType.TEXT, 'Select Message',
                                                       'Title successfully set!\n\n'
                                                       '**Please enter the update message.**')

        image_selection = message_selection.add_result('*', SelectionType.TEXT, 'Select Image',
                                                       'Message successfully set!\n\n'
                                                       '**Please enter the image url.**\n'
                                                       'For no image enter `none` for no image.')

        notification_selection = image_selection.add_result('*', SelectionType.REACTION, 'Select Notification',
                                                            'Message successfully set!\n\n'
                                                            '**Should we notify someone?**\n'
                                                            '\U00000031 **- Disable notifications**\n'
                                                            '\U00000032 **- Notify role**\n'
                                                            '\U00000033 **- Notify everyone**',
                                                            reactions=['\U00000031', '\U00000032', '\U00000033'])

        def f1(result):
            data_ = update_channels[list(update_channels.keys())[0]] if len(update_channels) <= 1 else \
                update_channels[str(result[0])]


        submit_selection = notification_selection.add_result(
            '*',
            SelectionType.CONFIRM_SELECTION,
            ReplacedText('{}', lambda x: x[1] if len(update_channels) > 1 else x[0]),
            ReplacedText('{}', lambda x: x[2] if len(update_channels) > 1 else x[1]),
            color=self.bot.get_embed_colour(ctx.message),
            thumbnail=ReplacedText('{}', f1),
            image=ReplacedText('{}', lambda x: x[3] if len(update_channels) > 1 else x[2])
        )

        async def a(context, result):
            data_ = update_channels[list(update_channels.keys())[0]] if len(update_channels) <= 1 else \
                update_channels[str(result[0])]

            update_message = discord.Embed()
            update_message.title = result[1] if len(update_channels) > 1 else result[0]
            update_message.colour = self.bot.get_embed_colour(ctx.message)
            update_message.description = result[2] if len(update_channels) > 1 else result[1]
            if (result[3] if len(update_channels) > 1 else result[2]).lower() != 'none':
                update_message.set_image(url=result[3] if len(update_channels) > 1 else result[2])
            if data['icon_url']:
                update_message.set_thumbnail(url=data['icon_url'])

            channel = context.bot.get_channel(data_['channel_id'])

            role = context.guild.get_role(data['role_id'])

            mention = None
            mention_r = result[4] if len(update_channels) > 1 else result[3]
            if mention_r == '\U00000032':
                mention = role.mention
            elif mention_r == '\U00000033':
                mention = '@everyone'

            message = await channel.send(content=mention, embed=update_message)
            if channel.is_news():
                with suppress(discord.Forbidden):
                    await message.publish()

        submit_selection.set_action(a)

        submit_selection.add_result('*', SelectionType.SUCCESS, 'Update successfully',
                                    ':white_check_mark: Update successfully sent!')

        await selection.start()

    @commands.group(name='updateset')
    async def _update_set(self, ctx: Context):
        """Update configuration options."""
        pass

    @_update_set.command(name='add')
    # TODO: Permissions Check
    async def _update_set_add(self, ctx: Context, channel: discord.TextChannel, emoji: Union[discord.Emoji, str], *, name: str):
        """Add a update channel"""
        existing_name = await self.settings.channel(channel).name()
        if existing_name:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The channel is already a update channel.\n' \
                                f'> **Channel:** {channel.mention}\n' \
                                f'> **Name:** {existing_name}'
            return await ctx.send(embed=embed)
        await self.settings.channel(channel).name.set(name)
        await self.settings.channel(channel).emoji.set(emoji.id if isinstance(emoji, discord.Emoji) else emoji)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'The channel has been successfully added as a update channel.\n' \
                            f'> **Channel:** {channel.mention}\n' \
                            f'> **Name:** {name}\n' \
                            f'> **Emoji:** {emoji}'
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
                            f'> **Channel:** {channel.mention}\n' \
                            f'> **Name:** {existing_name}'
        return await ctx.send(embed=embed)

    @_update_set.command(name='list')
    async def _update_set_list(self, ctx: Context):
        """List all update channels"""
        embed = discord.Embed(color=discord.Colour.dark_magenta())
        embed.title = 'Update Channels'
        for channel_id, data in (await self.settings.all_channels()).items():
            channel = ctx.guild.get_channel(channel_id)
            if not channel:
                continue
            role = ctx.guild.get_role(data['role_id'])
            embed.add_field(name=f'**{data["name"]}**',
                            value=f'> **Channel:** {channel.mention}\n'
                                  f'> **Emoji:** {self._get_emoji(data["emoji"])}\nf'
                                  f'> **Image URL:** {data["icon_url"] if data["icon_url"] else ":x:"}\n'
                                  f'> **Role:** {role.mention if role else ":x:"}\n'
                                  f'> **Footer Text:** {data["footer_text"] if data["footer_text"] else ":x:"}\n'
                                  f'> **Footer Icon URL:** '
                                  f'{data["footer_icon_url"] if data["footer_icon_url"] else ":x:"}',
                            inline=False)
        await ctx.send(embed=embed)

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
