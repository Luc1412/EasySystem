import asyncio
import discord
from discord.ext import commands

from bot import EasySystem


class Events(commands.Cog):

    def __init__(self, bot: EasySystem):
        self.bot = bot

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


def setup(bot):
    bot.add_cog(Events(bot))
