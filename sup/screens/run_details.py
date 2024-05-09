import emoji
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import Reactive
from textual.screen import Screen
from textual.widgets import Footer, Static, Tree, Label, TabbedContent, TabPane
from sup.k8s.k8s import KubectlCmd


class RunDetail(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Show Run List")]

    run_details = Reactive(dict())

    def __init__(self, run: str, namespace: str):
        super().__init__()
        self.run = run
        self.namespace = namespace
        self.refresh_time_in_sec = 5

    def compose(self) -> ComposeResult:
        with Static(id="top_bar"):
            yield Label("Run: ", id="runLabel")
            yield Label("Message: ", id="messageLabel")
            yield Label("Status: ", id="statusLabel")
            yield Label("Cause: ", id="causeLabel")
        with Horizontal():
            with Static(id="side_bar"):
                yield Tree("Stages", id="stagesTree")
            with Static(id="data_panel"):
                with TabbedContent():
                    with TabPane("Details", id="detailsTab"):
                        pass
                    with TabPane("Logs", id="logsTab"):
                        pass
                    with TabPane("YAML", id="yamlTab"):
                        pass
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(self.refresh_time_in_sec, self.update_run_details)
        self.update_run_details()

    def populate_stage_tree(self):
        # noinspection PyTypeChecker
        tree: Tree = self.query_one("#stagesTree")
        tree.clear()
        stages_node = tree.root
        stages_node.expand()
        for stage in (
            self.run_details.get("status").get("workloadRun").get("spec").get("stages")
        ):
            if not stage.get("pipeline"):
                ej = emoji.emojize(":white_circle: ")
            elif (
                stage.get("pipeline").get("started")
                and not stage.get("pipeline").get("completed")
            ):
                ej = emoji.emojize(":blue_circle: ")
            elif (
                stage.get("pipeline").get("passed")
                and stage.get("pipeline").get("passed") == True
            ):
                ej = emoji.emojize(":green_circle: ")
            else:
                ej = emoji.emojize(":red_circle: ")

            stages_node.add_leaf(ej + stage.get("name"), stage)

    def populate_top_bar(self):
        self.query_one("#runLabel").renderable = (
            Text("Run: ", style="#f59145")
            + Text(f"{self.run}", style="bold #ffffff")
            + " in "
            + Text(f"{self.namespace}", style="bold #ffffff")
            + " namespace"
        )

        msg = str(
            self.run_details.get("status")
            .get("conditions")[1]
            .get("message")
            .split(".")[0]
        )
        if not msg:
            msg = "Nothing to show here."
        self.query_one("#messageLabel").renderable = Text(
            "Message: ", style="#f59145"
        ) + Text(
            f"{msg}",
            style="bold #ffffff",
        )

        ready = str(self.run_details.get("status").get("conditions")[1].get("reason"))
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
            f'{self.run_details.get("spec").get("cause").get("message")}',
            style="bold #ffffff",
        )

    # noinspection PyBroadException
    def update_run_details(self):
        try:
            self.run_details = KubectlCmd.get_run_detail(self.run, self.namespace)
        except Exception:
            self.notify(
                "Sup was unable to get Run details from the cluster. Make sure the cluster is accessible and the kubeconfig is valid.",
                title="Refresh Error",
                severity="error",
                timeout=self.refresh_time_in_sec,
            )

    def watch_run_details(self):
        # Do something when the run data changes
        self.populate_top_bar()
        self.populate_stage_tree()
        pass
