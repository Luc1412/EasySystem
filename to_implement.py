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

