import re
from contextlib import suppress
from datetime import datetime

import discord
from discord.ext.commands import ColourConverter
from redbot.core import Config
from redbot.core.commands import commands, Context

from update.update import BaseCog


class MessageLink(BaseCog):
    """"""

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, 2187637202)
        default_guild_settings = {
            "linked_messages": []
        }
        # {
        #     "origin_message_channel_id": 71298321,
        #     "origin_message_id": 9723713,
        #     "target_message_channel_id": 62739183,
        #     "target_message_id": 213213189
        # }
        self.settings.register_guild(**default_guild_settings)

    async def _get_by_origin(self, origin: discord.Message):
        linked_messages = await self.settings.guild(origin.guild).linked_messages()
        for linked_message in linked_messages:
            if origin.id == linked_message['origin_message_id'] \
                    and origin.channel.id == linked_message['origin_message_channel_id']:
                return linked_message
        return None

    async def _get_by_target(self, target: discord.Message):
        linked_messages = await self.settings.guild(target.guild).linked_messages()
        for linked_message in linked_messages:
            if target.id == linked_message['target_message_id'] \
                    and target.channel.id == linked_message['target_message_channel_id']:
                return linked_message
        return None

    async def _execute_edit(self, target: discord.Message, origin: discord.Message):
        data = origin.content

        embed_data = self._parse_data(data)
        if not embed_data:
            return

        embed = discord.Embed()
        with suppress(commands.BadArgument, IndexError):
            formatted_colour = await ColourConverter().convert(None, embed_data.get('colour', ''))
            embed.colour = formatted_colour
        if embed_data.get('author.text'):
            embed.set_author(name=embed_data['author.name'],
                             url=embed_data.get('author.name', discord.embeds.EmptyEmbed),
                             icon_url=embed_data.get('author.icon', discord.embeds.EmptyEmbed))
        embed.title = embed_data.get('title', discord.embeds.EmptyEmbed)
        embed.description = embed_data.get('description', discord.embeds.EmptyEmbed)
        if embed_data.get('thumbnail'):
            embed.set_thumbnail(url=embed_data['thumbnail'])
        if embed_data.get('image'):
            embed.set_image(url=embed_data['image'])
        if embed_data.get('footer.text'):
            embed.set_footer(text=embed_data['footer.text'],
                             icon_url=embed_data.get('footer.icon', discord.embeds.EmptyEmbed))
        if embed_data.get('fields'):
            fields = embed_data['fields']
            for i in range(1, 25):
                if not fields.get(i):
                    continue
                if not fields[i].get('name') or not fields[i].get('value'):
                    continue
                embed.add_field(name=fields[i]['name'], value=fields[i]['name'], inline=fields[i].get('inline', True))

        with suppress(TypeError):
            embed.timestamp = datetime.utcfromtimestamp(int(embed_data.get('timestamp')))

        await target.edit(content=None, embed=embed)

    def _parse_data(self, data: str):
        embed_data = {}
        regex = r'#(colour|' \
                r'author\.name|author\.url|author\.icon|' \
                r'title|' \
                r'thumbnail|' \
                r'description|' \
                r'field\.(?:[1-9]|1[0-9]|2[0-5])\.name|field\.(?:[1-9]|1[0-9]|2[0-5])\.value|field\.(?:[1-9]|1[0-9]|2[0-5])\.inline|' \
                r'image|' \
                r'footer\.text|footer\.icon|' \
                r'timestamp)#' \
                r'(?: |)(.*)'
        results = re.findall(regex, data, re.IGNORECASE | re.MULTILINE)
        if len(results) == 0:
            return None
        for result in results:
            if result.lower().starts_with('field'):
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
        target_channel = self.bot.get_channel(data['target_message_channel_id'])
        target_message = await target_channel.fetch_message(data['target_message_id'])
        await self._execute_edit(target_message, message)

    @commands.group(name='mlink')
    async def _mlink(self, ctx: Context):
        """"""
        pass

    @_mlink.command(name='add')
    async def mlink_add(self, ctx: Context, target: discord.Message, origin: discord.Message):
        """"""
        if await self._get_by_origin(origin):
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The origin message is already linked.'
            return await ctx.send(embed=embed)
        if target.author.id != ctx.bot.user.id:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The target message has to sent by the bot.'
            return await ctx.send(embed=embed)
        if not origin.content:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The origin message can\'t be empty.'
            return await ctx.send(embed=embed)

        linked_messages = await self.settings.guild(origin.guild).linked_messages()
        linked_messages.append({
            'origin_message_channel_id': origin.channel.id,
            'origin_message_id': origin.id,
            'target_message_channel_id': target.channel.id,
            'target_message_id': target.id
        })
        await self.settings.guild(origin.guild).linked_messages.set(linked_messages)

        await self._execute_edit(target, origin)

        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = 'Successfully linked messages.'
        return await ctx.send(embed=embed)

    @_mlink.command(name='remove')
    async def mlink_remove(self, ctx: Context, target: discord.Message):
        """"""
        data = await self._get_by_target(target)
        if not data:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = 'The target message isn\'t linked.'
            return await ctx.send(embed=embed)
        print(data)
        linked_messages = await self.settings.guild(ctx.guild).linked_messages()
        linked_messages.remove(data)
        await self.settings.guild(ctx.guild).linked_messages.set(linked_messages)

        embed = discord.Embed(colour=discord.Colour.dark_blue())
        embed.description = 'Successfully unlinked message.'
        return await ctx.send(embed=embed)

    @_mlink.command(name='list')
    async def mlink_list(self, ctx: Context):
        """"""
        embed = discord.Embed(colour=discord.Color.dark_magenta())
        embed.title = 'Linked Messages'
        linked_messages = await self.settings.guild(ctx.guild).linked_messages()
        if len(linked_messages) < 1:
            embed.description = 'No messages are linked.'
            return await ctx.send(embed=embed)
        for entry in linked_messages:
            target_channel = self.bot.get_channel(entry['target_message_channel_id'])
            try:
                target_message = await target_channel.fetch_message(entry['target_message_id'])
            except (discord.NotFound, AttributeError):
                target_message = None

            origin_channel = self.bot.get_channel(entry['origin_message_channel_id'])
            try:
                origin_message = await target_channel.fetch_message(entry['origin_message_id'])
            except (discord.NotFound, AttributeError):
                origin_message = None

            embed.add_field(
                name=f'Linked to #{target_channel if target_channel else "Not Found"}',
                value=f'**Target Channel:** {target_channel.mention if target_channel else "Not Found"}\n'
                      f'**Target Message:** {f"[Link]({target_message.jump_url})" if target_message else "Not Found"}\n'
                      f'**Target Channel:** {origin_channel.mention if origin_channel else "Not Found"}\n'
                      f'**Origin Message:** {f"[Link]({origin_message.jump_url})" if origin_message else "Not Found"}\n',
                inline=False
            )

        await ctx.send(embed=embed)
