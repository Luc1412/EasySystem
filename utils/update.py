import discord
from redbot.core import Config
from redbot.core.commands import commands

BaseCog = getattr(commands, "Cog", object)


class Utils(BaseCog):
    """"""

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, 123342543665)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != 341939185051107330:
            return
        if member.bot:
            return
        user = member.guild.get_role(341940567023943690)
        splitter = member.guild.get_role(538409250544680960)
        notification = member.guild.get_role(500999972452565012)
        await member.add_roles(user, splitter, notification)
