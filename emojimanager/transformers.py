from typing import Optional, List, TYPE_CHECKING

import discord
from discord import app_commands


if TYPE_CHECKING:
    from emojimanager import EmojiManager


class EmojiTransformer(app_commands.Transformer):

    async def autocomplete(self, interaction: discord.Interaction, current: str, /) -> List[app_commands.Choice[str]]:
        cog: "EmojiManager" = interaction.client.get_cog("EmojiManager")  # type: ignore
        guild_ids = cog.settings.emoji_server_ids()
        return [
            app_commands.Choice(name=e.name, value=str(e.id))
            for e in interaction.client.emojis
            if str(e.id) == current or e.name.startswith(current) and e.guild.id in guild_ids
        ]

    async def transform(self, interaction: discord.Interaction, value: str, /) -> Optional[discord.Emoji]:
        try:
            emoji_id = int(value)
            return interaction.client.get_emoji(emoji_id)
        except ValueError:
            return None


class GuildTransformer(app_commands.Transformer):

    async def autocomplete(self, interaction: discord.Interaction, current: str, /) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=g.name, value=g.id)
            for g in interaction.client.guilds
            if str(g.id) == current or g.name.startswith(current)
        ]

    async def transform(self, interaction: discord.Interaction, value: str, /) -> Optional[discord.Guild]:
        try:
            guild_id = int(value)
            return interaction.client.get_guild(guild_id)
        except ValueError:
            return None
