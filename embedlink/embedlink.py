import difflib
import re
from contextlib import suppress
from datetime import datetime, timezone
from typing import List, Optional

import discord
from redbot.core import Config, app_commands, commands
from redbot.core.bot import Red


class EmbedLink(commands.Cog):
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

    async def _get_by_origin(self, origin: discord.Message | tuple[int, int, int]) -> Optional[dict]:
        if isinstance(origin, discord.Message):
            guild_id, channel_id, message_id = origin.guild.id, origin.channel.id, origin.id
        else:
            guild_id, channel_id, message_id = origin
        linked_messages = await self.settings.guild_from_id(guild_id).linked_messages()
        for linked_message in linked_messages:
            for message in linked_message['origins']:
                if message_id == message['id'] and channel_id == message['channel_id']:
                    return linked_message
        return None

    def build_embed(self, origins: List[discord.Message]) -> discord.Embed:
        data = '\n'.join(m.content for m in origins)

        embed_data = self._parse_data(data)

        embed = discord.Embed()
        if embed_data.get('colour'):
            with suppress(ValueError):
                embed.colour = discord.Colour.from_str(embed_data['colour'])
        if embed_data.get('author.name'):
            embed.set_author(
                name=embed_data['author.name'],
                url=embed_data.get('author.url', None),
                icon_url=embed_data.get('author.icon', None),
            )
        embed.title = embed_data.get('title', None)
        embed.description = embed_data.get('description', '')
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
                try:
                    inline = bool(fields[i].get('inline', True))
                except ValueError:
                    inline = True
                embed.add_field(name=fields[i]['name'], value=fields[i]['value'], inline=inline)

        with suppress(ValueError, TypeError):
            embed.timestamp = datetime.fromtimestamp(int(embed_data.get('timestamp')), timezone.utc)

        return embed

    def _parse_data(self, data: str) -> dict:
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
        if not isinstance(channel, discord.TextChannel) or not payload.guild_id:
            return
        data = await self._get_by_origin((payload.guild_id, payload.channel_id, payload.message_id))
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

        embed = self.build_embed(origins)
        await target_message.edit(content=None, embed=embed)

    @commands.hybrid_group(name='embed-link', description='Manage message links.')
    @commands.mod_or_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    @commands.guild_only()
    async def _embed_link(self, ctx: commands.Context):
        pass

    @_embed_link.command(name='template', description='Shows how to use message links.')
    async def _embed_link_template(self, ctx: commands.Context):
        message = (
            '`#colour#` Embed colour as `#RRGGBB`, `0xRRGGBB` or `rgb(R, G, B)`\n'
            '`#author.name#` Embed author name\n'
            '`#author.url#` Embed author URL (requires `author.name`)\n'
            '`#author.icon#` Embed author icon URL (requires `author.name`)\n'
            '`#title#` Embed title\n'
            '`#description#` Embed description\n'
            '`#thumbnail#` Embed thumbnail URL\n'
            '`#image#` Embed image URL\n'
            '`#footer.text#` Embed footer text\n'
            '`#footer.icon#` Embed footer icon URL (requires `footer.text`)\n'
            '`#field.x.name#` Embed field name. (Replace x with a number between 1 and 25)\n'
            '`#field.x.value#` Embed field 1 value (fields require `field.x.name` and `field.x.value` to be set)\n'
            '`#field.x.inline#` Embed field 1 inline (defaults to `true`)\n'
            '`#timestamp#` Embed timestamp as Unix timestamp'
        )
        await ctx.send(message)

    async def _embed_link_name_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        linked_messages = await self.settings.guild(interaction.guild).linked_messages()
        names = [lm['name'] for lm in linked_messages]
        return [
            app_commands.Choice(name=n, value=n)
            for n in difflib.get_close_matches(current.lower(), names, 25, cutoff=0.0)
        ]

    @_embed_link.command(name='add', description='Adds a message link.')
    @app_commands.describe(
        name='The name of the message link.',
        origin_message='The message to link from.',
        target_message='The message to link to.',
        target_channel='The channel to link to. If provided, a new message will be sent in this channel.',
    )
    @app_commands.rename(
        origin_message='origin-message', target_message='target-message', target_channel='target-channel'
    )
    @app_commands.autocomplete(name=_embed_link_name_autocomplete)
    async def _embed_link_add(
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
        if target_message and target_message.author.id is not ctx.bot.user.id:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The target message has to sent by the bot.'
            return await ctx.send(embed=embed)

        linked_messages = await self.settings.guild(origin_message.guild).linked_messages()
        if not target_message and not target_channel:
            name_match = [i for i in linked_messages if i['name'].lower() == name.lower()]
            if not name_match:
                embed = discord.Embed(colour=discord.Colour.dark_red())
                embed.description = (
                    'If you don\'t provide a target message or channel, '
                    'you have to provide a name to append a new origin message to.'
                )
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

            embed = self.build_embed(origins)
            await target.edit(content=None, embed=embed)

            embed = discord.Embed(colour=discord.Colour.green())
            embed.description = 'Successfully appended new origin message.'
            return await ctx.send(embed=embed)

        if [lm for lm in linked_messages if lm['name'].lower() == name.lower()]:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'A message link with that name already exists.'
            return await ctx.send(embed=embed)

        target_message_data = [
            lm
            for lm in linked_messages
            if target_message
            and lm['target_id'] == target_message.id
            and lm['target_channel_id'] == target_message.channel.id
        ]
        target_message_data = target_message_data[0] if target_message_data else None
        if target_message_data:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The target message is already linked.'
            return await ctx.send(embed=embed)

        embed = self.build_embed([origin_message])
        if target_channel:
            target_message = await target_channel.send(embed=embed)
        else:
            await target_message.edit(content=None, embed=embed)

        linked_messages.append(
            {
                'name': name,
                'origins': [{'channel_id': origin_message.channel.id, 'id': origin_message.id}],
                'target_channel_id': target_message.channel.id,
                'target_id': target_message.id,
            }
        )
        await self.settings.guild(origin_message.guild).linked_messages.set(linked_messages)

        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = 'Successfully linked messages.'
        return await ctx.send(embed=embed)

    @_embed_link.command(name='remove', description='Removes a message link.')
    @app_commands.describe(name='The name of the message link.')
    @app_commands.autocomplete(name=_embed_link_name_autocomplete)
    async def _embed_link_remove(self, ctx: commands.Context, name: str):
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

    @_embed_link.command(name='list', description='Lists all message links.')
    async def _embed_link_list(self, ctx: commands.Context):
        linked_messages = await self.settings.guild(ctx.guild).linked_messages()

        if len(linked_messages) < 1:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'No messages are linked.'
            return await ctx.send(embed=embed)

        await ctx.defer()

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
            embed.description += f'### {linked_message["name"]}\n- **Target:** {target_fmt}\n'

            for i, origin_data in enumerate(linked_message['origins'], 1):
                origin_channel = self.bot.get_channel(origin_data['channel_id'])
                try:
                    origin_message = await origin_channel.fetch_message(origin_data['id'])
                except (discord.NotFound, AttributeError):
                    origin_message = None
                origin_fmt = (
                    f'[Link]({origin_message.jump_url}) ({origin_channel.mention})' if origin_message else 'Not Found'
                )
                embed.description += f'- **Origin {i}:** {origin_fmt}\n'

        await ctx.send(embed=embed)
