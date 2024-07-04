from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import Reactive

from textual.widgets import Static, Label, Button


class TopBar(Static):
    """Run list"""

    run_details = Reactive(dict())

    def __init__(self, run, namespace):
        super().__init__(id="top_bar")
        self.run = run
        self.namespace = namespace

    def compose(self) -> ComposeResult:
        with Static():
            with Horizontal():
                with Vertical():
                    yield Label("Run: ", id="runLabel")
                    yield Label("Message: ", id="messageLabel")
                    yield Label("Status: ", id="statusLabel")
                    yield Label("Cause: ", id="causeLabel")
                yield Button.warning("Delete Run", id="deleteRunBtn")

    def populate(self, run_details):
        self.query_one("#runLabel").renderable = (
            Text("Run: ", style="#f59145")
            + Text(f"{self.run}", style="bold #ffffff")
            + " in "
            + Text(f"{self.namespace}", style="bold #ffffff")
            + " namespace"
        )

        msg = str(
            run_details.get("status").get("conditions")[1].get("message").split(".")[0]
        )
        if not msg:
            msg = "Nothing to show here."
        self.query_one("#messageLabel").renderable = Text(
            "Message: ", style="#f59145"
        ) + Text(
            f"{msg}",
            style="bold #ffffff",
        )

        ready = str(run_details.get("status").get("conditions")[1].get("reason"))
        self.query_one("#statusLabel").renderable = Text("Status: ", style="#f59145")
        if ready == "Succeeded":
            self.query_one("#statusLabel").renderable += Text(
                ready,
                style="bold #03AC13",
            )
        elif ready == "Failed":
            self.query_one("#statusLabel").renderable += Text(
                ready,
                style="bold #d1573f",
            )
        elif ready == "PlatformFailed":
            self.query_one("#statusLabel").renderable += Text(
                ready,
                style="bold #fc9847",
            )
        else:
            self.query_one("#statusLabel").renderable += Text(
                ready,
                style="bold #3f9bd1",
            )

        self.query_one("#causeLabel").renderable = Text(
            "Cause: ", style="#f59145"
        ) + Text(
            f'{run_details.get("spec").get("cause").get("message")}',
            style="bold #ffffff",
        )
