from redbot.core import Config
from redbot.core.commands import commands, Context

from update.update import BaseCog


class EmojiManager(BaseCog):
    """"""

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, 782392998)
        default_global_settings = {
            "emoji_server_ids": []
        }
        self.settings.register_global(**default_global_settings)

    @commands.group(name='emoji')
    async def _emoji(self, ctx: Context):
        """"""
        pass

    @_emoji.command(name='add')
    async def _emoji_add(self, ctx: Context, name: str):
        """"""
        pass

    @_emoji.command(name='remove')
    async def _emoji_remove(self, ctx: Context, name: str):
        """"""
        pass

    @_emoji.command(name='list')
    async def _emoji_list(self, ctx: Context):
        """"""
        pass

    @commands.command(name='emojiset')
    async def _emojiset(self, ctx: Context):
        """"""
        pass
