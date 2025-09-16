from __future__ import annotations

import discord


class ResponseView(discord.ui.LayoutView):
    def __init__(self, title: str, text: str) -> None:
        super().__init__()
        self.add_item(discord.ui.TextDisplay(f"# {title}\n{text}"))
