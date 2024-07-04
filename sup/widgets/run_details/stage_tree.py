import emoji

from datetime import datetime
from textual.app import ComposeResult
from textual.widgets import Static, Tree
from sup.k8s.k8s import KubectlCmd


class StageTree(Static):
    """Run list"""

    def __init__(self, run, namespace):
        super().__init__(id="side_bar")
        self.run = run
        self.namespace = namespace

    def compose(self) -> ComposeResult:
        yield Tree("Stages", id="stagesTree")

    # noinspection PyTypeChecker
    def populate(self, run_details):
        tree: Tree = self.query_one("#stagesTree")
        tree.clear()
        stages_node = tree.root
        stages_node.expand()
        ct = 0
        for run_spec_stage in (
            run_details.get("status").get("workloadRun").get("spec").get("stages")
        ):
            time_taken = ""
            if run_spec_stage.get("resumptions"):
                rct = 0
                for r in run_spec_stage.get("resumptions"):
                    if not r.get("started") and not r.get("completed"):
                        ej = emoji.emojize(":white_circle: ")
                        status_resumption = {}
                    elif r.get("started") and not r.get("completed"):
                        ej = emoji.emojize(":blue_circle: ")
                        status_resumption = (
                            run_details.get("status")
                            .get("stages", [])[ct]
                            .get("resumptions", [])[rct]
                        )
                    elif r.get("passed") and r.get("passed") is True:
                        ej = emoji.emojize(":green_circle: ")
                        status_resumption = (
                            run_details.get("status")
                            .get("stages", [])[ct]
                            .get("resumptions", [])[rct]
                        )
                    else:
                        ej = emoji.emojize(":red_circle: ")
                        status_resumption = (
                            run_details.get("status")
                            .get("stages", [])[ct]
                            .get("resumptions", [])[rct]
                        )

                    stages_node.add_leaf(
                        ej + "⏰ " + r.get("name"),
                        {
                            "run_spec_resumption": r,
                            "resumption": True,
                            "status_resumption": status_resumption,
                        },
                    )
                    rct += 1

            if not run_spec_stage.get("pipeline"):
                ej = emoji.emojize(":white_circle: ")
                status_stage = {}
            elif run_spec_stage.get("pipeline").get(
                "started"
            ) and not run_spec_stage.get("pipeline").get("completed"):
                ej = emoji.emojize(":blue_circle: ")
                status_stage = run_details.get("status").get("stages", [])[ct]
            elif (
                run_spec_stage.get("pipeline").get("passed")
                and run_spec_stage.get("pipeline").get("passed") is True
            ):
                ej = emoji.emojize(":green_circle: ")
                status_stage = run_details.get("status").get("stages", [])[ct]

                start = datetime.strptime(
                    run_spec_stage.get("pipeline").get("started"), "%Y-%m-%dT%H:%M:%SZ"
                )
                end = datetime.strptime(
                    run_spec_stage.get("pipeline").get("completed"),
                    "%Y-%m-%dT%H:%M:%SZ",
                )
                time_taken = KubectlCmd.datetime_difference_in_kubernetes_format(
                    start_time=start, end_time=end
                )

            else:
                ej = emoji.emojize(":red_circle: ")
                status_stage = run_details.get("status").get("stages", [])[ct]
                start = datetime.strptime(
                    run_spec_stage.get("pipeline").get("started"), "%Y-%m-%dT%H:%M:%SZ"
                )
                end = datetime.strptime(
                    run_spec_stage.get("pipeline").get("completed"),
                    "%Y-%m-%dT%H:%M:%SZ",
                )
                time_taken = KubectlCmd.datetime_difference_in_kubernetes_format(
                    start_time=start, end_time=end
                )

            stages_node.add_leaf(
                ej
                + run_spec_stage.get("name")
                + (f" ⌛ ({time_taken})" if time_taken else ""),
                {
                    "run_spec_stage": run_spec_stage,
                    "status_stage": status_stage,
                    "resumption": False,
                },
            )
            ct += 1
