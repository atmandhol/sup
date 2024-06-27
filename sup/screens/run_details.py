import emoji
import os
import pyperclip
import yaml
import re
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import Reactive
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Static,
    Tree,
    Label,
    TabbedContent,
    TabPane,
    MarkdownViewer,
    RichLog,
    Button,
)

from sup.k8s.k8s import KubectlCmd
from threading import Thread


# noinspection PyTypeChecker,PyBroadException
class RunDetail(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Show Run List"),
        ("c", "copy_logs", "Copy Log"),
        ("s", "goto_stage_list", "Stage List"),
        ("d", "goto_details", "Details"),
        ("l", "goto_logs", "Logs"),
    ]

    run_details = Reactive(dict())

    def __init__(self, run: str, namespace: str):
        super().__init__()
        self.run = run
        self.selected_stage = dict()
        self.stage_detail: str = "Select a stage to view the details"
        self.logs: str = "Select a stage to view the logs"
        self.namespace = namespace
        self.refresh_time_in_sec = 30

    @staticmethod
    def remove_colorization(text):
        ansi_escape = re.compile(
            r"""
                \x1B   # ESC
                (?:    # 7-bit C1 Fe (except CSI)
                    [@-Z\\-_]
                |      # or [ for CSI, followed by a control sequence
                    \[
                    [0-?]*  # Parameter bytes
                    [ -/]*  # Intermediate bytes
                    [@-~]   # Final byte
                )
            """,
            re.VERBOSE,
        )
        return ansi_escape.sub("", text)

    def action_copy_logs(self) -> None:
        pyperclip.copy(self.remove_colorization(self.logs))

    def action_goto_stage_list(self):
        tree = self.query_one("#stagesTree")
        tree.focus()

    def action_goto_details(self):
        tab = self.query_one(TabbedContent)
        tab.active = "detailsTab"
        mkd = self.query_one(MarkdownViewer)
        mkd.focus()

    def action_goto_logs(self):
        tab = self.query_one(TabbedContent)
        tab.active = "logsTab"
        log = self.query_one(RichLog)
        log.focus()

    def compose(self) -> ComposeResult:
        with Static(id="top_bar"):
            with Horizontal():
                with Vertical():
                    yield Label("Run: ", id="runLabel")
                    yield Label("Message: ", id="messageLabel")
                    yield Label("Status: ", id="statusLabel")
                    yield Label("Cause: ", id="causeLabel")
                yield Button.warning("Delete Run", id="deleteRunBtn")
        with Horizontal():
            with Static(id="side_bar"):
                yield Tree("Stages", id="stagesTree")
            with Static(id="data_panel"):
                with TabbedContent(id="tabbedContentPanel"):
                    with TabPane("Details", id="detailsTab"):
                        yield MarkdownViewer(
                            markdown=self.stage_detail,
                            show_table_of_contents=False,
                            id="markdownStageDetail",
                        )
                    with TabPane("Logs", id="logsTab"):
                        yield RichLog(id="logViewer", highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(self.refresh_time_in_sec, self.update_run_details)
        self.update_run_details()
        # Setup Markdown Viewer
        markdown: MarkdownViewer = self.query_one("#markdownStageDetail")
        markdown.show_table_of_contents = False
        markdown.show_vertical_scrollbar = True
        markdown.show_horizontal_scrollbar = False
        # Setup
        log_viewer: RichLog = self.query_one("#logViewer")
        log_viewer.show_vertical_scrollbar = True
        log_viewer.show_horizontal_scrollbar = False

        # Set initial focus
        tree: Tree = self.query_one("#stagesTree")
        tree.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "deleteRunBtn":
            try:
                KubectlCmd.delete_run(run=self.run, namespace=self.namespace)
                self.notify(
                    f"Run {self.run} in namespace {self.namespace} was deleted.",
                    timeout=10,
                )
                self.app.pop_screen()
            except Exception as err:
                self.notify(
                    f"Sup was unable to delete the run from the cluster. Error {err}",
                    title="Delete Error",
                    severity="error",
                    timeout=10,
                )

    def on_tree_node_selected(self, widget) -> None:
        if widget.node.data:
            self.selected_stage = widget.node
            self.populate_stage_details()
            self.populate_logs()

    # noinspection PyUnresolvedReferences
    def _populate_logs_handler(self):
        log_viewer: RichLog = self.query_one("#logViewer")
        log_viewer.clear()
        try:
            if self.selected_stage and not self.selected_stage.data.get("resumption"):
                stage_obj = (
                    self.selected_stage.data.get("status_stage").get("ref").get("name")
                )
                self.logs, cmd = KubectlCmd.get_stern_logs_for_stage(
                    stage_obj=stage_obj
                )
            else:
                resumption_obj = (
                    self.selected_stage.data.get("status_resumption")
                    .get("ref")
                    .get("name")
                )
                self.logs, cmd = KubectlCmd.get_stern_logs_for_resumption(
                    resumption_obj=resumption_obj
                )

            log_viewer.write(Text(self.logs))
        except Exception:
            log_viewer.write(
                Text(
                    "Could not get logs. Please make sure [bold]stern[/bold] CLI is installed."
                )
            )
            self.notify(
                "Sup was unable to get logs from the cluster. Make sure the cluster is accessible and the kubeconfig is valid.",
                title="Refresh Error",
                severity="error",
                timeout=self.refresh_time_in_sec,
            )

    def populate_logs(self):
        t = Thread(target=self._populate_logs_handler)
        t.start()

    # noinspection PyUnresolvedReferences
    def populate_stage_details(self):
        mkd: MarkdownViewer = self.query_one("#markdownStageDetail")
        mkd.show_table_of_contents = True
        try:
            if self.selected_stage and not self.selected_stage.data.get("resumption"):
                path = os.path.dirname(os.path.abspath(__file__)).replace(
                    "/screens", f"/templates/stage_detail.md"
                )
                tpl = open(path, "r").read()
                run_spec_stage = self.selected_stage.data.get("run_spec_stage")
                status_stage = self.selected_stage.data.get("status_stage")
                final_data = (
                    str(tpl)
                    .replace(
                        "%component_name",
                        run_spec_stage.get("componentRef").get("name"),
                    )
                    .replace(
                        "%namespace",
                        run_spec_stage.get("componentRef").get("namespace"),
                    )
                    .replace(
                        "%outputs",
                        yaml.dump(
                            run_spec_stage.get("outputs", "No Outputs to report")
                        ),
                    )
                    .replace(
                        "%pipelinerun_name",
                        status_stage.get("pipelineRun").get("ref").get("name")
                        if status_stage.get("pipelineRun")
                        else "PipelineRun not created",
                    )
                    .replace(
                        "%pipelinerun_ns",
                        status_stage.get("pipelineRun").get("ref").get("namespace")
                        if status_stage.get("pipelineRun")
                        else "PipelineRun not created",
                    )
                    .replace(
                        "%pipeline_passed",
                        str(run_spec_stage.get("pipeline").get("passed", "Did not run"))
                        if run_spec_stage.get("pipeline")
                        and run_spec_stage.get("pipeline").get("passed") is not None
                        else "Stage did not run/finish",
                    )
                    .replace(
                        "%pipeline_start",
                        run_spec_stage.get("pipeline").get("started", "Did not run")
                        if run_spec_stage.get("pipeline")
                        and run_spec_stage.get("pipeline").get("started")
                        else "Stage did not run/finish",
                    )
                    .replace(
                        "%pipeline_end",
                        run_spec_stage.get("pipeline").get("completed", "Did not run")
                        if run_spec_stage.get("pipeline")
                        and run_spec_stage.get("pipeline").get("completed")
                        else "Stage did not run/finish",
                    )
                    .replace(
                        "%pipeline_results",
                        yaml.dump(
                            run_spec_stage.get("pipeline").get(
                                "results", "No Results to Show"
                            )
                        )
                        if run_spec_stage.get("pipeline")
                        and run_spec_stage.get("pipeline").get("passed") is not None
                        else "No Results to show",
                    )
                    .replace(
                        "%pipeline_message",
                        run_spec_stage.get("pipeline").get("message", "Did not run")
                        if run_spec_stage.get("pipeline")
                        and run_spec_stage.get("pipeline").get("message")
                        else "Stage did not run/finish",
                    )
                )
            else:
                path = os.path.dirname(os.path.abspath(__file__)).replace(
                    "/screens", f"/templates/resumption_detail.md"
                )
                tpl = open(path, "r").read()
                run_spec_resumption = self.selected_stage.data.get(
                    "run_spec_resumption"
                )
                status_resumption = self.selected_stage.data.get("status_resumption")

                final_data = (
                    str(tpl)
                    .replace(
                        "%resumption_stage_name",
                        status_resumption.get("name"),
                    )
                    .replace(
                        "%resumption_name",
                        status_resumption.get("ref").get("name"),
                    )
                    .replace(
                        "%namespace",
                        status_resumption.get("ref").get("namespace"),
                    )
                    .replace(
                        "%key",
                        run_spec_resumption.get("key")
                        if "key" in run_spec_resumption
                        else "Resumption did not run/finish",
                    )
                    .replace(
                        "%message",
                        run_spec_resumption.get("message")
                        if "message" in run_spec_resumption
                        else "Resumption did not run/finish",
                    )
                    .replace(
                        "%taskrun_name",
                        status_resumption.get("taskRun").get("ref").get("name")
                        if status_resumption.get("taskRun")
                        else "taskRun not created",
                    )
                    .replace(
                        "%taskrun_ns",
                        status_resumption.get("taskRun").get("ref").get("namespace")
                        if status_resumption.get("taskRun")
                        else "taskRun not created",
                    )
                    .replace(
                        "%task_passed",
                        str(run_spec_resumption.get("passed", "Did not run"))
                        if run_spec_resumption.get("passed") is not None
                        else "Resumption did not run/finish",
                    )
                    .replace(
                        "%task_start",
                        run_spec_resumption.get("started", "Did not run")
                        if run_spec_resumption.get("started")
                        else "Resumption did not run/finish",
                    )
                    .replace(
                        "%task_end",
                        run_spec_resumption.get("completed", "Did not run")
                        if run_spec_resumption.get("completed")
                        else "Resumption did not run/finish",
                    )
                    .replace(
                        "%task_results",
                        yaml.dump(
                            run_spec_resumption.get("results", "No Results to Show")
                        )
                        if run_spec_resumption.get("passed") is not None
                        else "No Results to show",
                    )
                    .replace(
                        "%task_digest",
                        run_spec_resumption.get("resultDigest", "Did not run")
                        if run_spec_resumption.get("resultDigest")
                        else "Resumption did not run/finish",
                    )
                )

            self.stage_detail = final_data
            mkd.document.update(self.stage_detail)
            mkd.document.refresh(layout=True, recompose=True)
        except Exception as err:
            self.notify(
                f"Sup was unable to get Stage/Resumption details from the cluster. Error {err}",
                title="Refresh Error",
                severity="error",
                timeout=self.refresh_time_in_sec,
            )

    def populate_stage_tree(self):
        tree: Tree = self.query_one("#stagesTree")
        tree.clear()
        stages_node = tree.root
        stages_node.expand()
        ct = 0
        for run_spec_stage in (
            self.run_details.get("status").get("workloadRun").get("spec").get("stages")
        ):
            if not run_spec_stage.get("pipeline"):
                ej = emoji.emojize(":white_circle: ")
                status_stage = {}
            elif run_spec_stage.get("pipeline").get(
                "started"
            ) and not run_spec_stage.get("pipeline").get("completed"):
                ej = emoji.emojize(":blue_circle: ")
                status_stage = self.run_details.get("status").get("stages", [])[ct]
            elif (
                run_spec_stage.get("pipeline").get("passed")
                and run_spec_stage.get("pipeline").get("passed") is True
            ):
                ej = emoji.emojize(":green_circle: ")
                status_stage = self.run_details.get("status").get("stages", [])[ct]
            else:
                ej = emoji.emojize(":red_circle: ")
                status_stage = self.run_details.get("status").get("stages", [])[ct]

            stg_node = stages_node.add_leaf(
                ej + run_spec_stage.get("name"),
                {
                    "run_spec_stage": run_spec_stage,
                    "status_stage": status_stage,
                    "resumption": False,
                },
            )

            if run_spec_stage.get("resumptions"):
                rct = 0
                for r in run_spec_stage.get("resumptions"):
                    if not r.get("started") and not r.get("completed"):
                        ej = emoji.emojize(":white_circle: ")
                        status_resumption = {}
                    elif r.get("started") and not r.get("completed"):
                        ej = emoji.emojize(":blue_circle: ")
                        status_resumption = (
                            self.run_details.get("status")
                            .get("stages", [])[ct]
                            .get("resumptions", [])[rct]
                        )
                    elif r.get("passed") and r.get("passed") is True:
                        ej = emoji.emojize(":green_circle: ")
                        status_resumption = (
                            self.run_details.get("status")
                            .get("stages", [])[ct]
                            .get("resumptions", [])[rct]
                        )
                    else:
                        ej = emoji.emojize(":red_circle: ")
                        status_resumption = (
                            self.run_details.get("status")
                            .get("stages", [])[ct]
                            .get("resumptions", [])[rct]
                        )

                    stg_node.add_leaf(
                        ej + r.get("name"),
                        {
                            "run_spec_resumption": r,
                            "resumption": True,
                            "status_resumption": status_resumption,
                        },
                    )
                    stg_node.expand_all()
                    rct += 1
            ct += 1

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

    def _update_run_details_handler(self):
        try:
            self.run_details = KubectlCmd.get_run_detail(self.run, self.namespace)
        except Exception:
            self.notify(
                "Sup was unable to get Run details from the cluster. Make sure the cluster is accessible and the kubeconfig is valid.",
                title="Refresh Error",
                severity="error",
                timeout=self.refresh_time_in_sec,
            )

    def update_run_details(self):
        t = Thread(target=self._update_run_details_handler)
        t.run()

    def watch_run_details(self):
        self.populate_stage_tree()
        self.populate_top_bar()
        if self.selected_stage:
            self.populate_stage_details()
