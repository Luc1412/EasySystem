from typing import TYPE_CHECKING

from easyfnstats.easyfnstats import EasyFnStats

if TYPE_CHECKING:
    from redbot.core.bot import Red


async def setup(bot: "Red"):
    await bot.add_cog(EasyFnStats(bot))
