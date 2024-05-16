from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.reactive import Reactive
from textual.widgets import (
    Static,
    DataTable,
    Input,
    Switch,
    Label,
    Select,
)
from sup.k8s.k8s import KubectlCmd
from rich.text import Text
from sup.screens.run_details import RunDetail


class RunList(Static):
    """Run list"""

    run_data = Reactive(list())
    filter_string = Reactive(str())
    supply_chains = Reactive(list())
    selected_chain = Reactive(str())
    selected_status = Reactive(str())
    latest_run = Reactive(bool)

    def __init__(self):
        super().__init__()
        self.refresh_time_in_sec = 30

    BINDINGS = [
        Binding("ctrl+c", "app.quit", "Quit"),
        Binding("s", "search_run", "Search Run"),
        Binding("escape", "clear_filter", "Clear Filter"),
    ]

    def action_search_run(self):
        search_bar = self.query_one(Input)
        search_bar.focus()

    def action_clear_filter(self):
        search_bar = self.query_one("#filterInput")
        search_bar.value = ""
        search_bar.focus()

    def compose(self) -> ComposeResult:
        with Static(id="top_bar"):
            with Horizontal():
                yield Label("Show only latest:")
                yield Switch(value=True)
                yield Label("Filter by chain:")
                yield Select([("all", "all")], allow_blank=False, id="chainSelect")
                yield Label("Filter by status:")
                yield Select(
                    [
                        ("all", "all"),
                        ("Running", "Running"),
                        ("Succeeded", "Succeeded"),
                        ("Failed", "Failed"),
                        ("PlatformFailed", "PlatformFailed"),
                    ],
                    allow_blank=False,
                    id="statusSelect",
                )

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
        self.set_interval(self.refresh_time_in_sec, self.update_data)
        self.update_data()

    # noinspection PyShadowingBuiltins
    def on_input_changed(self, input):
        self.filter_string = input.value

    # noinspection PyShadowingBuiltins
    def on_input_submitted(self, widget):
        if widget.input.id == "filterInput":
            self.query_one(DataTable).focus()

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "chainSelect":
            self.selected_chain = str(event.value)
        elif event.select.id == "statusSelect":
            self.selected_status = str(event.value)
        self.update_data()

    def on_data_table_row_selected(self, widget):
        data_table: DataTable = widget.data_table
        if data_table.id == "runDataTable":
            run_name = (
                str(data_table.get_row_at(widget.cursor_row)[1].plain)
                + "run/"
                + str(data_table.get_row_at(widget.cursor_row)[2].plain).split("/")[1]
            )
            ns = str(data_table.get_row_at(widget.cursor_row)[0].plain)
            # self.notify(run_name)
            self.app.push_screen(RunDetail(run=run_name, namespace=ns))

    # noinspection PyBroadException
    def update_data(self):
        try:
            self.run_data = KubectlCmd.get_run_list(
                chain=self.selected_chain, status=self.selected_status
            )
            self.supply_chains = KubectlCmd.get_sc_list()
            # self.notify(
            #     f"Run Data updated at {datetime.now()}",
            #     timeout=self.refresh_time_in_sec,
            # )
        except Exception as err:
            self.notify(
                f"Sup was unable to get Run data from the cluster. Make sure the cluster is accessible and the kubeconfig is valid. {err}",
                title="Refresh Error",
                severity="error",
                timeout=self.refresh_time_in_sec,
            )

    def watch_selected_chain(self):
        self.watch_run_data()

    def watch_selected_status(self):
        self.watch_run_data()

    # noinspection PyTypeChecker
    def watch_supply_chains(self):
        select: Select = self.query_one("#chainSelect")
        val = [("all", "all")]
        for sc in self.supply_chains:
            sc_name = sc.get("metadata").get("name")
            val.append((sc_name, sc_name))
        select.set_options(val)

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
