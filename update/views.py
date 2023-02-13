from typing import Optional

import discord.ui


class UpdateModal(discord.ui.Modal, title='Update'):
    title_input = discord.ui.TextInput(label="Title", placeholder="Enter title...")
    text_input = discord.ui.TextInput(label="Text", placeholder="Enter text...", style=discord.TextStyle.long)
    interaction: discord.Interaction

    def __init__(self, title: Optional[str] = None, text: Optional[str] = None):
        super().__init__()
        self.title_input.default = title
        self.text_input.default = text

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        await interaction.channel.send('Submitted')
        self.interaction = interaction


class UpdateConfirmView(discord.ui.View):
    interaction: discord.Interaction

    def __init__(self):
        super().__init__(timeout=5 * 60)

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction, /) -> None:
        self.interaction = interaction
