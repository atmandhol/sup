from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import Reactive
from textual.widgets import Static, DataTable, Input
from sup.k8s.k8s import KubectlCmd
from rich.text import Text
from datetime import datetime


class RunList(Static):
    """Run list"""

    run_data = Reactive(list())
    filter_string = Reactive(str())

    def __init__(self):
        super().__init__()
        self.refresh_time_in_sec = 30

    BINDINGS = [
        Binding("ctrl+c", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Input(id="filterInput")
            yield DataTable(id="runDataTable")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        run_list = (
            "namespace",
            "supplychain",
            "run",
            "ready",
            "created",
            "progress",
            "message",
        )
        table.add_columns(*run_list)
        self.set_interval(self.refresh_time_in_sec, self.update_run_data)
        self.update_run_data()

    def on_input_changed(self, input):
        self.filter_string = input.value

    # noinspection PyBroadException
    def update_run_data(self):
        try:
            self.run_data = KubectlCmd.get_run_list()
            self.notify(f"Run Data updated at {datetime.now()}", timeout=self.refresh_time_in_sec)
        except Exception:
            self.notify(
                "Sup was unable to get Run data from the cluster. Make sure the cluster is accessible and the kubeconfig is valid.",
                title="Refresh Error",
                severity="error",
                timeout=self.refresh_time_in_sec,
            )

    def watch_filter_string(self):
        self.watch_run_data()

    def watch_run_data(self):
        table = self.query_one(DataTable)
        current_pos = table.cursor_row
        y_pos = table.scroll_y
        table.clear()
        for run in self.run_data:
            if self.filter_string and self.filter_string not in (
                str(
                    run.get("metadata")
                    .get("labels")
                    .get("supply-chain.apps.tanzu.vmware.com/workload-name")
                )
                + "/"
                + str(run.get("metadata").get("name"))
            ):
                continue

            styled_row = list()

            # Namespace
            styled_row.append(
                Text(
                    str(run.get("metadata").get("namespace")),
                    style="#96999e",
                )
            )

            # Supply chain
            styled_row.append(
                Text(
                    str(
                        run.get("metadata")
                        .get("labels")
                        .get("supply-chain.apps.tanzu.vmware.com/workload-kind")
                    ),
                    style="italic #ffffff",
                )
            )

            # Name
            styled_row.append(
                Text(
                    str(
                        run.get("metadata")
                        .get("labels")
                        .get("supply-chain.apps.tanzu.vmware.com/workload-name")
                    ),
                    style="#dbce0d",
                )
                + "/"
                + Text(
                    str(run.get("metadata").get("name")),
                    style="italic #ffffff",
                ),
            )

            # Status
            ready = str(run.get("status").get("conditions")[1].get("reason"))
            if ready == "Succeeded":
                styled_row.append(
                    Text(
                        ready,
                        style="italic #03AC13",
                        justify="right",
                    )
                )
            elif ready == "Failed":
                styled_row.append(
                    Text(
                        ready,
                        style="italic #d1573f",
                        justify="right",
                    )
                )
            elif ready == "PlatformFailed":
                styled_row.append(
                    Text(
                        ready,
                        style="italic #fc9847",
                        justify="right",
                    )
                )
            else:
                styled_row.append(
                    Text(
                        ready,
                        style="italic #3f9bd1",
                        justify="right",
                    )
                )

            # Timestamp
            styled_row.append(
                Text(
                    str(run.get("metadata").get("creationTimestamp")),
                    style="#ffffff",
                )
            )

            # Progress
            progress_line = Text(str(""))

            for stage in run.get("status").get("workloadRun").get("spec").get("stages"):
                for resumption in stage.get("resumptions", []):
                    if (
                        resumption.get("passed", None)
                        and resumption.get("passed", None) is True
                    ):
                        progress_line += Text("✓", style="bold #22c91c")
                    elif (
                        resumption.get("passed", None)
                        and resumption.get("passed", None) is False
                    ):
                        progress_line += Text("X", style="bold #c91c28")
                    else:
                        progress_line += Text("-", style="bold #ffffff")
                pipeline = stage.get("pipeline", {})
                if (
                    pipeline.get("passed", None) is not None
                    and pipeline.get("passed", None) is True
                ):
                    progress_line += Text("✓", style="bold #22c91c")
                elif (
                    pipeline.get("passed", None) is not None
                    and pipeline.get("passed", None) is False
                ):
                    progress_line += Text("X", style="bold #c91c28")
                else:
                    progress_line += Text("-", style="bold #ffffff")

            styled_row.append(progress_line)

            # Message
            styled_row.append(
                Text(
                    str(
                        run.get("status")
                        .get("conditions")[1]
                        .get("message")
                        .split(".")[0]
                    ),
                    style="#ffffff",
                )
            )

            table.add_row(*styled_row)
            table.move_cursor(row=current_pos)
            table.scroll_target_y = y_pos
