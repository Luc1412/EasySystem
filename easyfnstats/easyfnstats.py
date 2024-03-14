import re
from contextlib import suppress
from typing import TYPE_CHECKING

import aiohttp
import discord
from discord.ext import tasks
from redbot.core import commands, Config, app_commands

if TYPE_CHECKING:
    from redbot.core.bot import Red

INVITE_REGEX = re.compile(r'(?:https?://)?discord(?:app)?\.(?:com/invite|gg)/[a-zA-Z0-9]+/?')


class EasyFnStats(commands.Cog):
    def __init__(self, bot: "Red"):
        self.bot: "Red" = bot
        self.settings = Config.get_conf(self, 32466554543)
        default_guild_settings = {'promo_channel_id': []}
        self.settings.register_guild(**default_guild_settings)

    async def cog_load(self) -> None:
        self._premium_role_loop.start()

    @commands.hybrid_group('easyfnstats')
    async def _easyfnstats(self, ctx: commands.Context) -> None:
        pass

    @_easyfnstats.command(name='promo-channel', description='Sets the promo channel for the server')
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    async def _promo_channel(self, ctx: commands.Context, channel: discord.ForumChannel) -> None:
        await self.settings.guild(ctx.guild).promo_channel_id.set(channel.id)

        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'Successfully set the promo channel to {channel.mention}'
        await ctx.send(embed=embed)

    @commands.Cog.listener('on_thread_create')
    async def _on_promo_create(self, thread: discord.Thread) -> None:
        promo_channel_id = await self.settings.guild(thread.guild).promo_channel_id()
        if not promo_channel_id or thread.parent_id != promo_channel_id:
            return
        # Check for invite link being included
        invite_urls = INVITE_REGEX.findall(thread.starter_message.content)
        if len(invite_urls) != 1:
            await thread.delete()

            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = (
                'Please check our server promo rules again. You are only allowed to post one invite link.'
            )
            with suppress(discord.Forbidden):
                await thread.owner.send(embed=embed)
            return
        try:
            invite = await self.bot.fetch_invite(invite_urls[0])
        except discord.NotFound:
            await thread.delete()

            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'Please check our server promo rules again. The invite link you posted is invalid.'
            with suppress(discord.Forbidden):
                await thread.owner.send(embed=embed)
            return

        # Check if bot is on the guild
        api_keys = await self.bot.get_shared_api_tokens('easyfnstats')
        url = 'https://api.easyfnstats.com/guilds'
        params = {'id': invite.guild.id}
        headers = {'Authorization': api_keys.get('premium_key')}
        async with aiohttp.ClientSession() as session:
            res = await session.get(url, params=params, headers=headers)
            if res.status != 200:
                await thread.delete()

                embed = discord.Embed(colour=discord.Colour.dark_red())
                embed.description = (
                    'Please check our server promo rules again. EasyFortniteStats is not on the server. This is '
                    'required to advertise your server.'
                )
                with suppress(discord.Forbidden):
                    await thread.owner.send(embed=embed)
                return

    @commands.Cog.listener('on_message_edit')
    @tasks.loop(minutes=5)
    async def _premium_role_loop(self):
        api_keys = await self.bot.get_shared_api_tokens('easyfnstats')

        url = 'https://api.easyfnstats.com/premium'
        params = {'type': 'user'}
        headers = {'Authorization': api_keys.get('premium_key')}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as resp:
                data = await resp.json()
        premium_user_ids = [entry['id'] for entry in data]

        guild = self.bot.get_guild(341939185051107330)
        premium_role = guild.get_role(341940409309593606)
        translator_role = guild.get_role(498924054607298560)
        for user_id in premium_user_ids:
            member = guild.get_member(user_id)
            if not member:
                continue
            if premium_role not in member.roles:
                user_data = [e for e in data if e['id'] == user_id][0]
                # If user has translator role and source is grant, do not grant role
                if translator_role in member.roles and user_data['source'] == 'grant':
                    continue
                await member.add_roles(premium_role)

        for member in premium_role.members:
            if member.id not in premium_user_ids:
                await member.remove_roles(premium_role)

    @_premium_role_loop.before_loop
    async def before_premium_role_loop(self) -> None:
        await self.bot.wait_until_red_ready()

    async def cog_unload(self) -> None:
        self._premium_role_loop.cancel()
