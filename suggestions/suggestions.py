from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

import discord
from redbot.core import Config, app_commands, commands

from .types import SuggestionsGuildSettings
from .views import ResponseView

if TYPE_CHECKING:
    from redbot.core.bot import Red


class Suggestions(commands.Cog):
    """This cog to manage suggestions."""

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.settings: Config = Config.get_conf(self, 54686776576)
        default_guild_settings: SuggestionsGuildSettings = {
            "channel_id": None,
            "upvote_emoji": "✅",
            "downvote_emoji": "❌",
        }
        self.settings.register_guild(**default_guild_settings)

    @commands.hybrid_group(
        name="suggestions-settings", description="Manage suggestions settings."
    )
    @commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def _suggest_settings(self, _) -> None:
        pass

    @_suggest_settings.command(
        name="channel", description="Set the channel where suggestions should be sent."
    )
    @app_commands.describe(channel="The channel where suggestions should be sent.")
    async def _suggest_settings_channel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ) -> None:
        assert ctx.guild is not None
        await self.settings.guild(ctx.guild).channel_id.set(channel.id)

        await ctx.send(
            view=ResponseView(
                "Suggestions channel set",
                "Suggestions will now be sent to the specified channel.\n"
                f"> **Channel:** {channel.mention}",
            )
        )

    @_suggest_settings.command(
        name="emojis", description="Set the emojis for upvoting and downvoting."
    )
    @app_commands.describe(
        upvote_emoji="The emoji to use for upvoting.",
        downvote_emoji="The emoji to use for downvoting.",
    )
    @app_commands.rename(upvote_emoji="upvote-emoji", downvote_emoji="downvote-emoji")
    async def _suggest_settings_emojis(
        self, ctx: commands.Context, upvote_emoji: str, downvote_emoji: str
    ):
        assert ctx.guild is not None
        await self.settings.guild(ctx.guild).upvote_emoji.set(upvote_emoji)
        await self.settings.guild(ctx.guild).downvote_emoji.set(downvote_emoji)

        await ctx.send(
            view=ResponseView(
                "Suggestion emoji set",
                "Suggestion emojis have been set successfully.\n"
                f"> **Upvote emoji:** {upvote_emoji}\n"
                f"> **Downvote emoji:** {downvote_emoji}",
            )
        )

    @_suggest_settings.command(name="approve", description="Approve a suggestion.")
    async def _suggest_settings_approve(self, ctx: commands.Context):
        await self.finalize_suggestion(ctx, True)

    @_suggest_settings.command(name="deny", description="Deny a suggestion.")
    async def _suggest_settings_deny(self, ctx: commands.Context):
        await self.finalize_suggestion(ctx, False)

    async def finalize_suggestion(self, ctx: commands.Context, approved: bool) -> None:
        assert ctx.guild is not None
        # Check if message is in a thread, which channel is the suggestion channel.
        channel_id = await self.settings.guild(ctx.guild).channel_id()
        if (
            not isinstance(ctx.channel, discord.Thread)
            or not ctx.channel.parent
            or ctx.channel.parent.id != channel_id
        ):
            await ctx.send(
                view=ResponseView(
                    "Not in suggestion thread",
                    "You can only use this command in a suggestion thread.",
                )
            )
            return

        await ctx.send(
            view=discord.ui.LayoutView().add_item(
                discord.ui.Container(
                    discord.ui.TextDisplay(content="# Suggestion finalized"),
                    accent_colour=discord.Colour.green(),
                )
            )
        )

        assert isinstance(ctx.channel, discord.Thread)
        await ctx.channel.edit(
            name=ctx.channel.name.replace(
                "Pending", "Approved" if approved else "Denied"
            ),
            archived=True,
            locked=True,
        )

    @commands.Cog.listener("on_message")
    async def _on_message(self, message: discord.Message) -> None:
        if not message.guild or message.author.bot:
            return
        channel_id = await self.settings.guild(message.guild).channel_id()
        if not channel_id or message.channel.id != channel_id:
            return
        # Check message to be not spam.
        # Message needs to be at least 25 characters long.
        # Check if message has at least 3 words
        if len(message.content) < 25 or len(message.content.split()) < 3:
            await message.delete()

            with suppress(discord.Forbidden):
                await message.author.send(
                    view=ResponseView(
                        "Suggestion auto-denied",
                        "Your suggestion was automatically denied because it did not meet the minimum requirements:\n"
                        "- At least 25 characters long\n"
                        "- At least 3 words",
                    )
                )
            return

        try:
            await message.add_reaction(
                await self.settings.guild(message.guild).upvote_emoji()
            )
            await message.add_reaction(
                await self.settings.guild(message.guild).downvote_emoji()
            )
        except discord.Forbidden:
            await message.delete()
            return
        await message.create_thread(
            name=f"Pending suggestion by {message.author}", auto_archive_duration=10080
        )
