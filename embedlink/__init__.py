from typing import TYPE_CHECKING

from embedlink.embedlink import EmbedLink

if TYPE_CHECKING:
    from redbot.core.bot import Red


async def setup(bot: "Red"):
    await bot.add_cog(EmbedLink(bot))
