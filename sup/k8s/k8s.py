import json
import subprocess


class KubectlCmd:
    @staticmethod
    def run(cmd):
        process = subprocess.Popen(
            "kubectl " + cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = process.communicate()
        process.wait()
        return process, out, err

    @staticmethod
    def stern_run(cmd):
        process = subprocess.Popen(
            "stern" + cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = process.communicate()
        process.wait()
        return process, out, err

    @staticmethod
    def get_run_list():
        _, out, _ = KubectlCmd.run("get all-runs -A -ojson")
        return json.loads(out).get("items")

    @staticmethod
    def get_run_detail(run: str, namespace: str):
        _, out, _ = KubectlCmd.run(f"get {run} -n {namespace} -ojson")
        return json.loads(out)

    @staticmethod
    def get_stern_logs(stage_obj):
        cmd = (
            """ "" -c ".*" -A -l supply-chain.apps.tanzu.vmware.com/stage-object-name="""
            + stage_obj
            + """ --container-state="all" --since=2000h --timestamps=short --color="auto" --no-follow --only-log-lines --template '{{.Message}} {{"\\n"}}' | sort"""
        )
        # Add [{{color .PodColor .PodName}}] after message to add stage
        _, out, _ = KubectlCmd.stern_run(cmd)
        return out.decode(), cmd
