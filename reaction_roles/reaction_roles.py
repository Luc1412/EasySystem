from contextlib import suppress
from typing import Union

import discord
from redbot.core import Config, checks
from redbot.core.commands import commands, Context

BaseCog = getattr(commands, "Cog", object)


class ReactionRoles(BaseCog):
    """

    """

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, 93843927132)
        default_guild_settings = {
            "reaction_roles": {}
        }
        self.settings.register_guild(**default_guild_settings)

    def _get_emoji(self, emoji):
        try:
            emoji = int(emoji)
            emoji = self.bot.get_emoji(emoji)
            return emoji
        except ValueError:
            return emoji

    @commands.group(name='reactionroles')
    @checks.admin_or_permissions(manage_guild=True)
    async def _reaction_roles(self, ctx: Context):
        """"""
        pass

    @_reaction_roles.command(name='add')
    async def _reaction_roles_add(self, ctx: Context, message: discord.Message, emoji: Union[discord.Emoji, str],
                                  role: discord.Role):
        reaction_roles = await self.settings.guild(ctx.guild).reaction_roles()
        message_indicator = f'{message.channel.id}:{message.id}'

        if message_indicator in reaction_roles:
            if emoji in reaction_roles[message_indicator]:
                embed = discord.Embed(colour=discord.Colour.dark_red())
                embed.description = f'There is already a reaction roll registered with this emoji.\n' \
                                    f'> Emoji: {emoji}\n' \
                                    f'> Message: {message.jump_url}'
                return await ctx.send(embed=embed)
        else:
            reaction_roles[message_indicator] = {}

        try:
            await message.add_reaction(emoji)
        except discord.Forbidden:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'I could\'t add a reaction to the message due to missing permissions.\n' \
                                f'> Emoji: {emoji}\n' \
                                f'> Message: {message.jump_url}'
            return await ctx.send(embed=embed)

        reaction_roles[message_indicator][str(emoji)] = role.id
        await self.settings.guild(ctx.guild).reaction_roles.set(reaction_roles)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'The reaction role has been successfully added.\n' \
                            f'> Emoji: {emoji}\n' \
                            f'> Message: {message.jump_url}\n' \
                            f'> Role: {role.mention}'

        return await ctx.send(embed=embed)

    @_reaction_roles.command(name='remove')
    async def _reaction_roles_remove(self, ctx: Context, message: discord.Message, emoji: Union[discord.Emoji, str]):
        reaction_roles = await self.settings.guild(ctx.guild).reaction_roles()
        message_indicator = f'{message.channel.id}:{message.id}'

        if message_indicator not in reaction_roles or emoji not in reaction_roles[message_indicator]:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'There is already a reaction roll registered with this emoji.\n' \
                                f'> Emoji: {emoji}\n' \
                                f'> Message: {message.jump_url}'
            return await ctx.send(embed=embed)

        with suppress(discord.Forbidden):
            await message.remove_reaction(emoji, ctx.guild.me)

        del reaction_roles[message_indicator][str(emoji)]
        if len(reaction_roles[message_indicator]) == 0:
            del reaction_roles[message_indicator]
        await self.settings.guild(ctx.guild).reaction_roles.set(reaction_roles)
        embed = discord.Embed(colour=discord.Colour.dark_blue())
        embed.description = f'The reaction role has been successfully removed.\n' \
                            f'> Emoji: {emoji}\n' \
                            f'> Message: {message.jump_url}'
        return await ctx.send(embed=embed)

    @_reaction_roles.command(name='list')
    async def _reaction_roles_list(self, ctx: Context):
        reaction_roles = await self.settings.guild(ctx.guild).reaction_roles()
        if len(reaction_roles) == 0:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'There is no reaction role setup up for this server.'
            return await ctx.send(embed=embed)

        embed = discord.Embed(colour=discord.Colour.dark_magenta())
        for message_indicator, message_data in reaction_roles.items():
            split = message_indicator.split(':')
            channel = self.bot.get_channel(int(split[0]))
            try:
                message = await channel.fetch_message(int(split[1]))
            except discord.NotFound:
                continue
            reactions = []
            for raw_emoji, role_id in message_data.items():
                emoji = self._get_emoji(raw_emoji)
                role = ctx.guild.get_role(role_id)
                reactions.append(f'{emoji} **-** {role.mention}')
            embed.add_field(name=message.jump_url, value='\n'.join(reactions), inline=False)
        return await ctx.send(embed=embed)

    async def get_role(self, payload: discord.RawReactionActionEvent):
        message_indicator = f'{payload.channel_id}:{payload.message_id}'
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return None
        reaction_roles = await self.settings.guild(guild).reaction_roles()
        if message_indicator not in reaction_roles:
            return None
        emoji: discord.PartialEmoji = payload.emoji
        emoji = payload.emoji.id if emoji.is_custom_emoji() else payload.emoji
        print('emoji', emoji)
        print('data', reaction_roles[message_indicator])
        if emoji not in reaction_roles[message_indicator]:
            print(5)
            return None
        print(6)
        role = guild.get_role(reaction_roles[message_indicator][emoji])
        if not role:
            print(7)
            return None
        print(8)
        return role

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if not member:
            return
        print(15)
        role = await self.get_role(payload)
        if not role:
            print(16)
            return
        print(17)
        with suppress(discord.Forbidden):
            await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if not member:
            return
        role = await self.get_role(payload)
        if not role:
            return
        with suppress(discord.Forbidden):
            await member.remove_roles(role)
