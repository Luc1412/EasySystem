from emojimanager.emoji_manager import EmojiManager


def setup(bot):
    bot.add_cog(EmojiManager(bot))
