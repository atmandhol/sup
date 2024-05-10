import emoji
import os
import yaml
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
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
)

# noinspection PyProtectedMember
from textual.widgets._tree import TreeNode

from sup.k8s.k8s import KubectlCmd


class RunDetail(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Show Run List")]

    run_details = Reactive(dict())

    def __init__(self, run: str, namespace: str):
        super().__init__()
        self.run = run
        self.selected_stage = dict()
        self.stage_detail: str = "Select a stage to view the details"
        # noinspection PyTypeChecker
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
                        yield MarkdownViewer(
                            markdown=self.stage_detail,
                            show_table_of_contents=False,
                            id="markdownStageDetail",
                        )
                    with TabPane("Logs", id="logsTab"):
                        pass
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(self.refresh_time_in_sec, self.update_run_details)
        self.update_run_details()

    def on_tree_node_selected(self, widget) -> None:
        if widget.node.data:
            self.selected_stage = widget.node
            self.populate_stage_details()

    def populate_stage_details(self):
        # noinspection PyBroadException,PyTypeChecker
        mkd: MarkdownViewer = self.query_one("#markdownStageDetail")
        try:
            if self.selected_stage:
                path = os.path.dirname(os.path.abspath(__file__)).replace(
                    "/screens", f"/templates/stage_detail.md"
                )
                tpl = open(path, "r").read()
                stage = self.selected_stage.data.get("run_spec_stage")
                spec = self.selected_stage.data.get("status_stage")
                # noinspection PyTypeChecker
                markdown: MarkdownViewer = self.query_one("#markdownStageDetail")
                markdown.show_table_of_contents = True
                markdown.show_vertical_scrollbar = True
                markdown.show_horizontal_scrollbar = False
                final_data = (
                    str(tpl)
                    .replace("%component_name", stage.get("componentRef").get("name"))
                    .replace("%namespace", stage.get("componentRef").get("namespace"))
                    .replace(
                        "%outputs",
                        yaml.dump(stage.get("outputs", "No Outputs to report")),
                    )
                    .replace(
                        "%pipelinerun_name",
                        spec.get("pipelineRun").get("ref").get("name")
                        if spec.get("pipelineRun")
                        else "PipelineRun not created",
                    )
                    .replace(
                        "%pipelinerun_ns",
                        spec.get("pipelineRun").get("ref").get("namespace")
                        if spec.get("pipelineRun")
                        else "PipelineRun not created",
                    )
                    .replace(
                        "%pipeline_passed",
                        str(stage.get("pipeline").get("passed", "Did not run"))
                        if stage.get("pipeline")
                        and stage.get("pipeline").get("passed") is not None
                        else "Stage did not run/finish",
                    )
                    .replace(
                        "%pipeline_start",
                        stage.get("pipeline").get("started", "Did not run")
                        if stage.get("pipeline")
                        and stage.get("pipeline").get("started")
                        else "Stage did not run/finish",
                    )
                    .replace(
                        "%pipeline_end",
                        stage.get("pipeline").get("completed", "Did not run")
                        if stage.get("pipeline")
                        and stage.get("pipeline").get("completed")
                        else "Stage did not run/finish",
                    )
                    .replace(
                        "%pipeline_results",
                        yaml.dump(
                            stage.get("pipeline").get("results", "No Results to Show")
                        )
                        if stage.get("pipeline")
                        and stage.get("pipeline").get("passed") is not None
                        else "No Results to show",
                    )
                    .replace(
                        "%pipeline_message",
                        stage.get("pipeline").get("message", "Did not run")
                        if stage.get("pipeline")
                        and stage.get("pipeline").get("message")
                        else "Stage did not run/finish",
                    )
                )

                if stage.get("resumptions"):
                    for r in stage.get("resumptions"):
                        tpl_r = f"""
#### {r.get("name") if r.get("name") != "" else "R1"}
##### Overview
```yaml
key: {r.get("key")} 
message: {r.get("message")}                        
```
##### Status
```yaml
Passed: {r.get("passed", "Stage did not run/finish")}
Start: {r.get("started", "Stage did not run/finish")}
Completed: {r.get("completed", "Stage did not run/finish")}
```
##### Results
```yaml
resultDigest: {r.get("resultDigest", "Stage did not run/finish")}
results:
{yaml.dump(r.get("results", "No Results to Show")) if r.get("results") and r.get("passed") is not None else "No Results to show"}
```
                        """
                        final_data = final_data.replace("%resumptions", tpl_r)
                else:
                    final_data = final_data.replace(
                        "%resumptions", "This stage does not have any resumptions"
                    )
                self.stage_detail = final_data
                mkd.document.update(self.stage_detail)
                mkd.document.refresh(layout=True, recompose=True)

        except Exception as err:
            self.notify(
                f"Sup was unable to get Stage details from the cluster. Error {err}",
                title="Refresh Error",
                severity="error",
                timeout=self.refresh_time_in_sec,
            )

    def populate_stage_tree(self):
        # noinspection PyTypeChecker
        tree: Tree = self.query_one("#stagesTree")
        tree.clear()
        stages_node = tree.root
        stages_node.expand()
        ct = 0
        for stage in (
            self.run_details.get("status").get("workloadRun").get("spec").get("stages")
        ):
            if not stage.get("pipeline"):
                ej = emoji.emojize(":white_circle: ")
                spec = {}
            elif stage.get("pipeline").get("started") and not stage.get("pipeline").get(
                "completed"
            ):
                ej = emoji.emojize(":blue_circle: ")
                spec = self.run_details.get("status").get("stages", [])[ct]
            elif (
                stage.get("pipeline").get("passed")
                and stage.get("pipeline").get("passed") is True
            ):
                ej = emoji.emojize(":green_circle: ")
                spec = self.run_details.get("status").get("stages", [])[ct]
            else:
                ej = emoji.emojize(":red_circle: ")
                spec = self.run_details.get("status").get("stages", [])[ct]

            stages_node.add_leaf(
                ej + stage.get("name"),
                {
                    "run_spec_stage": stage,
                    "status_stage": spec,
                },
            )
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
        self.populate_top_bar()
        self.populate_stage_tree()
        if self.selected_stage:
            self.populate_stage_details()
