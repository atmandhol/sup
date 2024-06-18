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
    def get_run_list(chain: str = None, status: str = None, latest=True):
        _, out, _ = KubectlCmd.run("get all-runs -A -ojson")
        run_list = json.loads(out).get("items")
        filtered_run_list = list()
        for run in run_list:
            latest_check_passed = False
            chain_check_passed = False
            status_check_passed = False

            if not latest:
                latest_check_passed = True
            elif latest and KubectlCmd.is_latest(run, run_list):
                latest_check_passed = True

            if not chain or chain == "all":
                chain_check_passed = True
            elif KubectlCmd.belongs_to_chains(run, chain):
                chain_check_passed = True

            if not status or status == "all":
                status_check_passed = True
            elif KubectlCmd.belongs_to_statuses(run, status):
                status_check_passed = True

            if latest_check_passed and chain_check_passed and status_check_passed:
                filtered_run_list.append(run)
        return filtered_run_list

    @staticmethod
    def get_run_detail(run: str, namespace: str):
        _, out, _ = KubectlCmd.run(f"get {run} -n {namespace} -ojson")
        return json.loads(out)

    @staticmethod
    def get_sc_list():
        _, out, _ = KubectlCmd.run("get supplychains -A -ojson")
        return json.loads(out).get("items")

    @staticmethod
    def get_stern_logs_for_stage(stage_obj):
        cmd = (
            """ "" -c ".*" -A -l supply-chain.apps.tanzu.vmware.com/stage-object-name="""
            + stage_obj
            + """ --container-state="all" --since=2000h --timestamps=short --color="auto" --no-follow --only-log-lines --template '{{.Message}} {{"\\n"}}' | sort"""
        )
        # Add [{{color .PodColor .PodName}}] after message to add stage
        _, out, _ = KubectlCmd.stern_run(cmd)
        return out.decode(), cmd

    @staticmethod
    def get_stern_logs_for_resumption(resumption_obj):
        cmd = (
            """ "" -c ".*" -A -l supply-chain.apps.tanzu.vmware.com/resumption-name="""
            + resumption_obj
            + """ --container-state="all" --since=2000h --timestamps=short --color="auto" --no-follow --only-log-lines --template '{{.Message}} {{"\\n"}}' | sort"""
        )
        # Add [{{color .PodColor .PodName}}] after message to add stage
        _, out, _ = KubectlCmd.stern_run(cmd)
        return out.decode(), cmd

    @staticmethod
    def is_latest(run, run_list):
        workload = (
            run.get("metadata")
            .get("labels")
            .get("supply-chain.apps.tanzu.vmware.com/workload-name")
        )
        created_at_timestamp = run.get("metadata").get("creationTimestamp")
        for r in run_list:
            if (
                r.get("metadata")
                .get("labels")
                .get("supply-chain.apps.tanzu.vmware.com/workload-name")
                != workload
            ):
                continue
            if r.get("metadata").get("creationTimestamp") > created_at_timestamp:
                return False
        return True

    @staticmethod
    def belongs_to_chains(run, filter_chain):
        chain = (
            run.get("metadata")
            .get("labels")
            .get("supply-chain.apps.tanzu.vmware.com/workload-kind")
        )
        return chain.lower() == filter_chain.lower()

    @staticmethod
    def belongs_to_statuses(run, filter_status):
        status = run.get("status").get("conditions")[1].get("reason")
        return status.lower() == filter_status.lower()

    @staticmethod
    def delete_run(run, namespace):
        process, _, _ = KubectlCmd.run(f"delete {run} -n {namespace}")
        return process.returncode
