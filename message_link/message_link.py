import difflib
import re
from contextlib import suppress
from datetime import datetime, timezone
from typing import List, Optional

import discord
from redbot.core import Config, app_commands, commands
from redbot.core.bot import Red


class MessageLink(commands.Cog):
    def __init__(self, bot: "Red"):
        self.bot: "Red" = bot

        self.settings = Config.get_conf(self, 2187637202)
        default_guild_settings = {'linked_messages': []}
        # {
        #     'name': '',
        #     'origins': [
        #         'channel_id': 08324,
        #         'id': 903429,
        #     ],
        #     'target_channel_id': 62739183,
        #     'target_id': 213213189
        # }
        self.settings.register_guild(**default_guild_settings)

    async def _get_by_origin(self, origin: discord.Message) -> Optional[dict]:
        linked_messages = await self.settings.guild(origin.guild).linked_messages()
        for linked_message in linked_messages:
            for message in linked_message['origins']:
                if origin.id == message['id'] and origin.channel.id == message['channel_id']:
                    return linked_message
        return None

    async def _get_by_target(self, target: discord.Message) -> Optional[dict]:
        linked_messages = await self.settings.guild(target.guild).linked_messages()
        for linked_message in linked_messages:
            if target.id == linked_message['target_id'] and target.channel.id == linked_message['target_channel_id']:
                return linked_message
        return None

    async def _execute_edit(self, target: discord.Message, origins: List[discord.Message]) -> None:
        data = '\n'.join(m.content for m in origins)

        embed_data = self._parse_data(data)
        if not embed_data:
            return

        embed = discord.Embed()
        with suppress(ValueError):
            embed.colour = discord.Colour.from_str(embed_data.get('colour', ''))
        if embed_data.get('author.text'):
            embed.set_author(
                name=embed_data['author.name'],
                url=embed_data.get('author.name', None),
                icon_url=embed_data.get('author.icon', None),
            )
        embed.title = embed_data.get('title', None)
        embed.description = embed_data.get('description', None)
        if embed_data.get('thumbnail'):
            embed.set_thumbnail(url=embed_data['thumbnail'])
        if embed_data.get('image'):
            embed.set_image(url=embed_data['image'])
        if embed_data.get('footer.text'):
            embed.set_footer(
                text=embed_data['footer.text'],
                icon_url=embed_data.get('footer.icon', None),
            )
        if embed_data.get('fields'):
            fields = embed_data['fields']
            for i in range(1, 25):
                if not fields.get(i):
                    continue
                if not fields[i].get('name') or not fields[i].get('value'):
                    continue
                embed.add_field(
                    name=fields[i]['name'],
                    value=fields[i]['value'],
                    inline=fields[i].get('inline', True),
                )

        with suppress(TypeError):
            embed.timestamp = datetime.fromtimestamp(int(embed_data.get('timestamp')), timezone.utc)

        await target.edit(content=None, embed=embed)

    def _parse_data(self, data: str) -> Optional[dict]:
        embed_data = {}
        regex = re.compile(
            r'#(colour|'
            r'author\.name|'
            r'author\.url|'
            r'author\.icon|'
            r'title|'
            r'thumbnail|'
            r'description|'
            r'field\.(?:[1-9]|1[0-9]|2[0-5])\.name|'
            r'field\.(?:[1-9]|1[0-9]|2[0-5])\.value|'
            r'field\.(?:[1-9]|1[0-9]|2[0-5])\.inline|'
            r'image|'
            r'footer\.text|'
            r'footer\.icon|'
            r'timestamp'
            r')#(?: |)(.*)',
            re.IGNORECASE | re.MULTILINE,
        )

        current = None
        for line in data.split('\n'):
            results = regex.findall(line)
            if len(results) == 0:
                if not current:
                    continue
                if current.lower().startswith('field'):  # TODO: IMprove
                    parts = current.lower().split('.')
                    if 'fields' not in embed_data:
                        embed_data['fields'] = {}
                    if int(parts[1]) not in embed_data['fields']:
                        embed_data['fields'][int(parts[1])] = {}
                    embed_data['fields'][int(parts[1])][parts[2]] += f'\n{line}'
                    continue
                embed_data[current] += f'\n{line}'
            for result in results:
                current = result[0]
                if result[0].lower().startswith('field'):
                    parts = result[0].lower().split('.')
                    if 'fields' not in embed_data:
                        embed_data['fields'] = {}
                    if int(parts[1]) not in embed_data['fields']:
                        embed_data['fields'][int(parts[1])] = {}
                    embed_data['fields'][int(parts[1])][parts[2]] = result[1]
                    continue
                embed_data[result[0]] = result[1]

        return embed_data

    @commands.Cog.listener(name='on_raw_message_edit')
    async def on_message_update(self, payload: discord.RawMessageUpdateEvent):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if not isinstance(channel, discord.TextChannel):
            return
        data = await self._get_by_origin(message)
        if not data:
            return

        origins = []
        for origin in data['origins']:
            origin_channel = self.bot.get_channel(origin['channel_id'])
            if not origin_channel:
                continue
            with suppress(discord.NotFound):
                origins.append(await origin_channel.fetch_message(origin['id']))

        target_channel = self.bot.get_channel(data['target_channel_id'])
        if not target_channel:
            return
        try:
            target_message = await target_channel.fetch_message(data['target_id'])
        except discord.NotFound:
            return

        await self._execute_edit(target_message, origins)

    @commands.hybrid_group(name='message-link', description='Manage message links.')
    async def _message_link(self, ctx: commands.Context):
        pass

    async def _message_link_name_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        linked_messages = await self.settings.guild(interaction.guild).linked_messages()
        names = [lm['name'] for lm in linked_messages]
        return [app_commands.Choice(name=n, value=n) for n in difflib.get_close_matches(current.lower(), names, 25)]

    @_message_link.command(name='add', description='Adds a message link.')
    @app_commands.describe(
        name='The name of the message link.',
        origin_message='The message to link from.',
        target_message='The message to link to.',
        target_channel='The channel to link to. If provided, a new message will be sent in this channel.',
    )
    @app_commands.rename(
        origin_message='origin-message', target_message='target-message', target_channel='target-channel'
    )
    @app_commands.autocomplete(name=_message_link_name_autocomplete)
    async def _message_link_add(
        self,
        ctx: commands.Context,
        name: str,
        origin_message: str,
        target_message: Optional[str] = None,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        try:
            origin_message = await commands.MessageConverter().convert(ctx, origin_message)
        except commands.BadArgument:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = (
                'The origin message could not be found. Enter a message link, or message ID (in the same channel).'
            )
            return await ctx.send(embed=embed)

        if target_message:
            try:
                target_message = await commands.MessageConverter().convert(ctx, target_message)
            except commands.BadArgument:
                embed = discord.Embed(colour=discord.Colour.dark_red())
                embed.description = (
                    'The target message could not be found. Enter a message link, or message ID (in the same channel).'
                )
                return await ctx.send(embed=embed)

        if await self._get_by_origin(origin_message):
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The origin message is already linked.'
            return await ctx.send(embed=embed)
        if target_message and target_channel:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'You can\'t provide both a target message and a target channel.'
            return await ctx.send(embed=embed)
        if target_message and target_message.author is not ctx.bot.user:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The target message has to sent by the bot.'
            return await ctx.send(embed=embed)

        linked_messages = await self.settings.guild(origin_message.guild).linked_messages()
        if not target_message and not target_channel:
            name_match = [i for i in linked_messages if i['name'].lower() == name.lower()]
            if not name_match:
                embed = discord.Embed(colour=discord.Colour.dark_red())
                embed.description = 'If you don\'t provide a target message or channel, you have to provide a name to append a new origin message to.'
                return await ctx.send(embed=embed)
            index = linked_messages.index(name_match[0])
            linked_messages[index]['origins'].append({'channel_id': origin_message.channel.id, 'id': origin_message.id})

            target_channel = self.bot.get_channel(linked_messages[index]['target_channel_id'])
            if not target_channel:
                linked_messages.pop(index)
                await self.settings.guild(origin_message.guild).linked_messages.set(linked_messages)
                embed = discord.Embed(colour=discord.Colour.dark_red())
                embed.description = 'The target channel is no longer available. Removing the message link.'
                return await ctx.send(embed=embed)

            try:
                target = await target_channel.fetch_message(linked_messages[index]['target_id'])
            except discord.NotFound:
                linked_messages.pop(index)
                await self.settings.guild(origin_message.guild).linked_messages.set(linked_messages)
                embed = discord.Embed(colour=discord.Colour.dark_red())
                embed.description = 'The target message is no longer available. Removing the message link.'
                return await ctx.send(embed=embed)

            origins = []
            for origin in linked_messages[index]['origins']:
                origin_channel = self.bot.get_channel(origin['channel_id'])
                if not origin_channel:
                    linked_messages.pop(index)
                    await self.settings.guild(origin_message.guild).linked_messages.set(linked_messages)
                    embed = discord.Embed(colour=discord.Colour.dark_red())
                    embed.description = 'One of the origin channels is no longer available. Removing the message link.'
                    return await ctx.send(embed=embed)

                try:
                    origins.append(await origin_channel.fetch_message(origin['id']))
                except discord.NotFound:
                    linked_messages.pop(index)
                    await self.settings.guild(origin_message.guild).linked_messages.set(linked_messages)
                    embed = discord.Embed(colour=discord.Colour.dark_red())
                    embed.description = 'One of the origin messages is no longer available. Removing the message link.'
                    return await ctx.send(embed=embed)

            await self._execute_edit(target, origins)

            embed = discord.Embed(colour=discord.Colour.green())
            embed.description = 'Successfully appended new origin message.'
            return await ctx.send(embed=embed)

        if [lm for lm in linked_messages if lm['name'].lower() == name.lower()]:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'A message link with that name already exists.'
            return await ctx.send(embed=embed)

        if self._get_by_target(target_message):
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The target message is already linked.'
            return await ctx.send(embed=embed)

        linked_messages.append(
            {
                'name': name,
                'origins': [{'channel_id': origin_message.channel.id, 'id': origin_message.id}],
                'target_channel_id': target_message.channel.id,
                'target_id': target_message.id,
            }
        )
        await self.settings.guild(origin_message.guild).linked_messages.set(linked_messages)

        await self._execute_edit(target_message, [origin_message])

        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = 'Successfully linked messages.'
        return await ctx.send(embed=embed)

    @_message_link.command(name='remove', description='Removes a message link.')
    @app_commands.describe(name='The name of the message link.')
    @app_commands.autocomplete(name=_message_link_name_autocomplete)
    async def _message_link_remove(self, ctx: commands.Context, name: str):
        linked_messages = await self.settings.guild(ctx.guild).linked_messages()
        linked_message = [lm for lm in linked_messages if lm['name'].lower() == name.lower()]
        if not linked_message:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'No message link with that name exists.'
            return await ctx.send(embed=embed)

        linked_messages.remove(linked_message[0])
        await self.settings.guild(ctx.guild).linked_messages.set(linked_messages)

        embed = discord.Embed(colour=discord.Colour.dark_blue())
        embed.description = 'Successfully unlinked message.'
        return await ctx.send(embed=embed)

    @_message_link.command(name='list', description='Lists all message links.')
    async def _message_link_list(self, ctx: commands.Context):
        linked_messages = await self.settings.guild(ctx.guild).linked_messages()

        if len(linked_messages) < 1:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'No messages are linked.'
            return await ctx.send(embed=embed)

        embed = discord.Embed(colour=discord.Color.dark_magenta())
        embed.title = 'Linked Messages'
        embed.description = ''

        for linked_message in linked_messages:
            target_channel = self.bot.get_channel(linked_message['target_channel_id'])
            try:
                target_message = await target_channel.fetch_message(linked_message['target_id'])
            except (discord.NotFound, AttributeError):
                target_message = None

            target_fmt = (
                f'[Link]({target_message.jump_url}) ({target_channel.mention})' if target_message else 'Not Found'
            )
            embed.description = f'### {linked_message["name"]}\n' f'- **Target:** {target_fmt}\n'

            for i, origin_data in enumerate(linked_message['origins'], 1):
                origin_channel = self.bot.get_channel(origin_data['channel_id'])
                try:
                    origin_message = await origin_channel.fetch_message(origin_data['id'])
                except (discord.NotFound, AttributeError):
                    origin_message = None
                origin_fmt = (
                    f'[Link]({origin_message.jump_url}) ({origin_channel.mention})' if origin_message else 'Not Found'
                )
                embed.description += f'**Origin {i}:** {origin_fmt}\n'

        await ctx.send(embed=embed)
