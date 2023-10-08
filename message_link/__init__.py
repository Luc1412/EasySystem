from typing import TYPE_CHECKING

from message_link.message_link import MessageLink

if TYPE_CHECKING:
    from redbot.core.bot import Red


async def setup(bot: "Red"):
    await bot.add_cog(MessageLink(bot))
