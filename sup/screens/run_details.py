from textual.app import ComposeResult
from textual.reactive import Reactive
from textual.screen import Screen
from textual.widgets import Label, Footer
from sup.k8s.k8s import KubectlCmd


class RunDetail(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Show Run List")]

    run_details = Reactive(str())

    def __init__(self, run: str, namespace: str):
        super().__init__()
        self.run = run
        self.namespace = namespace
        self.refresh_time_in_sec = 5

    def compose(self) -> ComposeResult:
        yield Footer()
        yield Label()

    def on_mount(self) -> None:
        self.set_interval(self.refresh_time_in_sec, self.update_run_details)
        self.update_run_details()

    # noinspection PyBroadException
    def update_run_details(self):
        try:
            self.run_details = str(KubectlCmd.get_run_detail(self.run, self.namespace))
        except Exception:
            self.notify(
                "Sup was unable to get Run details from the cluster. Make sure the cluster is accessible and the kubeconfig is valid.",
                title="Refresh Error",
                severity="error",
                timeout=self.refresh_time_in_sec,
            )

    def watch_run_details(self):
        # Do something when the run data changes
        pass
