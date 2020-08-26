import asyncio
import re
from enum import Enum

import discord


class SelectionBuildException(Exception):
    pass


class SelectionBase:

    def __init__(self, interface, title, text, **kwargs):
        self.interface = interface
        self.title = title
        self.text = text

        self.interface_reactions = [self.interface.fail_emoji] if kwargs.get('first', False) else \
            [self.interface.back_emoji, self.interface.fail_emoji]

        self.footer = kwargs.get('footer_text', discord.embeds.EmptyEmbed)
        self.header_url = kwargs.get('header_url', discord.embeds.EmptyEmbed)
        self.header_icon = kwargs.get('header_icon', self.interface.header_icon)
        self.footer_icon = kwargs.get('footer_icon', self.interface.footer_icon)
        self.color = kwargs.get('color', self.interface.selection_color)
        self.fields = kwargs.get('fields', [])
        self.thumbnail = kwargs.get('thumbnail', '')
        self.image = kwargs.get('image', '')

        self.next = None
        self.prev = None

        self.result_events = {}
        self.action = None
        self.load_action = False

    def add_result(self, result: str, selection_or_result, header: str, desc: str, **kwargs):
        selection = selection_or_result.value(self.interface, header, desc, **kwargs)
        self.result_events[result] = selection
        return selection

    def set_action(self, function, loading=False):
        self.action = function
        self.load_action = loading

    def build_message(self):
        msg = discord.Embed()
        msg.colour = self.color

        msg.set_author(
            name=self.title.get(self.interface.result()) if type(self.title) is ReplacedText else self.title,
            url=self.header_url,
            icon_url=self.header_icon
        )

        msg.description = self.text.get(self.interface.result()) if type(self.text) is ReplacedText else self.text
        for field in self.fields:
            field_name = field.get('name', 'None')
            field_value = field.get('value', 'None')
            msg.add_field(name=field_name.get(self.interface.result()) if type(field_name) is ReplacedText else field_name,
                          value=field_value.get(self.interface.result()) if type(field_value) is ReplacedText else field_value,
                          inline=field.get('inline', True))
        msg.set_footer(
            text=self.footer.get(self.interface.result()) if type(self.footer) is ReplacedText else self.footer,
            icon_url=self.footer_icon
        )

        thumbnail_url = self.thumbnail.get(self.interface.result()) if type(self.thumbnail) is ReplacedText \
            else self.thumbnail
        if self.interface.check_url(thumbnail_url):
            msg.set_thumbnail(url=thumbnail_url)

        image_url = self.image.get(self.interface.result()) if type(self.image) is ReplacedText else self.image
        if self.interface.check_url(image_url):
            msg.set_image(url=image_url)

        return msg

    async def run_action(self):
        if not self.action:
            return
        if self.load_action:
            load_embed = discord.Embed()
            load_embed.colour = self.interface.load_color
            load_embed.description = self.interface.load_text
            await self.interface.message.edit(embed=load_embed)
        await self.action(self.interface.ctx, self.interface.result())


class ReactionSelection(SelectionBase):

    def __init__(self, interface, header: str, description: str, reactions: list, **kwargs):
        super().__init__(interface, header, description, **kwargs)

        if not kwargs.get('first', False):
            self.fields.append({'name': self.interface.back_hint, 'value': '\u200b' + str(self.interface.back_emoji)})
        self.fields.append({'name': self.interface.cancel_hint, 'value': '\u200b' + str(self.interface.fail_emoji)})

        self.reactions = reactions

    async def run(self):
        reaction_task = self.interface.loop.create_task(self._add_reactions())
        try:
            reaction, user = await self.interface.bot.wait_for('reaction_add', timeout=self.interface.timeout,
                                                               check=self._check)
        except asyncio.TimeoutError:
            reaction_task.cancel()
            await self.interface.message.clear_reactions()
            return SelectionResult(SelectionResultType.FAIL, 0)

        reaction_task.cancel()
        await self.interface.message.clear_reactions()
        emoji = reaction.emoji
        if emoji == self.interface.fail_emoji:
            return SelectionResult(SelectionResultType.FAIL, 1)
        if self is not self.interface.first and emoji == self.interface.back_emoji:
            return SelectionResult(SelectionResultType.BACK)
        self.next = self.result_events.get(emoji, self.result_events.get('*', None))
        return SelectionResult(SelectionResultType.SUCCESS, emoji)

    def _check(self, reaction, user):
        correct_reaction = False
        for reaction_ in self.reactions:
            if reaction_ != reaction.emoji:
                continue
            correct_reaction = True
            break
        return user is self.interface.member and (correct_reaction or reaction.emoji in self.interface_reactions)

    async def _add_reactions(self):
        for reaction in self.interface_reactions:
            await self.interface.message.add_reaction(reaction)
        for reaction in self.reactions:
            await self.interface.message.add_reaction(reaction)


