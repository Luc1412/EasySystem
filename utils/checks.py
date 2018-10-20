from discord.ext import commands


def is_guild_owner():
    def predicate(ctx: commands.Context):
        return ctx.bot.guilds[0].owner == ctx.author

    return commands.check(predicate)
