import os
import subprocess
from project_config import ProjectConfig

class Project:
    def __init__(self, path, is_echogit=False):
        self.path = path
        self.is_echogit = is_echogit
        # ugly but is_folder = folder but not folder that are echogit project.
        self.is_folder = os.path.isdir(path) and not is_echogit
        self.has_echogit_child = False
        self.children = []
        self.dirty = False
        self.push_error = False
        self.pull_error = False
        self.sync_results = {}
        self._logs = ""

    def get_logs(self):
        return self._logs

    def add_child(self, child):
        self.children.append(child)

    def get_name(self):
        return os.path.basename(self.path)

    def has_error(self):
        return self.push_error or self.pull_error

    def get_status(self):
        status_parts = []
        if self.dirty:
            status_parts.append("DIRTY")
        if not self.has_error():
            status_parts.append("OK")
        else:
            if self.push_error:
                status_parts.append("PUSH")
            if self.pull_error:
                status_parts.append("PULL")
        return f"[{','.join(status_parts)}]"

    def _add_logs_header(self, project_name, project_path, branch, peer):
        self._logs += f"project={project_name} path={project_path} branch={branch} peer={peer}\n"

    def _add_logs_footer(self):
        self._logs += "------------------------------------------------\n"

    def _sync_project_branch(self, project_path, project_name, peer, branch):
        remote_name = peer.name
        remote_path = os.path.join(peer.git_path, project_name)
        subprocess.run(["git", "remote", "add", remote_name, remote_path], cwd=project_path, stderr=subprocess.PIPE)

        push_result = subprocess.run(["git", "push", remote_name, branch], cwd=project_path, text=True, capture_output=True)
        pull_result = subprocess.run(["git", "pull", remote_name, branch], cwd=project_path, text=True, capture_output=True)

        status_result = subprocess.run(["git", "status", "--porcelain"], cwd=project_path, text=True, capture_output=True)
        dirty = bool(status_result.stdout)


        self._add_logs_header(project_name, project_path, branch, peer)
        self._logs += f"push: returncode={push_result.returncode}\n"
        self._logs += "=============================\n"
        self._logs += push_result.stderr
        self._logs += f"pull: returncode={pull_result.returncode}\n"
        self._logs += "=============================\n"
        self._logs += pull_result.stderr
        self._logs += f"status: returncode={status_result.returncode}\n"
        self._logs += "=============================\n"
        self._logs += status_result.stderr
        self._add_logs_footer()

        return {
            'dirty': dirty,
            'push': {
                'code': push_result.returncode,
                'output': push_result.stderr
            },
            'pull': {
                'code': pull_result.returncode,
                'output': pull_result.stderr
            }
        }


    def sync_echogit_project(self, project_path, peers):
        project_name = os.path.basename(project_path)

        try:
            project_config = ProjectConfig(project_path)
        except Exception as e:
            self._add_logs_header(project_name, project_path, "", "")
            self._logs += f"Error with project config: {e}\n"
            self._add_logs_footer()
            print(self.get_logs())
            return {'config_error': True}

        project_results = {}
        dirty = False
        push_error = False
        pull_error = False
        peer_error = ""

        for remote in project_config.sync_remotes:
            peer = peers.get_peer(remote)
            if not peer:
                peer_error += remote
                self._add_logs_header(project_name, project_path, "", peer)
                self._logs += f"No such peer\n"
                self._add_logs_footer()
                print(self.get_logs())
                continue

            project_results[remote] = {}
            for branch in project_config.sync_branches:
                result = self._sync_project_branch(project_path, project_name, peer, branch)
                project_results[remote][branch] = result
                if result['dirty']:
                    dirty = True
                if result['push']['code'] != 0:
                    push_error = True
                if result['pull']['code'] != 0:
                    pull_error = True

        return {
            'dirty': dirty,
            'push_error': push_error,
            'pull_error': pull_error,
            'peer_error': peer_error,
            'config_error': False,
            'results': project_results
        }

    def sync(self, projects, peers):
        """
        Sync this project and its children.
        """
        if self.is_echogit:
            results = self.sync_echogit_project(self.path, peers)
            if results:
                self.dirty = results.get('dirty', False)
                self.push_error = results.get('push_error', True)
                self.pull_error = results.get('pull_error', True)
                self.sync_results = results.get('results', {})
        for child in self.children:
            child.sync(projects, peers)
            self.dirty |= child.dirty
            self.push_error |= child.push_error
            self.pull_error |= child.pull_error

    def print_status(self, indent=""):
        status_msg = "ERRROR" if self.has_error() else "OK"
        print(f"{indent}{self.get_name()} - Status: {status_msg}, Dirty: {self.dirty}")
        if self.has_error() and self.is_echogit:
            for remote, branches in self.sync_results.items():
                for branch, result in branches.items():
                    print(f"{indent}  {remote}/{branch} - Push: {result['push']['output']}, Pull: {result['pull']['output']}")
        for child in self.children:
            child.print_status(indent + "  ")
