import discord
import time
from enum import Enum


class Utils:

    def __init__(self, bot):
        self.bot = bot

        self.channel = Channel(bot)
        self.color = Color()
        self.icon = Icon(bot)
        self.role = Role(bot)

    @staticmethod
    def format_username(user: discord.User):
        return f'{user.name}#{user.discriminator}'


class Icon:

    def __init__(self, bot):
        self.bot = bot

    def fail(self):
        emoji_id = int(self.bot.cfg.get('Icons.Fail'))
        return self.bot.get_emoji(emoji_id)

    def success(self):
        emoji_id = int(self.bot.cfg.get('Icons.Success'))
        return self.bot.get_emoji(emoji_id)

    def switch(self):
        emoji_id = int(self.bot.cfg.get('Icons.Switch'))
        return self.bot.get_emoji(emoji_id)

    def efs_logo(self):
        emoji_id = int(self.bot.cfg.get('Icons.EfsLogo'))
        return self.bot.get_emoji(emoji_id)

    def ess_logo(self):
        emoji_id = int(self.bot.cfg.get('Icons.EasyServerStats'))
        return self.bot.get_emoji(emoji_id)

    def general(self):
        emoji_id = int(self.bot.cfg.get('Icons.General'))
        return self.bot.get_emoji(emoji_id)

    def challenges(self):
        emoji_id = int(self.bot.cfg.get('Icons.Challenges'))
        return self.bot.get_emoji(emoji_id)


class Channel:

    def __init__(self, bot):
        self.bot = bot

    def home(self):
        channel_id = int(self.bot.cfg.get('Channel.Home'))
        return self.bot.get_channel(channel_id)

    def general(self):
        channel_id = int(self.bot.cfg.get('Channel.General'))
        return self.bot.get_channel(channel_id)

    def settings(self):
        channel_id = int(self.bot.cfg.get('Channel.Settings'))
        return self.bot.get_channel(channel_id)

    def general_update(self):
        channel_id = int(self.bot.cfg.get('Channel.GeneralUpdate'))
        return self.bot.get_channel(channel_id)

    def efs_update(self):
        channel_id = int(self.bot.cfg.get('Channel.EfsUpdate'))
        return self.bot.get_channel(channel_id)

    def ess_update(self):
        channel_id = int(self.bot.cfg.get('Channel.EssUpdate'))
        return self.bot.get_channel(channel_id)

    def search(self):
        channel_id = int(self.bot.cfg.get('Channel.Search'))
        return self.bot.get_channel(channel_id)

    def public_log(self):
        channel_id = int(self.bot.cfg.get('Channel.PublicLog'))
        return self.bot.get_channel(channel_id)

    def commands(self):
        channel_id = int(self.bot.cfg.get('Channel.Commands'))
        return self.bot.get_channel(channel_id)

    def admin_commands(self):
        channel_id = int(self.bot.cfg.get('Channel.AdminCommands'))
        return self.bot.get_channel(channel_id)

    def music(self):
        channel_id = int(self.bot.cfg.get('Channel.Music'))
        return self.bot.get_channel(channel_id)


class Role:

    def __init__(self, bot):
        self.bot = bot

    def user(self):
        role_id = int(self.bot.cfg.get('Roles.User'))
        return self.bot.guilds[0].get_role(role_id)

    def split(self):
        role_id = int(self.bot.cfg.get('Roles.Split'))
        return self.bot.guilds[0].get_role(role_id)

    def notification(self):
        role_id = int(self.bot.cfg.get('Roles.Notification'))
        return self.bot.guilds[0].get_role(role_id)

    def banned(self):
        role_id = int(self.bot.cfg.get('Roles.Banned'))
        return self.bot.guilds[0].get_role(role_id)

    def team(self):
        role_id = int(self.bot.cfg.get('Roles.Team'))
        return self.bot.guilds[0].get_role(role_id)

    def shop(self):
        role_id = int(self.bot.cfg.get('Roles.Shop'))
        return self.bot.guilds[0].get_role(role_id)

    def challenges(self):
        role_id = int(self.bot.cfg.get('Roles.Challenges'))
        return self.bot.guilds[0].get_role(role_id)


class Color:

    @staticmethod
    def fail():
        return discord.Colour.from_rgb(194, 54, 22)

    @staticmethod
    def success():
        return discord.Colour.from_rgb(39, 174, 96)

    @staticmethod
    def warn():
        return discord.Colour.from_rgb(241, 196, 15)

    @staticmethod
    def select():
        return discord.Colour.from_rgb(0, 98, 102)
