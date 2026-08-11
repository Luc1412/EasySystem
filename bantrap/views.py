from __future__ import annotations

import discord


class MessageView(discord.ui.LayoutView):
    def __init__(
        self,
        title: str,
        text: str,
        *,
        colour: discord.Colour | None = None,
    ) -> None:
        super().__init__()
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(f"## {title}\n{text}"),
                accent_colour=colour or discord.Colour.blurple(),
            )
        )
