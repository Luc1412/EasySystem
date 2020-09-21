from commandchannel.commandchannel import CommandChannel


def setup(bot):
    bot.add_cog(CommandChannel(bot))