class ConfirmSelection(ReactionSelection):

    def __init__(self, interface, head: str, desc: str, **kwargs):
        super().__init__(interface, head, desc, reactions=[interface.success_emoji], **kwargs)


class MultiReactionSelection(ReactionSelection):

    async def run(self):
        reaction_task = self.interface.loop.create_task(self._add_reactions())
        try:
            reaction, user = await self.interface.bot.wait_for('reaction_add', timeout=self.interface.timeout,
                                                               check=self._check)
        except asyncio.TimeoutError:
            reaction_task.cancel()
            await self.interface.message.clear_reactions()
            return SelectionResult(SelectionResultType.FAIL, 0)

        selections = []
        for reaction in reaction.message.reactions:
            if reaction.emoji not in self.reactions:
                continue
            users = await reaction.users().flatten()
            for user in users:
                if user is not self.interface.member:
                    continue
                selections.append(reaction.emoji)
                break

        reaction_task.cancel()
        await self.interface.message.clear_reactions()
        emoji = reaction.emoji
        if emoji is self.interface.fail_emoji:
            return SelectionResult(SelectionResultType.FAIL, 1)
        if self is not self.interface.first and emoji is self.interface.back_emoji:
            return SelectionResult(SelectionResultType.BACK)
        return SelectionResult(SelectionResultType.SUCCESS, selections)

    def _check(self, reaction, user):
        return user is self.interface.member and reaction.emoji in (self.interface_reactions +
                                                                    [self.interface.success_emoji])

    async def _add_reactions(self):
        for reaction in self.interface_reactions:
            await self.interface.message.add_reaction(reaction)
        for reaction in self.reactions:
            await self.interface.message.add_reaction(reaction)
        await self.interface.message.add_reaction(self.interface.success_emoji)


class TextSelection(SelectionBase):

    def __init__(self, interface, title, text, **kwargs):
        super().__init__(interface, title, text, **kwargs)

        if not kwargs.get('first', False):
            self.fields.append({'name': self.interface.back_hint, 'value': '\u200b' + str(self.interface.back_emoji)})
        self.fields.append({'name': self.interface.cancel_hint, 'value': '\u200b' + str(self.interface.fail_emoji)})

    async def run(self):
        reaction_task = self.interface.loop.create_task(self._add_reactions())

        done, pending = await asyncio.wait([
            self.interface.bot.wait_for('message', timeout=self.interface.timeout, check=self._check),
            self.interface.bot.wait_for('reaction_add', timeout=self.interface.timeout, check=self._check_cancel)
        ], return_when=asyncio.FIRST_COMPLETED)
        for future in pending:
            future.cancel()
        try:
            result = done.pop().result()
        except asyncio.TimeoutError:
            reaction_task.cancel()
            await self.interface.message.clear_reactions()
            return SelectionResult(SelectionResultType.FAIL, 0)

        reaction_task.cancel()
        await self.interface.message.clear_reactions()
        if type(result) is not discord.Message:
            return SelectionResult(SelectionResultType.FAIL, 1)
        self.next = self.result_events.get(result.content, self.result_events.get('*', None))
        data = result.content
        await result.delete()
        return SelectionResult(SelectionResultType.SUCCESS, data)

    def _check(self, user_input):
        return user_input.author is self.interface.member

    def _check_cancel(self, reaction, user):
        return user is self.interface.member and reaction.emoji in self.interface_reactions

    async def _add_reactions(self):
        for reaction in self.interface_reactions:
            await self.interface.message.add_reaction(reaction)


class SelectionSuccess(SelectionBase):

    def __init__(self, interface, header, description, **kwargs):
        super().__init__(interface, header, description, **kwargs)

        self.color = kwargs.get('color', self.interface.success_color)


class SelectionFail(SelectionBase):

    def __init__(self, interface, head: str, desc: str, allow_retry=True, **kwargs):
        super().__init__(interface, head, desc, **kwargs)

        if allow_retry:
            self.fields.append({'name': self.interface.retry_hint, 'value': '\u200b' + str(self.interface.retry_emoji)})

        self.allow_retry = allow_retry
        self.color = kwargs.get('color', interface.fail_color)

    async def run(self):
        if not self.allow_retry:
            return SelectionResult(SelectionResultType.NONE)
        await self.interface.message.add_reaction(self.interface.retry_emoji)
        try:
            await self.interface.bot.wait_for('reaction_add', timeout=self.interface.timeout, check=self._check)
        except asyncio.TimeoutError:
            await self.interface.message.clear_reactions()
            return SelectionResult(SelectionResultType.NONE)

        await self.interface.message.clear_reactions()
        return SelectionResult(SelectionResultType.RETRY)

    def _check(self, reaction, user):
        return user is self.interface.member and reaction.emoji == self.interface.retry_emoji


