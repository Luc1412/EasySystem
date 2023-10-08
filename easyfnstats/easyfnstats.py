from typing import TYPE_CHECKING

import aiohttp
from discord.ext import tasks
from redbot.core import commands

if TYPE_CHECKING:
    from redbot.core.bot import Red


class EasyFnStats(commands.Cog):
    def __init__(self, bot: "Red"):
        self.bot: "Red" = bot

    async def cog_load(self) -> None:
        self._premium_role_loop.start()

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

    async def cog_unload(self) -> None:
        self._premium_role_loop.cancel()
