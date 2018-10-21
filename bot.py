#!/usr/bin/env python

import asyncio
import datetime
import gzip
import logging
import os
import shutil
import sys
import time
import traceback

import discord
import pytz
from discord.ext import commands
from discord.ext.commands import CommandOnCooldown

from utils.config import Config
from utils.database import Database
from utils.utils import Utils

start_time = time.time()


async def get_prefix(client, message):
    return '!'


initial_extensions = ['cogs.admin',
                      'cogs.events']


class Bot(commands.Bot):

    def __init__(self, *args, **kwargs):
        self.logger = set_logger()
        self.cfg = Config(self)
        self.db = Database(self)
        self.utils = Utils(self)
        super().__init__(*args, command_prefix=get_prefix, **kwargs)

    async def send_error(self, ctx: commands.Context, message: str, dm=False):
        error_message = discord.Embed()
        error_message.colour = self.utils.color.fail()
        error_message.description = f'{ctx.author.mention} {message}'
        error_message.set_footer(text=self.cfg.get('Core.Footer'), icon_url=self.cfg.get('Images.FooterIconURL'))
        if dm:
            error_message.set_author(name='An error occurred while executing the command!',
                                     icon_url=ctx.bot.cfg.get('Images.IconSmallURL'))
            await ctx.author.send(embed=error_message)
        else:
            error_message.set_author(name='An error occurred while executing the command!',
                                     icon_url=ctx.bot.cfg.get('Images.IconSmallURL'))
            await ctx.send(embed=error_message)

    async def send_embed(self, ctx: commands.Context, title, content, color):
        embed_message = discord.Embed()
        embed_message.colour = color
        embed_message.set_author(name=title, icon_url='')
        embed_message.description = content
        embed_message.set_footer(text='', icon_url='')

        await ctx.send(embed=embed_message)


def init(bot_class=Bot):
    client = bot_class(description='EasySystem Bot', case_insensitive=True)

    for extension in initial_extensions:
        try:
            client.load_extension(extension)
        except Exception:
            client.logger.exception(f'Failed to load extension {extension}.')
            traceback.print_exc()

    @client.event
    async def on_ready():
        bot.loop.create_task(update())
        bot.logger.info(f'[CORE] The bot was started successfully after {str(int(time.time() - start_time))} seconds!')

    @client.event
    async def on_command_error(ctx, error):

        ignored = (commands.MissingRequiredArgument, commands.CommandNotFound)

        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        if isinstance(error, commands.NoPrivateMessage):
            return await bot.send_error(ctx, error='This command cannot be used in private messages.', dm=True)
        elif isinstance(error, commands.DisabledCommand):
            return await bot.send_error(ctx, 'General.CommandMaintenance')
        elif isinstance(error, discord.Forbidden):
            return await ctx.bot.send_perm_warn(ctx)
        elif isinstance(error, CommandOnCooldown):
            return await bot.send_error(ctx, error=ctx.bot.lang.get(ctx.guild, 'General.CooldownMessage')
                                        .replace('%seconds%', str(int(error.retry_after + 1.00))))
        else:
            raise error

    @client.event
    async def on_error(event, *args, **kwargs):
        import traceback
        bot.logger.exception(traceback.format_exc())
        return
        bot.logger.exception(traceback.format_exc())

        error_message = discord.Embed()
        error_message.colour = bot.utils.color.fail()
        error_message.set_author(name='An error occurred!',
                                 icon_url=bot.cfg.get('Images.IconSmallURL'))
        error_message.description = f'```py\n{traceback.format_exc()}\n```'
        error_message.set_footer(text=bot.cfg.get('Core.Footer'),
                                 icon_url=bot.cfg.get('Images.FooterIconURL'))
        error_message.timestamp = datetime.datetime.now(pytz.timezone('Europe/Berlin'))
        await bot.utils.channel.error().send(embed=error_message)

    @client.event
    async def on_command(ctx: commands.Context):
        if not isinstance(ctx.channel, discord.TextChannel):
            return
        client.logger.info(f'[CORE] {ctx.author.name} on {ctx.guild.name}: {ctx.message.content}')

    @client.event
    async def process_commands(message: discord.Message):
        ctx = await client.get_context(message, cls=commands.Context)
        if ctx.valid:
            await client.invoke(ctx)

    return client


class DiscordHandler(logging.Handler):

    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self._channel = channel

    def emit(self, record):
        if not bot.is_ready():
            return
        log_entry = self.format(record)
        bot.loop.create_task(self._channel.send(log_entry))


def set_logger():
    logger = logging.getLogger('bot')
    logger.setLevel(logging.DEBUG)
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.INFO)
    log_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)
    discord_logger.addHandler(console_handler)

    if sys.argv.__contains__('-NoFileLog'):
        return logger

    if not os.path.exists('logs'):
        os.makedirs('logs')
    if os.path.isfile('logs//latest.log'):
        filename = None
        index = 1
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        while filename is None:
            check_filename = f'{date}-{index}.log.gz'
            if os.path.isfile(f'logs//{check_filename}'):
                index += 1
            else:
                filename = check_filename
        with open('logs//latest.log', 'rb') as f_in, gzip.open(f'logs//{filename}', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        os.remove('logs//latest.log')

    file_handler = logging.FileHandler(filename='logs//latest.log', encoding='utf-8', mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
    discord_logger.addHandler(file_handler)

    return logger


async def update():
    motd_nbr = 0

    while False:  # TODO: Change
        motd_data = bot.utils.get_motd_playlist()[motd_nbr]
        motd_type = None
        if motd_data[0] == 'p':
            motd_type = discord.ActivityType.playing
        elif motd_data[0] == 'l':
            motd_type = discord.ActivityType.listening
        elif motd_data[0] == 'w':
            motd_type = discord.ActivityType.watching
        activity = discord.Activity()
        activity.type = motd_type
        activity.name = motd_data[1]
        await bot.change_presence(activity=activity, status=discord.Status.online)

        if motd_nbr >= len(bot.utils.get_motd_playlist()) - 1:
            motd_nbr = 0
        else:
            motd_nbr += 1

        bot.db.stats.set_guild_amount()
        await asyncio.sleep(60)


async def main(efs_bot: Bot):
    efs_bot.remove_command("help")
    await efs_bot.login(efs_bot.cfg.get('Core.Token'))
    await efs_bot.connect()


if __name__ == '__main__':
    bot = init()
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main(bot))
    except discord.LoginFailure:
        bot.logger.exception(traceback.format_exc())
    except Exception as e:
        bot.logger.exception('[CORE] Fatal exception! Bot is not able to login! Attempting graceful logout!',
                             exc_info=e)
        loop.run_until_complete(bot.logout())
    finally:
        loop.close()
        exit(0)
