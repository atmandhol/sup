from textual.app import ComposeResult

from textual.widgets import Static, Input, ListView, ListItem, Label, Button


class RunPanel(Static):
    """Run list"""

    def __init__(self):
        super().__init__()
        self.failed = False
        self.latest_in_workload = True

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search Run")
        yield Button("Reset", variant="error")
        yield ListView(
            ListItem(Label("One")),
            ListItem(Label("Two")),
            ListItem(Label("Three")),
        )
