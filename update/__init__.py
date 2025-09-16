from __future__ import annotations

from typing import TYPE_CHECKING

from .update import Update

if TYPE_CHECKING:
    from redbot.core.bot import Red


async def setup(bot: Red) -> None:
    await bot.add_cog(Update(bot))
