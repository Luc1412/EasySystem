from typing import TYPE_CHECKING

from emojimanager.emoji_manager import EmojiManager

if TYPE_CHECKING:
    from redbot.core.bot import Red


async def setup(bot: "Red"):
    await bot.add_cog(EmojiManager(bot))
