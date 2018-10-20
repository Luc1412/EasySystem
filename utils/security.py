class SecurityManager:

    def __init__(self, bot):
        self.bot = bot

    def _invite_check(self, url):
        url = url.lower()
        if not url.__conatins__('https://discord.gg'):
            return
        invite = self.bot.get_invite(url)
        # invite.guild.id
