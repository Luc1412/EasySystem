import time
from enum import Enum

import discord


class Utils:

    def __init__(self, bot):
        self.bot = bot

        self.channel = Channel(bot)
        self.color = Color()
        self.icon = Icon(bot)
        self.role = Role(bot)
        self.countdown = CountdownManager()


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

    def general(self):
        emoji_id = int(self.bot.cfg.get('Icons.General'))
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

    def search(self):
        channel_id = int(self.bot.cfg.get('Channel.Search'))
        return self.bot.get_channel(channel_id)


class Role:

    def __init__(self, bot):
        self.bot = bot

    def user(self):
        role_id = int(self.bot.cfg.get('Roles.User'))
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


class CountdownManager:

    def __init__(self):
        self.countdown_list = dict()

    def add(self, user: discord.User):
        self.countdown_list[user] = time.time()

    def check(self, user: discord.User):
        if user not in self.countdown_list:
            return False
        value = (self.countdown_list[user] + 30) >= time.time()
        if not value:
            del self.countdown_list[user]
        return value


class UpdateType(Enum):
    GeneralUpdate = '%general_icon%'
    EfsUpdate = '%efs_icon%'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, UpdateType))

    @staticmethod
    def get_by_reaction(reaction: str):
        for lang_item in UpdateType.list():
            if lang_item == reaction:
                return UpdateType(lang_item)
        return None
