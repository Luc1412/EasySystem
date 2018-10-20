import asyncio
import datetime
import time

import discord
from discord.ext import commands

from bot import Bot
from utils import checks
from utils.utils import UpdateType


class AdminCommands:

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    async def selection_cancel(ctx, message):
        cancel_message = discord.Embed()
        cancel_message.colour = ctx.bot.utils.color.fail()
        cancel_message.set_author(name='Selection canceled!', icon_url=ctx.bot.cfg.get('Images.IconSmallUrl'))
        cancel_message.description = 'The selection was successfully canceled!'
        cancel_message.set_footer(text=ctx.bot.cfg.get('Core.Footer'),
                                  icon_url=ctx.bot.cfg.get('Images.FooterIconURL'))
        await message.edit(embed=cancel_message, content=None)

    @commands.group(invoke_without_command=True, case_insensitive=True)
    @commands.guild_only()
    @checks.is_guild_owner()
    async def whitelist(self, ctx: commands.Context):
        whitelist_message = discord.Embed()

    @commands.command(case_insensitive=True)
    @commands.guild_only()
    @checks.is_guild_owner()
    async def icons(self, ctx: commands.Context):
        message = str()
        for emoji in ctx.guild.emojis:
            message = message + f'{str(emoji.id)} **-** {emoji}\n'
        icons_message = discord.Embed()
        icons_message.colour = self.bot.utils.color.success()
        icons_message.set_author(name='Guild\'s Icons', icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        icons_message.description = message
        icons_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                 icon_url=self.bot.cfg.get('Images.FooterIconURL'))

        await ctx.send(embed=icons_message, delete_after=60)

    @commands.command(case_insensitive=True)
    @commands.guild_only()
    @checks.is_guild_owner()
    async def roles(self, ctx: commands.Context):
        message = str()
        for role in ctx.guild.roles:
            message = message + f'{str(role.id)} **-** {role.mention}\n'
        roles_message = discord.Embed()
        roles_message.colour = self.bot.utils.color.success()
        roles_message.set_author(name='Guild\'s Roles', icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        roles_message.description = message
        roles_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                 icon_url=self.bot.cfg.get('Images.FooterIconURL'))

        await ctx.send(embed=roles_message, delete_after=60)

    @commands.command(case_insensitive=True)
    @commands.guild_only()
    @checks.is_guild_owner()
    async def search(self, ctx: commands.Context, channel: discord.TextChannel, word):
        start = time.time()
        result_channel = ctx.bot.utils.channel.search()
        result_channel.delete_messages()
        async for message in result_channel.history(limit=None):
            await message.delete()
        counter = 0
        async for message in channel.history(limit=None, reverse=True):
            if message.content.lower().__contains__(word.lower()):
                await result_channel.send(message.content)
                counter += 1
        await ctx.channel.send(f'Fetch **{counter}** results in {time.time() - start} seconds!')

    @commands.command(case_insensitive=True)
    @commands.guild_only()
    @checks.is_guild_owner()
    async def setup(self, ctx: commands.Context):

        for member in ctx.bot.guilds[0].members:
            if member.bot:
                continue
            await member.add_roles(self.bot.utils.role.user(), reason='Add all')
            if self.bot.db.user.receive_notification(member):
                await member.add_roles(self.bot.utils.role.notification(), reason='Add all')

        home_channel = ctx.bot.utils.channel.home()
        async for message in home_channel.history():
            await message.delete()
        home_message = discord.Embed()
        home_message.colour = discord.Colour.dark_blue()
        home_message.set_author(name='Easy System Support', url='https://Luc1412.de',
                                icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        home_message.description = 'Welcome to Easy System Support!\n' \
                                   'Here you get support and updates for all EasySystem products.'
        home_message \
            .add_field(name='Rules',
                       value=f'**1.** Ask only for support or join the Wait for Support Channel if you need support.\n'
                             f'**2.** Be friendly and respectful! Don\'t send pornographic, racist, sexist or '
                             f'offensive content!\n '
                             f'**3.** **2nd Rule** is also valid for the avatar, name and game-name!\n'
                             f'**4.** Don\'t spam or write in caps!\n'
                             f'**5.** Advertisement is currently in every form forbidden! Also in private messages!\n'
                             f'**6.** Follow Discord\'s [Terms of Service](https://discordapp.com/terms),'
                             f' [Community Guidelines](https://discordapp.com/guidelines) and your countries laws\n'
                             f'**7.** Directions of {ctx.bot.utils.role.team().mention} are followed and not '
                             f'circumvented')
        home_message.set_footer(text='Last Update',
                                icon_url=self.bot.cfg.get('Images.FooterIconURL'))
        home_message.timestamp = datetime.datetime(2018, 10, 20, 14, 0)
        await home_channel.send(embed=home_message)

        s_channel = ctx.bot.utils.channel.settings()
        async for message in s_channel.history():
            await message.delete()
        notify_message = discord.Embed()
        notify_message.colour = self.bot.utils.color.select()
        notify_message.set_author(name='Notification', icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        notify_message.set_thumbnail(url='https://server.luc1412.de/img/bell.png')
        notify_message.description = f'**Click {self.bot.utils.icon.switch()} to toggle notification!**\n\n' \
                                     f'If you enable it, you will be pinged if there is a new update from ' \
                                     f'**EasySystem** or **EasyFortniteStats**\n\n' \
                                     f'ℹ️*This setting has a 30 seconds Cooldown!*'
        notify_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                  icon_url=self.bot.cfg.get('Images.FooterIconURL'))
        message = await s_channel.send(embed=notify_message)
        await message.add_reaction(ctx.bot.utils.icon.switch())

    @commands.command(case_insensitive=True)
    @commands.guild_only()
    @checks.is_guild_owner()
    async def restart(self, ctx: commands.Context):
        import sys
        restart_message = discord.Embed()
        restart_message.colour = ctx.bot.utils.color.fail()
        restart_message.description = 'Bot reboots in 3 seconds...'
        await ctx.send(embed=restart_message)
        await asyncio.sleep(3)
        ctx.bot.info('Restart Bot...')
        sys.exit()

    @commands.command(case_insensitive=True)
    @commands.guild_only()
    @checks.is_guild_owner()
    async def update(self, ctx: commands.Context):
        select_message = discord.Embed()
        select_message.colour = ctx.bot.utils.color.select()
        select_message.set_author(name='Update Assistant', icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        select_message.description = f'__**In which channel should the update be sent?**__\n\n' \
                                     f'{self.bot.utils.icon.general()} **- General Update**\n' \
                                     f'{self.bot.utils.icon.efs_logo()} **- EasyFortniteStats**\n\n' \
                                     f'Use {ctx.bot.utils.icon.fail()} to abort selection!'
        select_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                  icon_url=self.bot.cfg.get('Images.FooterIconURL'))
        message = await ctx.send(embed=select_message)
        await message.add_reaction(self.bot.utils.icon.fail())
        for reaction in UpdateType.list():
            await message.add_reaction(reaction.replace('%general_icon%', str(ctx.bot.utils.icon.general()))
                                       .replace('%efs_icon%', str(ctx.bot.utils.icon.efs_logo()))
                                       .replace('>', '').replace('<', ''))

            def check(reaction, user):
                emoji = str(reaction.emoji).replace(str(ctx.bot.utils.icon.general()), '%general_icon%') \
                    .replace(str(ctx.bot.utils.icon.efs_logo()), '%efs_icon%')
                return user is ctx.author and (emoji or reaction.emoji is self.bot.utils.icon.fail())

        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            select_message.colour = ctx.bot.utils.color.fail()
            select_message.set_author(name='Channel selection canceled!',
                                      icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
            select_message.description = 'The Channel selection was aborted after one minute!'
            select_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                      icon_url=self.bot.cfg.get('Images.FooterIconURL'))
            await message.edit(embed=select_message)
        else:
            await message.clear_reactions()
            if reaction.emoji is self.bot.utils.icon.fail():
                await self.selection_cancel(ctx, message)
                return

            channel = UpdateType.get_by_reaction(str(reaction.emoji)
                                                 .replace(str(ctx.bot.utils.icon.general()), '%general_icon%')
                                                 .replace(str(ctx.bot.utils.icon.efs_logo()), '%efs_icon%'))

            select_message.description = 'Channel successfully selected!\n\n' \
                                         '**Please enter the update title**\n\n' \
                                         'Reply with \'cancel\' to cancel'
            await message.edit(embed=select_message)

            def check(user_input):
                return user_input.author is ctx.author

            try:
                user_input = await ctx.bot.wait_for('message', timeout=60.0, check=check)
                await user_input.delete()
            except asyncio.TimeoutError:
                select_message.colour = ctx.bot.utils.color.fail()
                select_message.set_author(name='Description input canceled!',
                                          icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
                select_message.description = 'The Description input was aborted after one minute!'
                select_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                          icon_url=self.bot.cfg.get('Images.FooterIconURL'))
                await message.edit(embed=select_message)
            else:
                if user_input.content.lower() == 'cancel':
                    await self.selection_cancel(ctx, message)
                    return

                title = user_input.content

                select_message.description = 'Title successfully set!\n\n' \
                                             '**Please enter the update description**\n\n' \
                                             'Reply with \'cancel\' to cancel'
                await message.edit(embed=select_message)

                def check(user_input):
                    return user_input.author is ctx.author

                try:
                    user_input = await ctx.bot.wait_for('message', timeout=600.0, check=check)
                    await user_input.delete()
                except asyncio.TimeoutError:
                    select_message.colour = ctx.bot.utils.color.fail()
                    select_message.set_author(name='Description input canceled!',
                                              icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
                    select_message.description = 'The Description input was aborted after one minute!'
                    select_message.set_footer(text='', icon_url='')
                    await message.edit(embed=select_message)
                else:
                    if user_input.content.lower() == 'cancel':
                        await self.selection_cancel(ctx, message)
                        return

                    description = user_input.content

                    select_message.description = 'Description successfully set!\n\n' \
                                                 '**Please enter the image url.** ' \
                                                 'For no image enter \'none\' for no image.\n\n' \
                                                 'Reply with \'cancel\' to cancel'
                    await message.edit(embed=select_message)

                    def check(user_input):
                        return user_input.author is ctx.author

                    try:
                        user_input = await ctx.bot.wait_for('message', timeout=60.0, check=check)
                        await user_input.delete()
                    except asyncio.TimeoutError:
                        select_message.colour = ctx.bot.utils.color.fail()
                        select_message.set_author(name='Image input canceled!',
                                                  icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
                        select_message.description = 'The image input was aborted after one minute!'
                        select_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                                  icon_url=self.bot.cfg.get('Images.FooterIconURL'))
                        await message.edit(embed=select_message)
                    else:
                        if user_input.content.lower() == 'cancel':
                            await self.selection_cancel(ctx, message)
                            return

                        image_url = None if user_input.content == 'none' else user_input.content

                        update_message = discord.Embed()
                        update_message.colour = discord.Colour.blurple()
                        update_message.set_author(name=title,
                                                  url=discord.Embed.Empty
                                                  if channel is not UpdateType.EfsUpdate
                                                  else 'https://Luc1412.de/efs-update',
                                                  icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
                        update_message.description = description
                        if image_url:
                            update_message.set_image(url=image_url)
                        update_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                                  icon_url=self.bot.cfg.get('Images.FooterIconURL'))
                        update_message.timestamp = datetime.datetime.now()
                        await message.edit(embed=update_message,
                                           content=f'Use {ctx.bot.utils.icon.success()} to send update! '
                                                   f'(Use {ctx.bot.utils.icon.fail()} to cancel)')
                        await message.add_reaction(ctx.bot.utils.icon.success())
                        await message.add_reaction(ctx.bot.utils.icon.fail())

                        def check(reaction, user):
                            return user is ctx.author and (reaction.emoji.id is ctx.bot.utils.icon.success().id or
                                                           reaction.emoji.id is ctx.bot.utils.icon.fail().id)

                        try:
                            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=600.0, check=check)
                        except asyncio.TimeoutError:
                            await message.clear_reactions()
                            select_message.timestamp = None
                            select_message.colour = ctx.bot.utils.color.fail()
                            select_message.set_author(name='Image input canceled!',
                                                      icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
                            select_message.description = 'The image input was aborted after one minute!'
                            select_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                                      icon_url=self.bot.cfg.get('Images.FooterIconURL'))
                            await message.edit(embed=select_message)
                        else:
                            await message.clear_reactions()
                            if reaction.emoji is self.bot.utils.icon.fail():
                                await self.selection_cancel(ctx, message)
                                return
                            elif reaction.emoji is self.bot.utils.icon.success():
                                update_role = ctx.bot.utils.role.notification()
                                await update_role.edit(mentionable=True, reason='Update mention')

                                if channel is UpdateType.GeneralUpdate:
                                    await ctx.bot.utils.channel.general_update().send(content=update_role.mention,
                                                                                      embed=update_message)
                                elif channel is UpdateType.EfsUpdate:
                                    await ctx.bot.utils.channel.efs_update().send(content=update_role.mention,
                                                                                  embed=update_message)

                                await update_role.edit(mentionable=False, reason='Update mention')

                                select_message.colour = ctx.bot.utils.color.success()
                                select_message.description = f'{ctx.bot.utils.icon.success()} Update successfully sent!'
                                await message.edit(content=None, embed=select_message)


def setup(bot):
    bot.add_cog(AdminCommands(bot))
