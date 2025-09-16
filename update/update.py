from __future__ import annotations

import json
from contextlib import suppress
from typing import TYPE_CHECKING, Any

import discord
from discord import app_commands
from discord.components import _component_factory
from redbot.core import Config, checks, commands

from .types import UpdateGuildSettings
from .views import ConfirmView, ResponseView, UpdateModal

if TYPE_CHECKING:
    from redbot.core.bot import Red


class Update(commands.Cog):
    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.settings: Config = Config.get_conf(self, 200912392)
        default_channel_settings: UpdateGuildSettings = {
            "emoji_id": None,
            "role_id": None,
        }
        self.settings.register_channel(**default_channel_settings)

    @commands.hybrid_command(
        name="update",
        description="Sends a update message to the selected channel with the selected parameters",
    )
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        channel="The channel where the update message should be sent to.",
        mention_type="The type of mention that should be used.",
        payload="The raw payload that should be used for the update message.",
        image="The image that should be used for the update message.",
    )
    @app_commands.rename(mention_type="mention-type")
    @app_commands.choices(
        mention_type=[
            app_commands.Choice(name="None", value=0),
            app_commands.Choice(name="Role", value=1),
            app_commands.Choice(name="Everyone", value=2),
        ]
    )
    async def _update(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        mention_type: app_commands.Choice[int],
        payload: str | None = None,
        image: discord.Attachment | None = None,
    ) -> None:
        assert ctx.guild is not None
        if ctx.interaction is None:
            return

        if (
            mention_type.value == 1
            and not await self.settings.channel(channel).role_id()
        ):
            await ctx.send(
                view=ResponseView(
                    "No mention role setup",
                    "You selected to mention a role but no role is set for the channel.",
                ),
                ephemeral=True,
            )
            return

        if image and image.content_type not in ("image/png", "image/jpeg", "image/gif"):
            await ctx.send(
                view=ResponseView(
                    "Invalid image", "The image must be a PNG, JPEG, or GIF."
                ),
                ephemeral=True,
            )
            return

        image_file = await image.to_file() if image else None

        mention = None
        if mention_type.value == 1:
            role = ctx.guild.get_role(await self.settings.channel(channel).role_id())
            if not role:
                await ctx.send(
                    view=ResponseView(
                        "Invalid mention role",
                        "The mention role set for the channel does not exist.",
                    ),
                    ephemeral=True,
                )
                return
            mention = role.mention
        elif mention_type.value == 2:
            mention = "@everyone"

        if not payload:
            modal = UpdateModal()
            await ctx.interaction.response.send_modal(modal)

            if await modal.wait():
                return

            ctx.interaction = modal.interaction

            view = modal.build_view()
            if image_file:
                view.add_item(
                    discord.ui.MediaGallery(discord.MediaGalleryItem(image_file))
                )
        else:
            view = self.build_view_from_payload(payload)

        if mention:
            view.add_item(discord.ui.TextDisplay(content=f"-# {mention}"))

        confirm_view = ConfirmView(view.children)
        await ctx.send(
            view=confirm_view, allowed_mentions=discord.AllowedMentions.none()
        )

        if await view.wait():
            await ctx.interaction.edit_original_response(
                view=ResponseView(
                    "Update canceled",
                    "The confirmation timed out and the update message was not sent.",
                ),
            )
            return
        ctx.interaction = confirm_view.interaction

        message = await channel.send(
            view=view, allowed_mentions=discord.AllowedMentions.all()
        )
        emoji_id = await self.settings.channel(channel).emoji_id()
        if emoji_id and ctx.bot.get_emoji(emoji_id):
            with suppress(discord.Forbidden):
                await message.add_reaction(ctx.bot.get_emoji(emoji_id))
        if channel.is_news():
            with suppress(discord.Forbidden):
                await message.publish()

        await ctx.interaction.response.edit_message(
            view=ResponseView(
                "Update sent",
                "The update message was successfully sent.",
            ),
        )

    @commands.hybrid_command(name="update-edit", description="Edits a update message.")
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        message="The message that should be edited.",
        image="The image that should be used for the update message.",
        clear_image="Whether the image should be cleared.",
    )
    @app_commands.rename(clear_image="clear-image")
    async def _update_edit(
        self,
        ctx: commands.Context,
        message: discord.Message,
        payload: str | None = None,
        clear_image: bool = False,
        image: discord.Attachment | None = None,
    ) -> None:
        if ctx.interaction is None:
            return
        if not message.components:
            await ctx.send(
                view=ResponseView(
                    "Not an update message",
                    "The provided message is not an update message.",
                ),
                ephemeral=True,
            )
            return

        if image and clear_image:
            await ctx.send(
                view=ResponseView(
                    "Conflicting options",
                    "You can not provide an image and clear the image at the same time.",
                ),
                ephemeral=True,
            )
            return

        if image and image.content_type not in ("image/png", "image/jpeg", "image/gif"):
            await ctx.send(
                view=ResponseView(
                    "Invalid image", "The image must be a PNG, JPEG, or GIF."
                ),
                ephemeral=True,
            )
            return

        image_file = await image.to_file() if image else None

        components = message.components
        if (
            len(components) in (2, 3)
            and isinstance(components[0], discord.TextDisplay)
            and (
                len(components) == 3
                and isinstance(components[1], discord.MediaGalleryComponent)
                and len(components[1].items) == 1
            )
            and isinstance(components[-1], discord.TextDisplay)
        ):
            message_component = components[0]
            title = message_component.content.split("\n")[0].removeprefix("# ").strip()
            text = "\n".join(message_component.content.split("\n")[1:]).strip()
            old_image_file = (
                components[1].items[0].media if len(components) == 3 else None
            )

            modal = UpdateModal(title, text)
            await ctx.interaction.response.send_modal(modal)

            if await modal.wait():
                return

            ctx.interaction = modal.interaction

            view = modal.build_view()
            if image_file:
                view.add_item(
                    discord.ui.MediaGallery(discord.MediaGalleryItem(image_file))
                )
            elif old_image_file and not clear_image:
                image_file = await old_image_file.to_file()
                view.add_item(
                    discord.ui.MediaGallery(discord.MediaGalleryItem(image_file))
                )
        elif payload:
            view = self.build_view_from_payload(payload)
        else:
            await ctx.send(
                view=ResponseView(
                    "Invalid message",
                    "The provided message is not a valid update message and no payload was provided.",
                ),
                ephemeral=True,
            )
            return

        attachments = message.attachments
        if image_file:
            attachments = [image_file]
        elif clear_image:
            attachments = []
        await message.edit(view=view, attachments=attachments)

        await ctx.send(
            view=ResponseView(
                "Update edited",
                "The update message was successfully edited.",
            ),
        )

    @commands.hybrid_group(name="update-settings")
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    async def _update_settings(self, _) -> None:
        """Update configuration options."""
        pass

    @_update_settings.command(
        name="role", description="Set the mention role for a update channel."
    )
    async def _update_settings_role(
        self, ctx: commands.Context, channel: discord.TextChannel, role: discord.Role
    ) -> None:
        await self.settings.channel(channel).role_id.set(role.id)

        await ctx.send(
            view=ResponseView(
                "Mention role set",
                "The mention role for the channel has been successfully set.\n"
                f"> **Channel:** {channel.mention}\n"
                f"> **Role:** {role.mention}",
            ),
        )

    @_update_settings.command(
        name="emoji", description="Set the emoji for a update channel."
    )
    async def _update_settings_emoji(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        emoji: discord.PartialEmoji,
    ) -> None:
        if not emoji.is_custom_emoji():
            await ctx.send(
                view=ResponseView(
                    "Invalid emoji",
                    "The emoji must be a custom emoji.",
                ),
            )
            return
        await self.settings.channel(channel).emoji_id.set(emoji.id)
        await ctx.send(
            view=ResponseView(
                "Emoji set",
                "The emoji has been successfully set.\n"
                f"> **Channel:** {channel.mention}\n"
                f"> **Emoji:** {emoji}",
            ),
        )

    @_update_settings.command(
        name="clear", description="Clears the settings for a update channel."
    )
    async def _update_settings_clear(
        self, ctx: commands.Context, channel: discord.TextChannel
    ) -> None:
        await self.settings.channel(channel).clear()
        await ctx.send(
            view=ResponseView(
                "Settings cleared",
                "The settings for the update channel have been cleared.\n"
                f"> **Channel:** {channel.mention}",
            ),
        )

    @_update_settings.command(
        name="list", description="List all settings for all update channels."
    )
    async def _update_settings_list(self, ctx: commands.Context):
        assert ctx.guild is not None
        view = discord.ui.LayoutView().add_item(
            discord.ui.TextDisplay("# Update Channels")
        )
        for channel_id, data in (await self.settings.all_channels()).items():
            channel = ctx.guild.get_channel(channel_id)
            if not channel:
                continue
            role = ctx.guild.get_role(data["role_id"])
            view.add_item(
                discord.ui.TextDisplay(
                    f"### {channel.mention}\n"
                    f"> **Emoji:** {ctx.bot.get_emoji(data['emoji_id'])}\n"
                    f"> **Role:** {role.mention if role else 'None'}",
                )
            )
            # Only add separator if this is not the last channel in the list
            if channel_id != list((await self.settings.all_channels()).keys())[-1]:
                view.add_item(discord.ui.Separator())
        if len(view.children) == 1:
            view.add_item(
                discord.ui.TextDisplay("There are no update channels set up.")
            )
        await ctx.send(view=view)

    def build_view_from_payload(self, payload: str) -> discord.ui.LayoutView:
        data: dict[Any, Any] = json.loads(payload)

        components = []
        for component_data in data["data"]["components"]:
            if component := _component_factory(component_data):
                components.append(component)

        class ComponentsMessage(discord.Message):
            def __init__(self, components: list[discord.Component]):
                self.components = components

        return discord.ui.LayoutView.from_message(ComponentsMessage(components))
