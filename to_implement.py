import datetime

import discord
from discord.ext import commands


async def setup(self, ctx: commands.Context):

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

@commands.Cog.listener()
async def on_member_join(self, member: discord.Member):
    if member.bot:
        return

    join_message = discord.Embed()
    join_message.colour = self.bot.utils.color.success()
    join_message.set_author(name='Welcome on EasySystem Support!', icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
    join_message.set_thumbnail(url=member.avatar_url)
    join_message.description = f'Please visit {self.bot.utils.channel.home().mention} for rules.\n' \
                               f'If you don\'t want to get any notification from the server, go to ' \
                               f'{self.bot.utils.channel.settings().mention} and turn it off'
    join_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                            icon_url=self.bot.cfg.get('Images.FooterIconURL'))

    await self.bot.utils.channel.general().send(content=member.mention, embed=join_message)
    if await self.bot.db.users.receive_notification(member):
        await member.add_roles(self.bot.utils.role.notification(), reason='Notification Joined')
    if await self.bot.db.users.receive_shop_notification(member):
        await member.add_roles(self.bot.utils.role.shop(), reason='Shop Notification Joined')
    if await self.bot.db.users.receive_challenges_notification(member):
        await member.add_roles(self.bot.utils.role.challenges(), reason='Challenges Notification Joined')

@commands.Cog.listener()
async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
    channel = self.bot.get_channel(payload.channel_id)
    member = self.bot.guilds[0].get_member(payload.user_id)
    message = await channel.fetch_message(payload.message_id)
    if member.bot:
        return
    if channel is not self.bot.utils.channel.settings():
        return
    await message.remove_reaction(payload.emoji, member)
    if str(payload.emoji) == '🛒':
        change_message = discord.Embed()
        change_message.set_author(name='Successfully changed Auto Shop Notifications!',
                                  icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        change_message.set_thumbnail(url='https://i.imgur.com/LLZHCWN.png')
        change_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                  icon_url=self.bot.cfg.get('Images.FooterIconURL'))
        if await self.bot.db.users.receive_shop_notification(member):
            await self.bot.db.users.set_receive_shop_notification(member, False)
            change_message.colour = self.bot.utils.color.fail()
            change_message.description \
                = f'~~**------------------------------------------------**~~\n' \
                  f'{self.bot.utils.icon.fail()} Successfully **DISABLED** Shop notifications!\n' \
                  f'~~**------------------------------------------------**~~'
            await member.remove_roles(self.bot.utils.role.shop(), reason='Disabled Shop Notifications')
        else:
            await self.bot.db.users.set_receive_shop_notification(member, True)
            change_message.colour = self.bot.utils.color.success()
            change_message.description \
                = f'~~**------------------------------------------------**~~\n' \
                  f'{self.bot.utils.icon.success()} Successfully **ENABLED** Shop notifications!\n' \
                  f'~~**------------------------------------------------**~~'
            await member.add_roles(self.bot.utils.role.shop(), reason='Enabled Shop Notifications')
        await member.send(embed=change_message)
    elif payload.emoji.id == self.bot.utils.icon.challenges().id:
        change_message = discord.Embed()
        change_message.set_author(name='Successfully changed Auto Challenge Notifications!',
                                  icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        change_message.set_thumbnail(url='')
        change_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                  icon_url=self.bot.cfg.get('Images.FooterIconURL'))
        if await self.bot.db.users.receive_challenges_notification(member):
            await self.bot.db.users.set_receive_challenges_notification(member, False)
            change_message.colour = self.bot.utils.color.fail()
            change_message.description \
                = f'~~**------------------------------------------------**~~\n' \
                  f'{self.bot.utils.icon.fail()} Successfully **DISABLED** Challenges notifications!\n' \
                  f'~~**------------------------------------------------**~~'
            await member.remove_roles(self.bot.utils.role.challenges(), reason='Disabled Challenges Notifications')
        else:
            await self.bot.db.users.set_receive_challenges_notification(member, True)
            change_message.colour = self.bot.utils.color.success()
            change_message.description \
                = f'~~**------------------------------------------------**~~\n' \
                  f'{self.bot.utils.icon.success()} Successfully **ENABLED** Challenges notifications!\n' \
                  f'~~**------------------------------------------------**~~'
            await member.add_roles(self.bot.utils.role.challenges(), reason='Enabled Challenges Notifications')
        await member.send(embed=change_message)
    elif payload.emoji.id == self.bot.utils.icon.switch().id:
        change_message = discord.Embed()
        change_message.set_author(name='Successfully changed notifications!',
                                  icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        change_message.set_thumbnail(url='')
        change_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                  icon_url=self.bot.cfg.get('Images.FooterIconURL'))
        if await self.bot.db.users.receive_notification(member):
            await self.bot.db.users.set_receive_notification(member, False)
            change_message.colour = self.bot.utils.color.fail()
            change_message.description = f'~~**------------------------------------------------**~~\n' \
                                         f'{self.bot.utils.icon.fail()} Successfully **DISABLED** notifications!\n' \
                                         f'~~**------------------------------------------------**~~'
            await member.remove_roles(self.bot.utils.role.notification(), reason='Disabled Notifications')
        else:
            await self.bot.db.users.set_receive_notification(member, True)
            change_message.colour = self.bot.utils.color.success()
            change_message.description \
                = f'~~**------------------------------------------------**~~\n' \
                  f'{self.bot.utils.icon.success()} Successfully **ENABLED** notifications!\n' \
                  f'~~**------------------------------------------------**~~'
            await member.add_roles(self.bot.utils.role.notification(), reason='Enabled Notifications')
        await member.send(embed=change_message)
    elif payload.emoji.id == self.bot.utils.icon.ess_logo().id:
        pass

@commands.Cog.listener()
async def on_message(self, message: discord.Message):
    if message.channel is self.bot.utils.channel.music():
        if message.author is message.guild.me:
            return
        await asyncio.sleep(30)
        try:
            await message.delete()
        except discord.NotFound:
            pass