import traceback
from contextlib import suppress
from typing import Union

import discord
from redbot.core import Config, checks
from redbot.core.commands import commands, Context

from update.selection import SelectionInterface, SelectionType, ReplacedText, NumberReaction

BaseCog = getattr(commands, "Cog", object)


class Update(BaseCog):
    """

    """

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, 200912392)
        default_channel_settings = {
            "name": None,
            "emoji": None,
            "icon_url": None,
            "role_id": None,
            "footer_icon_url": None,
            "footer_text": None
        }
        self.settings.register_channel(**default_channel_settings)

    def _get_emoji(self, emoji):
        try:
            emoji = int(emoji)
            emoji = self.bot.get_emoji(emoji)
            return emoji
        except ValueError:
            return emoji

    @commands.group(name='update', invoke_without_command=True)
    @checks.admin_or_permissions(manage_guild=True)
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
            update_channels[emoji] = (cid, data)

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

        notification_selection = image_selection.add_result(
            '*', SelectionType.REACTION,
            'Select Notification',
            'Message successfully set!\n\n'
            '**Should we notify someone?**\n'
            ':one: **- Disable notifications**\n'
            ':two: **- Notify role**\n'
            ':three: **- Notify everyone**',
            reactions=[NumberReaction.ONE.value, NumberReaction.TWO.value, NumberReaction.THREE.value]
        )

        def f1(result):
            cid_, data_ = update_channels[list(update_channels.keys())[0]] if len(update_channels) <= 1 else \
                update_channels[result[0]]
            return data_['icon_url'] if data_['icon_url'] else discord.embeds.EmptyEmbed

        def f2(result):
            cid_, data_ = update_channels[list(update_channels.keys())[0]] if len(update_channels) <= 1 else \
                update_channels[result[0]]
            return data_['footer_text'] if data_['footer_text'] else None

        def f3(result):
            cid_, data_ = update_channels[list(update_channels.keys())[0]] if len(update_channels) <= 1 else \
                update_channels[result[0]]
            return data_['footer_icon_url'] if data_['footer_icon_url'] else discord.embeds.EmptyEmbed

        submit_selection = notification_selection.add_result(
            '*',
            SelectionType.CONFIRM_SELECTION,
            ReplacedText('{}', lambda x: x[1] if len(update_channels) > 1 else x[0]),
            ReplacedText('{}', lambda x: x[2] if len(update_channels) > 1 else x[1]),
            color=await self.bot.get_embed_colour(ctx.message),
            thumbnail=ReplacedText('{}', f1),
            image=ReplacedText('{}', lambda x: x[3] if len(update_channels) > 1 else x[2]),
            footer_text=ReplacedText('{}', f2),
            footer_icon=ReplacedText('{}', f3),
        )

        async def a(context, result):
            try:
                cid_, data_ = update_channels[list(update_channels.keys())[0]] if len(update_channels) <= 1 else \
                    update_channels[result[0]]

                update_message = discord.Embed()
                update_message.title = result[1] if len(update_channels) > 1 else result[0]
                update_message.colour = await self.bot.get_embed_colour(context.message)
                update_message.description = result[2] if len(update_channels) > 1 else result[1]
                if (result[3] if len(update_channels) > 1 else result[2]).lower() != 'none':
                    update_message.set_image(url=result[3] if len(update_channels) > 1 else result[2])
                if data['icon_url']:
                    update_message.set_thumbnail(url=data['icon_url'])

                channel = context.bot.get_channel(cid_)

                role = context.guild.get_role(data['role_id'])

                mention = None
                mention_r = result[4] if len(update_channels) > 1 else result[3]
                if mention_r == NumberReaction.TWO.value:
                    mention = role.mention
                elif mention_r == NumberReaction.THREE.value:
                    mention = '@everyone'

                message = await channel.send(content=mention, embed=update_message,
                                             allowed_mentions=discord.AllowedMentions(everyone=True, roles=True))
                with suppress(discord.Forbidden):
                    await message.add_reaction(list(update_channels.keys())[0] if len(update_channels) <= 1
                                               else result[0])
                if channel.is_news():
                    with suppress(discord.Forbidden):
                        await message.publish()
            except:
                print(traceback.format_exc())

        submit_selection.set_action(a)

        submit_selection.add_result('*', SelectionType.SUCCESS, 'Update successfully',
                                    ':white_check_mark: Update successfully sent!')

        await selection.start()

    @_update.command(name='edit')
    @checks.admin_or_permissions(manage_guild=True)
    async def _update_edit(self, ctx: Context, message: discord.Message):
        """Sends a update message to the selected channel with the selected parameters"""
        existing_name = await self.settings.channel(message.channel).name()
        if not existing_name:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The channel where the message is located is no update channel.\n' \
                                f'> **Channel:** {message.channel.mention}\n'
            return await ctx.send(embed=embed)
        if message.author.id != ctx.bot.user.id or len(message.embeds) != 1:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The message is not update message.\n' \
                                f'> **Channel:** {message.channel.mention}\n'
            return await ctx.send(embed=embed)

        icon_url = await self.settings.channel(message.channel).icon_url()
        footer_icon_url = await self.settings.channel(message.channel).footer_icon_url()
        footer_text = await self.settings.channel(message.channel).footer_text()

        selection = SelectionInterface(ctx, timeout=600)

        title_selection = selection.set_base_selection(SelectionType.TEXT, 'Select new Title',
                                                       '**Please enter the new update title.**')

        message_selection = title_selection.add_result('*', SelectionType.TEXT, 'Select new Message',
                                                       'Title successfully set!\n\n'
                                                       '**Please enter the new update message.**')

        image_selection = message_selection.add_result('*', SelectionType.TEXT, 'Select Image',
                                                       'Message successfully set!\n\n'
                                                       '**Please enter the image url.**\n'
                                                       'For no image enter `none` for no image.')

        def f1(result):
            return icon_url if icon_url else discord.embeds.EmptyEmbed

        def f2(result):
            return footer_text if footer_text else None

        def f3(result):
            return footer_icon_url if footer_icon_url else discord.embeds.EmptyEmbed

        submit_selection = image_selection.add_result(
            '*',
            SelectionType.CONFIRM_SELECTION,
            ReplacedText('{}', lambda x: x[0]),
            ReplacedText('{}', lambda x: x[1]),
            color=await self.bot.get_embed_colour(ctx.message),
            thumbnail=ReplacedText('{}', f1),
            image=ReplacedText('{}', lambda x: x[2]),
            footer_text=ReplacedText('{}', f2),
            footer_icon=ReplacedText('{}', f3),
        )

        async def a(context, result):
            try:

                update_message = message.embeds[0]
                update_message.title = result[0]
                update_message.colour = await self.bot.get_embed_colour(context.message)
                update_message.description = result[1]
                if (result[2]).lower() != 'none':
                    update_message.set_image(url=result[2])
                if icon_url:
                    update_message.set_thumbnail(url=icon_url)

                await message.edit(content=message.content, embed=update_message)
            except:
                print(traceback.format_exc())

        submit_selection.set_action(a)

        submit_selection.add_result('*', SelectionType.SUCCESS, 'Update edit successfully',
                                    ':white_check_mark: Update successfully edited!')

        await selection.start()

    @commands.group(name='updateset')
    @checks.admin_or_permissions(manage_guild=True)
    async def _update_set(self, ctx: Context):
        """Update configuration options."""
        pass

    @_update_set.command(name='add')
    async def _update_set_add(self,
                              ctx: Context,
                              channel: discord.TextChannel,
                              emoji: Union[discord.Emoji, str],
                              *, name: str):
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
                                  f'> **Emoji:** {self._get_emoji(data["emoji"])}\n'
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
