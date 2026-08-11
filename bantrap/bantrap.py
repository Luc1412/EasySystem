from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import TYPE_CHECKING

import discord
from redbot.core import Config, app_commands, commands

from .types import BanTrapGuildSettings
from .views import MessageView

if TYPE_CHECKING:
    from redbot.core.bot import Red

log = logging.getLogger("red.easysystem.bantrap")


class BanTrap(commands.Cog):
    """Soft-ban members who ignore the warning in a designated channel."""

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.settings = Config.get_conf(
            self, identifier=184_927_361, force_registration=True
        )
        defaults: BanTrapGuildSettings = {"channel_id": None, "log_channel_id": None}
        self.settings.register_guild(**defaults)
        self._members_in_progress: set[tuple[int, int]] = set()

    @commands.hybrid_group(  # pyright: ignore[reportArgumentType]
        name="bantrap", description="Manage the ban-trap feature."
    )
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    async def bantrap(self, ctx: commands.Context) -> None:
        """Manage the ban-trap feature."""

    @bantrap.command(  # pyright: ignore[reportArgumentType]
        name="setup",
        description="Create a channel that soft-bans anyone who sends a message in it.",
    )
    @app_commands.describe(name="The name of the warning channel.")
    async def bantrap_setup(
        self, ctx: commands.Context, name: str = "do-not-send-messages"
    ) -> None:
        """Create and configure the ban-trap channel."""
        assert ctx.guild is not None

        existing_id: int | None = await self.settings.guild(ctx.guild).channel_id()
        existing = ctx.guild.get_channel(existing_id) if existing_id else None
        if existing is not None:
            await ctx.send(
                view=MessageView(
                    "Ban-trap already configured",
                    f"The current ban-trap channel is {existing.mention}.",
                    colour=discord.Colour.orange(),
                ),
                ephemeral=True,
            )
            return

        bot_member = ctx.guild.me
        permissions = bot_member.guild_permissions
        missing = [
            label
            for allowed, label in (
                (permissions.manage_channels, "Manage Channels"),
                (permissions.ban_members, "Ban Members"),
                (permissions.moderate_members, "Moderate Members"),
            )
            if not allowed
        ]
        if missing:
            await ctx.send(
                view=MessageView(
                    "Missing permissions",
                    "I need these permissions before setup: " + ", ".join(missing),
                    colour=discord.Colour.red(),
                ),
                ephemeral=True,
            )
            return

        safe_name = name.strip().lower().replace(" ", "-")[:100]
        if not safe_name:
            await ctx.send(
                view=MessageView(
                    "Invalid channel name",
                    "The channel name cannot be empty.",
                    colour=discord.Colour.red(),
                ),
                ephemeral=True,
            )
            return

        reason = f"Ban trap configured by {ctx.author} ({ctx.author.id})"
        try:
            channel = await ctx.guild.create_text_channel(
                safe_name,
                topic="Do not send messages here. Doing so triggers an automatic soft-ban.",
                reason=reason,
            )
            await channel.send(view=self._warning_view())
        except discord.HTTPException:
            log.exception(
                "Could not create the ban-trap channel in guild %s", ctx.guild.id
            )
            await ctx.send(
                view=MessageView(
                    "Setup failed",
                    "I could not create the channel or its warning message. Check my permissions.",
                    colour=discord.Colour.red(),
                ),
                ephemeral=True,
            )
            return

        await self.settings.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(
            view=MessageView(
                "Ban-trap created",
                f"The warning channel is now available at {channel.mention}.",
                colour=discord.Colour.green(),
            ),
            ephemeral=True,
        )

    @bantrap.command(  # pyright: ignore[reportArgumentType]
        name="log-channel",
        description="Set or clear the channel used for ban-trap moderation logs.",
    )
    @app_commands.describe(channel="The log channel. Leave empty to disable logging.")
    async def bantrap_log_channel(
        self, ctx: commands.Context, channel: discord.TextChannel | None = None
    ) -> None:
        """Set the event log channel, or clear it when no channel is supplied."""
        assert ctx.guild is not None
        await self.settings.guild(ctx.guild).log_channel_id.set(
            channel.id if channel is not None else None
        )

        if channel is None:
            text = "Ban-trap event logging has been disabled."
        else:
            text = f"Ban-trap moderation events will be sent to {channel.mention}."
        await ctx.send(
            view=MessageView(
                "Log channel updated", text, colour=discord.Colour.green()
            ),
            ephemeral=True,
        )

    @commands.Cog.listener("on_message")
    async def on_bantrap_message(self, message: discord.Message) -> None:
        guild = message.guild
        if (
            guild is None
            or message.author.bot
            or not isinstance(message.author, discord.Member)
        ):
            return

        channel_id: int | None = await self.settings.guild(guild).channel_id()
        if channel_id is None or message.channel.id != channel_id:
            return

        member = message.author
        key = (guild.id, member.id)
        if key in self._members_in_progress:
            return

        # Never act on the server owner or a member the bot cannot moderate.
        bot_member = guild.me
        if member == guild.owner or member.top_role >= bot_member.top_role:
            log.warning(
                "Could not moderate member %s in ban-trap channel %s due to role hierarchy",
                member.id,
                message.channel.id,
            )
            await self._send_log(
                guild,
                "Moderation skipped",
                f"{member.mention} (`{member.id}`) wrote in <#{message.channel.id}>, "
                "but I cannot moderate them because of the role hierarchy.",
                discord.Colour.orange(),
            )
            return

        self._members_in_progress.add(key)
        try:
            await self._softban(member, message)
        finally:
            self._members_in_progress.discard(key)

    async def _softban(self, member: discord.Member, message: discord.Message) -> None:
        reason = f"Sent a message in ban-trap channel #{message.channel} ({message.channel.id})"

        try:
            await member.timeout(timedelta(days=3), reason=reason)
            await member.ban(delete_message_seconds=604_800, reason=reason)
        except discord.Forbidden:
            log.warning(
                "Missing permission or role hierarchy prevented soft-banning member %s in guild %s",
                member.id,
                member.guild.id,
            )
            await self._send_log(
                member.guild,
                "Soft-ban failed",
                f"I could not soft-ban {member.mention} (`{member.id}`) after they wrote in "
                f"<#{message.channel.id}>. Check my permissions and role position.",
                discord.Colour.red(),
            )
            return
        except discord.HTTPException:
            log.exception(
                "Discord rejected the soft-ban for member %s in guild %s",
                member.id,
                member.guild.id,
            )
            await self._send_log(
                member.guild,
                "Soft-ban failed",
                f"Discord rejected the soft-ban for {member.mention} (`{member.id}`) after "
                f"they wrote in <#{message.channel.id}>.",
                discord.Colour.red(),
            )
            return

        # A small delay avoids Discord occasionally processing the unban before the ban.
        await asyncio.sleep(1)
        try:
            await member.guild.unban(member, reason="Ban-trap soft-ban completed")
        except discord.HTTPException:
            log.exception(
                "Could not unban member %s after ban-trap soft-ban in guild %s",
                member.id,
                member.guild.id,
            )
            await self._send_log(
                member.guild,
                "Unban failed",
                f"{member.mention} (`{member.id}`) was timed out and banned, but I could not "
                "complete the automatic unban. Manual action is required.",
                discord.Colour.red(),
            )
            return

        await self._send_log(
            member.guild,
            "Soft-ban completed",
            f"{member.mention} (`{member.id}`) wrote in <#{message.channel.id}> and received "
            "a 3-day timeout plus a soft-ban with seven days of messages purged.",
            discord.Colour.green(),
        )

    async def _send_log(
        self,
        guild: discord.Guild,
        title: str,
        text: str,
        colour: discord.Colour,
    ) -> None:
        channel_id: int | None = await self.settings.guild(guild).log_channel_id()
        if channel_id is None:
            return

        channel = guild.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        try:
            await channel.send(
                view=MessageView(title, text, colour=colour),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.HTTPException:
            log.exception("Could not send a ban-trap event log in guild %s", guild.id)

    @staticmethod
    def _warning_view() -> MessageView:
        return MessageView(
            ":warning: DON'T SEND MESSAGES HERE :warning:",
            (
                "This channel is a trap for compromised and malicious accounts. "
                "**Sending a message** here will result in an automatic **3-day soft-ban**."
            ),
            colour=discord.Colour.red(),
        )