class SelectionResult:

    def __init__(self, type, value=None):
        self.type = type
        self.value = value


class ReplacedText:

    def __init__(self, text: str, *replace_functions):
        self.text = text
        self.replace_functions = replace_functions

    def get(self, result):
        replacements = [func(result) for func in self.replace_functions]
        return self.text.format(*replacements)


class SelectionType(Enum):
    SUCCESS = SelectionSuccess
    FAIL = SelectionFail  # 0 - timeout | 1 - cancel
    REACTION = ReactionSelection
    CONFIRM_SELECTION = ConfirmSelection
    MULTI_REACTION = MultiReactionSelection
    TEXT = TextSelection


class SelectionResultType(Enum):
    NONE = 0
    SUCCESS = 1
    FAIL = 2
    BACK = 3
    RETRY = 4


class SelectionInterface:

    def __init__(self, ctx, **kwargs):
        self.ctx = ctx
        self.bot = ctx.bot
        self.member = ctx.author
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.loop = self.bot.loop

        self.timeout = kwargs.get('timeout', 120)

        self.success_emoji = kwargs.get('success_emoji', '\U00002705')  # :white_check_mark:
        self.fail_emoji = kwargs.get('fail_emoji', '\U0000274c')  # :x:
        self.back_emoji = kwargs.get('back_emoji', '\U00002b05')  # :arrow_left:
        self.retry_emoji = kwargs.get('retry_emoji', '\U0001f501')  # :repeat:

        self.success_color = kwargs.get('success_color', discord.Color.green())
        self.fail_color = kwargs.get('fail_color', discord.Color.red())
        self.selection_color = kwargs.get('selection_color', discord.Color.dark_teal())

        self.header_icon = kwargs.get('header_icon', discord.embeds.EmptyEmbed)
        self.footer_icon = kwargs.get('footer_icon', discord.embeds.EmptyEmbed)

        self.abort_title = kwargs.get('abort_title', 'Selection Canceled')
        self.abort_text = kwargs.get('abort_text', 'The selection has been successfully canceled!')
        self.timeout_title = kwargs.get('timeout_title', 'Selection Canceled')
        self.timeout_text = kwargs.get('timeout_text', 'The selection has been canceled after {0:.1f} minutes!')\
            .format(self.timeout / 60)

        self.cancel_hint = kwargs.get('cancel_hint', '**Cancel**')
        self.retry_hint = kwargs.get('retry_hint', '**Retry**')
        self.back_hint = kwargs.get('back_hint', '**Back**')

        self.message = None
        self.first = None
        self.current_selection = None
        self._result = {}

    def check_url(self, url):
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return re.match(regex, url) is not None

    def set_base_selection(self, selection, header: str, desc: str, **kwargs):
        kwargs['first'] = True
        base_selection = selection.value(self, header, desc, **kwargs)
        self.first = base_selection
        self.current_selection = base_selection
        return self.current_selection

    async def start(self, retry=False):
        base_selection_msg = self.current_selection.build_message()
        if not retry:
            self.message = await self.channel.send(embed=base_selection_msg)
        else:
            await self.message.edit(embed=base_selection_msg)
        result = await self.current_selection.run()
        if result.type is SelectionResultType.SUCCESS:
            self._result[0] = result.value
            await self.current_selection.run_action()
        elif result.type is SelectionResultType.FAIL:
            if result.value == 0:
                self.current_selection.next = SelectionFail(self, self.timeout_title, self.timeout_text)
            elif result.value == 1:
                self.current_selection.next = SelectionFail(self, self.abort_title, self.abort_text, False)

        next_selection = self.current_selection.next
        if next_selection:
            next_selection.prev = self.current_selection
        self.current_selection = next_selection

        index = 1
        while self.current_selection:
            selection_msg = self.current_selection.build_message()
            await self.message.edit(embed=selection_msg)
            try:
                result = await self.current_selection.run()
                if result.type is SelectionResultType.SUCCESS:
                    self._result[index] = result.value
                    await self.current_selection.run_action()
                    index += 1
                elif result.type is SelectionResultType.BACK:
                    index -= 1
                    self.current_selection = self.current_selection.prev
                    continue
                elif result.type is SelectionResultType.FAIL:
                    if result.value == 0:
                        self.current_selection.next = SelectionFail(self, self.timeout_title, self.timeout_text)
                    elif result.value == 1:
                        self.current_selection.next = SelectionFail(self, self.abort_title, self.abort_text, False)
                elif result.type is SelectionResultType.RETRY:
                    self.current_selection = self.first
                    self._result = []
                    return await self.start(retry=True)
            except AttributeError:
                pass
            next_selection = self.current_selection.next
            if next_selection:
                next_selection.prev = self.current_selection
            self.current_selection = next_selection

    def result(self):
        return self._result
