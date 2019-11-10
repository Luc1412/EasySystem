from discord.ext import commands


class Context(commands.Context):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def cfg(self):
        return self.bot.cfg

    @property
    def db(self):
        return self.bot.db

    @property
    def utils(self):
        return self.bot.utils

    @property
    def logger(self):
        return self.bot.logger

    @property
    def scheduler(self):
        return self.bot.get_cog('ScheduleManager')

    @property
    def storage(self):
        return self.bot.get_cog('StorageManager')
