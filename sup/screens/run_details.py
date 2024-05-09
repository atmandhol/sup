from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label


class RunDetail(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Show Run List")]

    def __init__(self, run: str):
        super().__init__()
        self.run = run

    def compose(self) -> ComposeResult:
        yield Label(self.run)
        pass
