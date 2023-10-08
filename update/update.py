from contextlib import suppress
from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands
from redbot.core import Config, checks
from redbot.core.commands import commands, Context

from update.views import UpdateModal, UpdateConfirmView

if TYPE_CHECKING:
    from redbot.core.bot import Red


class Update(commands.Cog):
    def __init__(self, bot: "Red"):
        self.bot: "Red" = bot
        self.settings: Config = Config.get_conf(self, 200912392)
        default_channel_settings = {
            "emoji_id": None,
            "icon_url": None,
            "role_id": None,
        }
        self.settings.register_channel(**default_channel_settings)

    @commands.hybrid_command(
        name='update', description='Sends a update message to the selected channel with the selected parameters'
    )
    @checks.admin_or_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        channel='The channel where the update message should be sent to.',
        mention_type='The type of mention that should be used.',
        image='The image that should be used for the update message.',
    )
    @app_commands.rename(mention_type='mention-type')
    @app_commands.choices(
        mention_type=[
            app_commands.Choice(name='None', value=0),
            app_commands.Choice(name='Role', value=1),
            app_commands.Choice(name='Everyone', value=2),
        ]
    )
    async def _update(
        self,
        ctx: Context,
        channel: discord.TextChannel,
        mention_type: app_commands.Choice[int],
        image: Optional[discord.Attachment] = None,
    ):
        if mention_type.value == 1 and not await self.settings.channel(channel).role_id():
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'You selected to mention a role but no role is set for the channel.'
            return await ctx.send(embed=embed)

        if image and image.content_type not in ('image/png', 'image/jpeg', 'image/gif'):
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The image is not a valid image.'
            return await ctx.send(embed=embed)

        modal = UpdateModal()
        await ctx.interaction.response.send_modal(modal)

        if await modal.wait():
            return

        image_file = await image.to_file() if image else None

        update_embed = discord.Embed()
        update_embed.title = modal.title_input.value
        update_embed.colour = await self.bot.get_embed_colour(ctx)
        update_embed.description = modal.text_input.value
        if image_file:
            update_embed.set_image(url=f'attachment://{image_file.filename}')
        if icon_url := await self.settings.channel(channel).icon_url():
            update_embed.set_thumbnail(url=icon_url)

        mention = None
        if mention_type.value == 1:
            role = ctx.guild.get_role(await self.settings.channel(channel).role_id())
            mention = role.mention
        elif mention_type.value == 2:
            mention = '@everyone'

        view = UpdateConfirmView()
        extra_payload = {'file': image_file} if image_file else {}
        await modal.interaction.response.send_message(
            'Do you want to send the update message?', embed=update_embed, view=view, **extra_payload
        )

        if await view.wait():
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The confirmation timed out and the update message was not sent.'
            return await modal.interaction.edit_original_response(content=None, embed=embed, attachments=[], view=None)

        message = await channel.send(
            content=mention,
            embed=update_embed,
            allowed_mentions=discord.AllowedMentions(everyone=True, roles=True),
            **extra_payload,
        )
        emoji_id = await self.settings.channel(channel).emoji_id()
        if emoji_id and ctx.bot.get_emoji(emoji_id):
            with suppress(discord.Forbidden):
                await message.add_reaction(ctx.bot.get_emoji(emoji_id))
        if channel.is_news():
            with suppress(discord.Forbidden):
                await message.publish()

        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'The update message was successfully sent.'
        await view.interaction.response.edit_message(content=None, embed=embed, attachments=[], view=None)

    @commands.hybrid_command(name='update-edit', description='Edits a update message.')
    @checks.admin_or_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        message='The message that should be edited.',
        image='The image that should be used for the update message.',
        clear_image='Whether the image should be cleared.',
    )
    @app_commands.rename(clear_image='clear-image')
    async def _update_edit(
        self,
        ctx: Context,
        message: discord.Message,
        clear_image: bool = False,
        image: Optional[discord.Attachment] = None,
    ):
        if not len(message.embeds) == 1:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The provided message is not an update message.'
            return await ctx.send(embed=embed)

        if image and clear_image:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'You can not provide an image and clear the image at the same time.'
            return await ctx.send(embed=embed)

        if image and image.content_type not in ['image/png', 'image/jpeg', 'image/gif']:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The image is not a valid image.'
            return await ctx.send(embed=embed)

        update_embed = message.embeds[0]

        modal = UpdateModal(update_embed.title, update_embed.description)
        await ctx.interaction.response.send_modal(modal)

        if await modal.wait():
            return

        image_file = await image.to_file() if image else None

        update_embed.title = modal.title_input.value
        update_embed.description = modal.text_input.value
        update_embed.colour = await self.bot.get_embed_colour(ctx)
        if image_file:
            update_embed.set_image(url=f'attachment://{image_file.filename}')
        if clear_image:
            update_embed.set_image(url=None)
        attachments = message.attachments
        if image_file:
            attachments = [image_file]
        elif clear_image:
            attachments = []
        await message.edit(embed=update_embed, attachments=attachments)

        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'The update message was successfully edited.'
        await modal.interaction.response.send_message(embed=embed)

    @commands.hybrid_group(name='update-settings')
    @checks.admin_or_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    async def _update_settings(self, ctx: Context):
        """Update configuration options."""
        pass

    @_update_settings.command(name='icon', description='Set the icon url for a update channel.')
    @app_commands.describe(channel='The channel for which the icon url should be set', url='The url of the icon')
    async def _update_settings_icon(self, ctx: Context, channel: discord.TextChannel, url: str):
        if not url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The url is not a valid image url.'
            return await ctx.send(embed=embed)
        await self.settings.channel(channel).icon_url.set(url)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = (
            f'The icon url for the channel has been successfully set.\n' f'> **Channel:** {channel.mention}'
        )
        embed.set_thumbnail(url=url)
        return await ctx.send(embed=embed)

    @_update_settings.command(name='role', description='Set the mention role for a update channel.')
    async def _update_settings_role(self, ctx: Context, channel: discord.TextChannel, role: discord.Role):
        await self.settings.channel(channel).role_id.set(role.id)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = (
            f'The mention role for the channel has been successfully set.\n'
            f'> **Channel:** {channel.mention}\n'
            f'> **Role:** {role.mention}'
        )
        return await ctx.send(embed=embed)

    @_update_settings.command(name='emoji', description='Set the emoji for a update channel.')
    async def _update_settings_role(self, ctx: Context, channel: discord.TextChannel, emoji: discord.PartialEmoji):
        if not emoji.is_custom_emoji():
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'The emoji is not a custom emoji.'
            return await ctx.send(embed=embed)
        await self.settings.channel(channel).emoji_id.set(emoji.id)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = (
            f'The emoji for the channel has been successfully set.\n'
            f'> **Channel:** {channel.mention}\n'
            f'> **Emoji:** {emoji}'
        )
        return await ctx.send(embed=embed)

    @_update_settings.command(name='clear', description='Clears the settings for a update channel.')
    async def _update_settings_clear(self, ctx: Context, channel: discord.TextChannel):
        await self.settings.channel(channel).clear()
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'The settings for the update channel have been cleared.'
        return await ctx.send(embed=embed)

    @_update_settings.command(name='list', description='List all settings for all update channels.')
    async def _update_settings_list(self, ctx: Context):
        embed = discord.Embed(color=discord.Colour.dark_magenta())
        embed.title = 'Update Channels'
        for channel_id, data in (await self.settings.all_channels()).items():
            channel = ctx.guild.get_channel(channel_id)
            if not channel:
                continue
            role = ctx.guild.get_role(data['role_id'])
            embed.add_field(
                name=f'**#{channel.name}**',
                value=f'> **Emoji:** {ctx.bot.get_emoji(data["emoji_id"])}\n'
                f'> **Image URL:** {data["icon_url"] or "None"}\n'
                f'> **Role:** {role.mention if role else "None"}',
                inline=False,
            )
        await ctx.send(embed=embed)
