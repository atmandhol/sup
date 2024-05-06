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
