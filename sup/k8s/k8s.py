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
    def get_run_list():
        _, out, _ = KubectlCmd.run("get all-runs -A -ojson")
        return json.loads(out).get("items")

    @staticmethod
    def get_run_detail(run: str, namespace: str):
        _, out, _ = KubectlCmd.run(f"get {run} -n {namespace} -ojson")
        return json.loads(out)
