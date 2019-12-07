import datetime
import typing

import discord
import io
import time
from discord.ext import commands

from bot import EasySystem
from utils.context import Context
from utils.selection import SelectionInterface, SelectionType, ReplacedText


class AdminCommands(commands.Cog):

    def __init__(self, bot: EasySystem):
        self.bot = bot
        self._last_result = None

    @staticmethod
    def cleanup_code(content):
        """Automatically removed code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @commands.command(case_insensitive=True)
    @commands.guild_only()
    @commands.is_owner()
    async def setup(self, ctx: commands.Context):

        return

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
        update_notify_message = discord.Embed()
        update_notify_message.colour = self.bot.utils.color.select()
        update_notify_message.set_author(name='Notification', icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        update_notify_message.description = f'**Click {self.bot.utils.icon.switch()} to toggle notification!**\n\n' \
                                            f'If you enable it, you will be pinged if there is a new update from ' \
                                            f'**EasySystem** or **EasyFortniteStats**\n\n' \
                                            f':information_source: *This setting has a 30 seconds Cooldown!*'
        update_notify_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                         icon_url=self.bot.cfg.get('Images.FooterIconURL'))
        message = await s_channel.send(embed=update_notify_message)
        await message.add_reaction(ctx.bot.utils.icon.switch())

        auto_channel_message = discord.Embed()
        auto_channel_message.colour = self.bot.utils.color.select()
        auto_channel_message.set_author(name='Auto Channel Notification',
                                        icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        auto_channel_message.set_thumbnail(url='https://i.imgur.com/0uhRrdP.png')
        auto_channel_message.description = f'**React with Emoji to toggle Auto Channel Notifications.**\n\n' \
                                           f':shopping_cart: **-** Toggle Auto Shop Notifications\n' \
                                           f'{self.bot.utils.icon.challenges()} **-** Toggle Auto Shop Notifications\n\n' \
                                           f':information_source: *This setting has a 30 seconds Cooldown!*'
        auto_channel_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                        icon_url=self.bot.cfg.get('Images.FooterIconURL'))
        message = await s_channel.send(embed=auto_channel_message)
        await message.add_reaction('🛒')
        await message.add_reaction(self.bot.utils.icon.challenges())

    @commands.command(case_insensitive=True)
    @commands.guild_only()
    @commands.is_owner()
    async def update(self, ctx: commands.Context):
        selection = SelectionInterface(ctx, timeout=600)

        type_selection = selection.set_base_selection(SelectionType.REACTION,
                                                      'Select type',
                                                      f'**In which channel should the update be sent?**\n\n'
                                                      f'{self.bot.utils.icon.announcement()} **- General Update**\n'
                                                      f'{self.bot.utils.icon.efs_logo()} **- EasyFortniteStats**\n'
                                                      f'{self.bot.utils.icon.ess_logo()} **- EasyServerStats**\n',
                                                      reactions=[self.bot.utils.icon.announcement(),
                                                                 self.bot.utils.icon.efs_logo(),
                                                                 self.bot.utils.icon.ess_logo()])

        title_selection = type_selection.add_result('*', SelectionType.TEXT, 'Select Title',
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
                                                            '\U0001f514 **- Enable Notification**\n'
                                                            '\U0001f515 **- Disable Notification**',
                                                            reactions=['\U0001f514', '\U0001f515'])

        def f1(result):
            return result[1]

        def f2(result):
            return result[2]

        def f3(result):
            return result[3]

        submit_selection = notification_selection.add_result('*',
                                                             SelectionType.CONFIRM_SELECTION, ReplacedText('{}', f1),
                                                             ReplacedText('▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n{}', f2),
                                                             color=discord.Color.blurple(),
                                                             image=ReplacedText('{}', f3))

        async def a(context, result):
            update_message = discord.Embed()
            update_message.set_author(name=result[1])
            update_message.colour = discord.Color.blurple()
            update_message.description = f'▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n{result[2]}'

            update_role = context.utils.role.notification()
            await update_role.edit(mentionable=True, reason='Update mention')

            channel = None
            if str(selection.result()[0]) == str(self.bot.utils.icon.announcement()):
                channel = context.utils.channel.general_update()
            elif str(selection.result()[0]) == str(self.bot.utils.icon.efs_logo()):
                channel = context.utils.channel.efs_update()
            elif str(selection.result()[0]) == str(self.bot.utils.icon.ess_logo()):
                channel = context.utils.channel.ess_update()

            await channel.send(content=update_role.mention if selection.result()[4] == '\U0001f514' else None,
                               embed=update_message)
            await update_role.edit(mentionable=False, reason='Update mention')

        submit_selection.set_action(a)

        submit_selection.add_result('*', SelectionType.SUCCESS, 'Update successfully',
                                    ':white_check_mark: Update successfully sent!')

        await selection.start()

    @commands.command()
    @commands.is_owner()
    async def emoji(self, ctx: Context, action: str, name_or_id: typing.Union[str, int] = None):
        emoji_guild = ctx.bot.get_guild(652557455749939210)
        if action == 'list':
            emoji_message = ''
            for emoji in emoji_guild.emojis:
                emoji_message += f'{emoji} **-** `{emoji.id}`\n'
            if len(emoji_guild.emojis) == 0:
                emoji_message = 'No emoji on the emoji server.'
            message = discord.Embed()
            message.colour = discord.Color.dark_magenta()
            message.title = 'Easy System Emoji'
            message.description = emoji_message
            await ctx.send(embed=message)
        elif action == 'add':
            if name_or_id is None:
                return await ctx.bot.send_error(ctx, 'Please provide a emoji name')
            if len(ctx.message.attachments) != 1:
                return await ctx.bot.send_error(ctx, 'If you want to add a emoji you need to upload a file.')
            image = await ctx.message.attachments[0].read()
            try:
                emoji = await emoji_guild.create_custom_emoji(name=name_or_id, image=image)
            except discord.HTTPException as e:
                return await ctx.bot.send_error(ctx, f'An error occurred: {e.text}')

            message = discord.Embed()
            message.colour = discord.Color.green()
            message.set_thumbnail(url=emoji.url)
            message.description = f'Successfully created emoji with the name **{emoji.name}** and the id `{emoji.id}`'
            await ctx.send(embed=message)
        elif action == 'remove':
            if name_or_id is None:
                return await ctx.bot.send_error(ctx, 'Please provide a emoji id')
            try:
                emoji = await emoji_guild.fetch_emoji(name_or_id)
            except discord.NotFound:
                return await ctx.bot.send_error(ctx, 'The given emoji wasn\'t found!')
            await emoji.delete()

            message = discord.Embed()
            message.colour = discord.Color.dark_red()
            message.set_thumbnail(url=emoji.url)
            message.description = f'Successfully deleted emoji with the name **{emoji.name}** and the id `{emoji.id}`'
            await ctx.send(embed=message)
        else:
            return await ctx.bot.send_error(ctx, 'Please use `!emoji <list/add/remove> [name or id]`')

    @commands.command()
    @commands.is_owner()
    async def eval(self, ctx: commands.Context, *, body: str):
        import textwrap
        from contextlib import redirect_stdout
        import traceback

        """Evaluates a code"""

        env = {
            'bot': ctx.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'
        time1 = time.time()
        try:
            exec (to_compile, env)
        except Exception as e:
            await ctx.bot.send_error(ctx, message=f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.bot.send_error(ctx, message=f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()

            time2 = time.time()

            eval_message = discord.Embed()
            eval_message.colour = ctx.bot.utils.color.success()
            eval_message.set_author(name='Code Eval', icon_url=ctx.bot.cfg.get('Images.IconSmallURL'))
            eval_message.set_footer(
                text=f'Took {time2 - time1:.2f} seconds to execute',
                icon_url=ctx.bot.cfg.get('Images.FooterIconURL'))

            if ret is None:
                if value:
                    eval_message.description = f'\n📥 **Input:**\n' \
                                               f'```py\n{body}```\n\n' \
                                               f'📤 **Output:**\n' \
                                               f'```py\n{value}\n```'
            else:
                self._last_result = ret
                eval_message.description = f'\n📥 **Input:**\n' \
                                           f'```py\n{body}```\n\n' \
                                           f'📤 **Output:**\n' \
                                           f'```py\n{value}{ret}\n```'

            await ctx.send(embed=eval_message)

    @commands.command()
    @commands.guild_only()
    async def agree(self, ctx: commands.Context):
        return
        if ctx.author.roles.__contains__(ctx.bot.utils.role.user()):
            return
        join_message = discord.Embed()
        join_message.colour = self.bot.utils.color.success()
        join_message.set_author(name='Welcome on EasySystem Support!', icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        join_message.set_thumbnail(url=ctx.author.avatar_url)
        join_message.description = f'Please visit {self.bot.utils.channel.home().mention} for rules.\n' \
                                   f'If you don\'t want to get any notification from the server, go to ' \
                                   f'{self.bot.utils.channel.settings().mention} and turn it off'
        join_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                icon_url=self.bot.cfg.get('Images.FooterIconURL'))

        await self.bot.utils.channel.general().send(content=ctx.author.mention, embed=join_message)
        if await self.bot.db.users.receive_notification(ctx.author):
            await ctx.author.add_roles(self.bot.utils.role.notification(), reason='Notification Joined')
        if await self.bot.db.users.receive_shop_notification(ctx.author):
            await ctx.author.add_roles(self.bot.utils.role.shop(), reason='Shop Notification Joined')
        if await self.bot.db.users.receive_challenges_notification(ctx.author):
            await ctx.author.add_roles(self.bot.utils.role.challenges(), reason='Challenges Notification Joined')

    @commands.command(aliases=['fortnite', 'efs', 'apex', 'eas', 'suggest', 'fm', 'ftn'])
    @commands.guild_only()
    async def fn(self, ctx: commands.Context):
        if ctx.channel is ctx.bot.utils.channel.commands() or ctx.channel is ctx.bot.utils.channel.admin_commands():
            return
        command_message = discord.Embed()
        command_message.colour = self.bot.utils.color.success()
        command_message.set_author(name='Commands not allowed!', icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        command_message.description = f'Please go in {ctx.bot.utils.channel.commands().mention} to use commands.'
        command_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                   icon_url=self.bot.cfg.get('Images.FooterIconURL'))

        await ctx.send(embed=command_message, delete_after=15)
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(AdminCommands(bot))
