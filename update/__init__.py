from typing import TYPE_CHECKING

from update.update import Update

if TYPE_CHECKING:
    from redbot.core.bot import Red


async def setup(bot: "Red"):
    await bot.add_cog(Update(bot))
