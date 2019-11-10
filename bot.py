import asyncio
import datetime
import discord
import gzip
import logging
import os
import shutil
import sys
import time
import traceback
from discord.ext import commands
from utils.config import Config
from utils.context import Context
from utils.database import Database
from utils.utils import Utils

start_time = time.time()


class EasySystem(commands.Bot):

    def __init__(self, *args, **kwargs):
        self.logger = set_logger()
        self.cfg = Config(False)

        super().__init__(*args, command_prefix='!', **kwargs, owner_id=int(self.cfg.get('Core.OwnerID')))

        self.db = Database(self)
        self.utils = Utils(self)

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


def init(bot_class=EasySystem):
    client = bot_class(description='EasySystem Bot', case_insensitive=True)
    client.remove_command("help")

    extensions = client.cfg.get('Core.InitialCogs').split(', ')

    for extension in extensions:
        try:
            client.load_extension(f'cogs.{extension}')
        except Exception:
            client.logger.exception(f'Failed to load extension {extension}.')
            traceback.print_exc()

    @client.event
    async def on_ready():
        global start_time
        if start_time == 0.0:
            return
        bot.logger.info(f'[CORE] The bot was started successfully after {int(time.time() - start_time)} seconds.')
        start_time = 0.0

    @client.event
    async def on_command_error(ctx, error):

        ignored = (commands.MissingRequiredArgument, commands.CommandNotFound, commands.BadArgument, discord.NotFound,
                   commands.NotOwner)

        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        raise error

    @client.event
    async def on_error(event, *args, **kwargs):
        await bot.utils.report_exception(traceback.format_exc())

    @client.event
    async def on_command(ctx):
        client.logger.info(f'[CORE] {ctx.author} on {ctx.guild.name}: {ctx.message.content}')

    @client.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return
        if not isinstance(message.channel, discord.TextChannel):
            return
        await client.process_commands(message)

    @client.event
    async def process_commands(message: discord.Message):
        await client.wait_until_ready()
        ctx = await client.get_context(message, cls=Context)
        if not ctx.valid:
            return
        await client.invoke(ctx)

    return client


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


async def main(efs_bot: EasySystem):
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
