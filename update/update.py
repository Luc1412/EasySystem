from redbot.core import Config
from redbot.core.commands import commands, Context

BaseCog = getattr(commands, "Cog", object)


class Update(BaseCog):
    """

    """

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, 4695331128)
        default_guild_settings = {

        }
        self.settings.register_guild(**default_guild_settings)

    @commands.command(name='update')
    async def _update(self, ctx: Context):
        pass

