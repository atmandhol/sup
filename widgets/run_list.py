from textual.app import ComposeResult
from textual.widgets import Static, Input, Button, DataTable, Label
from k8s.k8s import KubectlCmd
from rich.text import Text


class RunList(Static):
    """Run list"""

    def __init__(self):
        super().__init__()
        self.failed = False
        self.latest_in_workload = True
        self.run_data = list()

    def compose(self) -> ComposeResult:
        # yield Input(placeholder="Search Run", id="runSearchInput")
        # yield Button("Reset", id="resetButton")
        yield DataTable(id="runDataTable")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        self.run_data = KubectlCmd.get_run_list()
        run_list = (
            "Namespace",
            "Supply Chain",
            "Run",
            "Ready",
            "Created",
            "Progress",
        )

        table.add_columns(*run_list)

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
            styled_row.append(
                Text(
                    "84%",
                    style="#ffffff",
                )
            )
            table.add_row(*styled_row)
