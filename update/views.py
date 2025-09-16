import discord.ui


class UpdateModal(discord.ui.Modal, title="Compose Update"):
    title_input = discord.ui.Label(
        text="Title",
        component=discord.ui.TextInput(label="Title", placeholder="Enter title..."),
    )
    text_input = discord.ui.Label(
        text="Text",
        component=discord.ui.TextInput(placeholder="Enter text..."),
    )
    interaction: discord.Interaction

    def __init__(self, title: str | None = None, text: str | None = None):
        super().__init__()
        assert isinstance(self.title_input.component, discord.ui.TextInput)
        assert isinstance(self.text_input.component, discord.ui.TextInput)
        self.title_input.component.default = title
        self.text_input.component.default = text

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        self.interaction = interaction

    def build_view(self) -> discord.ui.LayoutView:
        assert isinstance(self.title_input.component, discord.ui.TextInput)
        assert isinstance(self.text_input.component, discord.ui.TextInput)
        view = discord.ui.LayoutView()
        view.add_item(
            discord.ui.TextDisplay(
                f"# {self.title_input.component.value}\n"
                f"{self.text_input.component.value}"
            )
        )
        return view


class ResponseView(discord.ui.LayoutView):
    def __init__(self, title: str, text: str) -> None:
        super().__init__()
        self.add_item(discord.ui.TextDisplay(f"# {title}\n{text}"))


class ConfirmView(discord.ui.LayoutView):
    interaction: discord.Interaction

    def __init__(self, items: list[discord.ui.Item]) -> None:
        super().__init__()
        for item in items:
            self.add_item(item)
        self.add_item(
            discord.ui.Separator(spacing=discord.SeparatorSpacing.large)
        ).add_item(
            discord.ui.Section(
                discord.ui.TextDisplay("**Do you want to send the update message?**"),
                accessory=ConfirmButton(self),
            )
        )


class ConfirmButton(discord.ui.Button):
    def __init__(self, view: ConfirmView) -> None:
        super().__init__(style=discord.ButtonStyle.green, label="Confirm")
        self.__view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        self.__view.interaction = interaction
