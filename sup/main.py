from textual.app import App, ComposeResult
from textual.widgets import Footer

from widgets.run_list import RunList


# noinspection PyTypeChecker
class Sup(App):
    """An Interactive CLI for Tanzu Supply Chain"""

    TITLE = "Sup - Interactive CLI for Tanzu Supply Chain"

    CSS_PATH = "styles/sup.css"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Footer()
        yield RunList()


if __name__ == "__main__":
    app = Sup()
    app.run()
