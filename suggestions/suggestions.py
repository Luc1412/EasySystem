from contextlib import suppress
from typing import TYPE_CHECKING

import discord
from redbot.core import Config, app_commands, commands

if TYPE_CHECKING:
    from redbot.core.bot import Red


class Suggestions(commands.Cog):
    """This cog to manage suggestions."""

    def __init__(self, bot: "Red"):
        self.bot: "Red" = bot
        self.settings = Config.get_conf(self, 54686776576)
        default_guild_settings = {
            'channel_id': None,
            'upvote_emoji': '✅',
            'downvote_emoji': '❌'
        }
        self.settings.register_guild(**default_guild_settings)

    @commands.hybrid_group(name='suggestions-settings', description='Manage suggestions settings.')
    @commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def _suggest_settings(self, ctx: commands.Context):
        pass

    @_suggest_settings.command(name='channel', description='Set the channel where suggestions should be sent.')
    @app_commands.describe(channel='The channel where suggestions should be sent.')
    async def _suggest_settings_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.settings.guild(ctx.guild).channel_id.set(channel.id)

        embed = discord.Embed(colour=discord.Colour.dark_green())
        embed.description = f'Suggestions will now be sent to {channel.mention}'
        await ctx.send(embed=embed)

    @_suggest_settings.command(name='emojis', description='Set the emojis for upvoting and downvoting.')
    @app_commands.describe(
        upvote_emoji='The emoji to use for upvoting.', downvote_emoji='The emoji to use for downvoting.'
    )
    @app_commands.rename(upvote_emoji='upvote-emoji', downvote_emoji='downvote-emoji')
    async def _suggest_settings_emojis(self, ctx: commands.Context, upvote_emoji: str, downvote_emoji: str):
        await self.settings.guild(ctx.guild).upvote_emoji.set(upvote_emoji)
        await self.settings.guild(ctx.guild).downvote_emoji.set(downvote_emoji)

        embed = discord.Embed(colour=discord.Colour.dark_green())
        embed.description = f'Upvote emoji set to {upvote_emoji} and downvote emoji set to {downvote_emoji}'
        await ctx.send(embed=embed)

    @_suggest_settings.command(name='approve', description='Approve a suggestion.')
    async def _suggest_settings_approve(self, ctx: commands.Context):
        await self.finalize_suggestion(ctx, True)

    @_suggest_settings.command(name='deny', description='Deny a suggestion.')
    async def _suggest_settings_deny(self, ctx: commands.Context):
        await self.finalize_suggestion(ctx, False)

    async def finalize_suggestion(self, ctx: commands.Context, approved: bool):
        # Check if message is in a thread, which channel is the suggestion channel.
        channel_id = await self.settings.guild(ctx.guild).channel_id()
        if not isinstance(ctx.channel, discord.Thread) or ctx.channel.parent.id != channel_id:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'You can only use this command in a suggestion thread.'
            await ctx.send(embed=embed, ephemeral=True)

        thread_name = ctx.channel.name.replace('Pending', 'Approved' if approved else 'Denied')
        await ctx.channel.edit(name=thread_name, locked=True)

        embed = discord.Embed(colour=discord.Colour.green() if approved else discord.Colour.red())
        embed.description = f'This suggestion has been {"approved" if approved else "denied"}.'
        await ctx.send(embed=embed)

    @commands.Cog.listener('on_message')
    async def _on_message(self, message: discord.Message):
        if not message.guild and not message.author.bot:
            return
        channel_id = await self.settings.guild(message.guild).channel_id()
        if not channel_id or message.channel.id != channel_id:
            return
        # Check message to be not spam.
        # Message needs to be at least 25 characters long.
        # Check if message has at least 3 words
        if len(message.content) < 25 or len(message.content.split()) < 3:
            await message.delete()
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.title = 'Your suggestion has been automatically denied'
            embed.description = f'Your suggestion has to be at least 25 characters long and have at least 3 words.'
            with suppress(discord.Forbidden):
                await message.author.send(embed=embed)
            return

        try:
            await message.add_reaction(await self.settings.guild(message.guild).upvote_emoji())
            await message.add_reaction(await self.settings.guild(message.guild).downvote_emoji())
        except discord.Forbidden:
            await message.delete()
            return
        await message.create_thread(name=f'Pending suggestion by {message.author}', auto_archive_duration=10080)



