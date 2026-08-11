from __future__ import annotations

from typing import TYPE_CHECKING, cast

import aiohttp
from discord.ext import tasks
from redbot.core import commands

from .types import PremiumUser

if TYPE_CHECKING:
    from redbot.core.bot import Red


def parse_premium_users(value: object) -> list[PremiumUser]:
    if not isinstance(value, list):
        raise ValueError("Premium API response must be a list")

    users: list[PremiumUser] = []
    for entry in value:
        if not isinstance(entry, dict):
            raise ValueError("Each premium user must be an object")
        user_id = entry.get("id")
        source = entry.get("source")
        if not isinstance(user_id, int) or isinstance(user_id, bool):
            raise ValueError("Premium user id must be an integer")
        if not isinstance(source, str):
            raise ValueError("Premium user source must be a string")
        users.append({"id": user_id, "source": source})
    return users


class EasyFnStats(commands.Cog):
    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot

    async def cog_load(self) -> None:
        self._premium_role_loop.start()

    @tasks.loop(minutes=5)
    async def _premium_role_loop(self) -> None:
        api_keys = await self.bot.get_shared_api_tokens("easyfnstats")

        url = "https://api.easyfnstats.com/premium"
        params = {"type": "user"}
        headers = {"Authorization": api_keys.get("premium_key")}
        async with (
            aiohttp.ClientSession() as session,
            session.get(url, params=params, headers=headers) as resp,
        ):
            data = parse_premium_users(cast(object, await resp.json()))
        premium_user_ids = [entry["id"] for entry in data]

        guild = self.bot.get_guild(341939185051107330)
        if not guild:
            return
        premium_role = guild.get_role(341940409309593606)
        translator_role = guild.get_role(498924054607298560)
        if not premium_role or not translator_role:
            return
        for user_id in premium_user_ids:
            member = guild.get_member(user_id)
            if not member:
                continue
            if premium_role not in member.roles:
                user_data = [e for e in data if e["id"] == user_id][0]
                # If user has translator role and source is grant, do not grant role
                if translator_role in member.roles and user_data["source"] == "grant":
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
