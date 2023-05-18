from typing import TYPE_CHECKING

from suggestions.suggestions import Suggestions

if TYPE_CHECKING:
    from redbot.core.bot import Red


async def setup(bot: "Red"):
    await bot.add_cog(Suggestions(bot))
