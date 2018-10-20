import discord

from bot import Bot


class Events:

    def __init__(self, bot: Bot):
        self.bot = bot

    async def on_member_join(self, member: discord.Member):
        join_message = discord.Embed()
        join_message.colour = self.bot.utils.color.success()
        join_message.set_author(name='Welcome on EasySystem Support!', icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        join_message.set_author(name='Welcome on EasySystem Support!', icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
        join_message.set_thumbnail(url=member.avatar_url)
        join_message.description = f'Please visit {self.bot.utils.channel.home().mention} for rules.\n' \
                                   f'If you don\'t want to get any permissions from the server, go to ' \
                                   f'{self.bot.utils.channel.settings().mention} and turn it off'
        join_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                icon_url=self.bot.cfg.get('Images.FooterIconURL'))

        await self.bot.utils.channel.general().send(content=member.mention, embed=join_message)
        await member.add_roles(self.bot.utils.role.user(), reason='User Joined')
        if self.bot.db.user.receive_notification(member):
            await member.add_roles(self.bot.utils.role.notification(), reason='Notification Joined')

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        channel = self.bot.get_channel(payload.channel_id)
        user = self.bot.get_user(payload.user_id)
        member = self.bot.guilds[0].get_member(payload.user_id)
        message = await channel.get_message(payload.message_id)
        if user.bot:
            return
        if channel is not self.bot.utils.channel.settings():
            return
        await message.remove_reaction(payload.emoji, user)
        if payload.emoji.id == self.bot.utils.icon.switch().id:
            if self.bot.utils.countdown.check(user):
                return
            self.bot.utils.countdown.add(user)
            change_message = discord.Embed()
            change_message.set_author(name='Successfully changed notifications!',
                                      icon_url=self.bot.cfg.get('Images.IconSmallUrl'))
            change_message.set_thumbnail(url='https://server.luc1412.de/img/bell.png')
            change_message.set_footer(text=self.bot.cfg.get('Core.Footer'),
                                      icon_url=self.bot.cfg.get('Images.FooterIconURL'))
            if self.bot.db.user.receive_notification(user):

                self.bot.db.user.set_receive_notification(user, False)
                change_message.colour = self.bot.utils.color.fail()
                change_message.description = f'~~**------------------------------------------------**~~\n' \
                                             f'{self.bot.utils.icon.fail()} Successfully **DISABLED** notifications!\n' \
                                             f'~~**------------------------------------------------**~~'
                await member.remove_roles(self.bot.utils.role.notification(), reason='Disabled Notifications')
            else:
                self.bot.db.user.set_receive_notification(user, True)
                change_message.colour = self.bot.utils.color.success()
                change_message.description \
                    = f'~~**------------------------------------------------**~~\n' \
                      f'{self.bot.utils.icon.success()} Successfully **ENABLED** notifications!\n' \
                      f'~~**------------------------------------------------**~~'
                await member.add_roles(self.bot.utils.role.notification(), reason='Enabled Notifications')
            await user.send(embed=change_message)


def setup(bot):
    bot.add_cog(Events(bot))
