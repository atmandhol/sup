from textual.app import ComposeResult
from textual.binding import Binding
from textual.reactive import Reactive
from textual.widgets import Static, DataTable
from k8s.k8s import KubectlCmd
from rich.text import Text


class RunList(Static):
    """Run list"""

    run_data = Reactive(list())

    def __init__(self):
        super().__init__()
        # Possible values supplyChain, created, ready
        self.sort_by = "supplychain"
        self.sort_asc = True

    BINDINGS = [
        Binding("alt+s", "sort_by_supplychain", "Sort by Supply Chains", show=True),
        Binding("alt+t", "sort_by_time", "Sort by Time", show=True),
        Binding("alt+u", "sort_by_status", "Sort by Status", show=True),
        Binding("alt+d", "asc_desc", "ASC/DESC", show=True),
        Binding("ctrl+c", "app.quit", "Quit"),
    ]

    def action_asc_desc(self) -> None:
        self.sort_asc = not self.sort_asc
        table = self.query_one(DataTable)
        table.sort(reverse=self.sort_asc)

    def action_sort_by_supplychain(self) -> None:
        self.sort_by = "supplychain"
        table = self.query_one(DataTable)
        table.sort(self.sort_by, key=lambda supplychain: supplychain.plain, reverse=self.sort_asc)

    def action_sort_by_time(self) -> None:
        self.sort_by = "created"
        table = self.query_one(DataTable)
        table.sort(self.sort_by, key=lambda created: created.plain, reverse=self.sort_asc)

    def action_sort_by_status(self) -> None:
        self.sort_by = "ready"
        table = self.query_one(DataTable)
        table.sort(self.sort_by, key=lambda ready: ready.plain, reverse=self.sort_asc)

    def compose(self) -> ComposeResult:
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
        )
        table.add_columns(*run_list)
        self.set_interval(10 / 60, self.update_run_data)

    def update_run_data(self):
        self.run_data = KubectlCmd.get_run_list()

    def watch_run_data(self):
        table = self.query_one(DataTable)
        table.clear()
        for run in self.run_data:
            styled_row = list()
            styled_row.append(
                Text(
                    str(run.get("metadata").get("namespace")),
                    style="#96999e",
                )
            )
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
            styled_row.append(
                Text(
                    str(
                        run.get("metadata")
                        .get("labels")
                        .get("supply-chain.apps.tanzu.vmware.com/workload-name")
                    ),
                    style="italic #ffba61",
                )
                + "/"
                + Text(
                    str(run.get("metadata").get("name")),
                    style="#ffffff",
                ),
            )

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
            else:
                styled_row.append(
                    Text(
                        ready,
                        style="italic #3f9bd1",
                        justify="right",
                    )
                )
            styled_row.append(
                Text(
                    str(run.get("metadata").get("creationTimestamp")),
                    style="#ffffff",
                )
            )

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
            table.add_row(*styled_row)

