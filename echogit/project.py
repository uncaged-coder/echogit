import os
import subprocess
from project_config import ProjectConfig


class Project:
    def __init__(self, full_local_path, project_path, is_echogit=False, is_git=False):
        self.full_local_path = full_local_path
        self.project_path = project_path
        self.is_echogit = is_echogit
        self.is_git = is_git
        self.is_folder = os.path.isdir(full_local_path) and not is_echogit and not is_git
        self.has_echogit_child = False
        self.children = []
        self.dirty = False
        self.push_error = False
        self.pull_error = False
        self.missing_echogit_error = False
        self.sync_results = {}
        self._logs = ""

    def get_logs(self):
        return self._logs

    def add_child(self, child):
        self.children.append(child)

    def get_name(self):
        return os.path.basename(self.full_local_path)

    def has_error(self):
        return self.push_error or self.pull_error or self.missing_echogit_error

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
            if self.missing_echogit_error:
                status_parts.append("EGIT_MISS")
        return f"[{','.join(status_parts)}]"

    def _add_logs_header(self, project_name, project_path, branch, peer):
        self._logs += f"project={project_name} path={project_path} branch={branch} peer={peer}\n"

    def _add_logs_footer(self):
        self._logs += "------------------------------------------------\n"

    def _sync_project_git_branch(self, project_name, peer, branch):
        remote_name = peer.name
        remote_path = os.path.join(peer.git_path, self.project_path + ".git")
        subprocess.run(["git", "remote", "add", remote_name, remote_path], cwd=self.full_local_path, stderr=subprocess.PIPE)

        push_result = subprocess.run(["git", "push", remote_name, branch], cwd=self.full_local_path, text=True, capture_output=True)
        pull_result = subprocess.run(["git", "pull", remote_name, branch], cwd=self.full_local_path, text=True, capture_output=True)

        status_result = subprocess.run(["git", "status", "--porcelain"], cwd=self.full_local_path, text=True, capture_output=True)
        dirty = bool(status_result.stdout)

        self._add_logs_header(project_name, self.project_path, branch, peer)
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

    def _sync_echogit_git_project(self, peers):
        project_branches_results = {}
        for peer in peers:
            for branch in self.project_config.sync_branches:
                result = self._sync_project_git_branch(self.get_name(), peer, branch)
                project_branches_results[branch] = result
        return project_branches_results

    def _sync_project_rsync(self, peer):
        # Implement rsync synchronization logic here
        remote_path = os.path.join(peer.rsync_path, self.project_path)
        # Add a trailing slash to the source path to avoid creating an extra directory level
        source_path = os.path.join(self.full_local_path, '')

        rsync_command = ["rsync", "-avz", source_path, remote_path]

        rsync_result = subprocess.run(rsync_command, text=True, capture_output=True)

        self._add_logs_header(self.get_name(), self.full_local_path, "", peer)
        self._logs += f"rsync: returncode={rsync_result.returncode}\n"
        self._logs += "=============================\n"
        self._logs += rsync_result.stderr
        self._add_logs_footer()

        return {
            'rsync': {
                'code': rsync_result.returncode,
                'output': rsync_result.stderr
            }
        }

    def _sync_echogit_rsync_project(self, peers):
        project_results = {}
        for peer in peers:
            result = self._sync_project_rsync(peer)
            project_results[peer.name] = result
        return project_results

    def sync_echogit_project(self, peers):
        project_name = os.path.basename(self.full_local_path)

        try:
            self.project_config = ProjectConfig(self.full_local_path)
        except Exception as e:
            self._add_logs_header(project_name, self.full_local_path, "", "")
            self._logs += f"Error with project config: {e}\n"
            self._add_logs_footer()
            print(self.get_logs())
            return {'config_error': True}

        project_results = {}
        dirty = False
        push_error = False
        pull_error = False
        peer_error = ""

        for remote in self.project_config.sync_remotes:
            peer = peers.get_peer(remote)
            if not peer:
                peer_error += remote
                self._add_logs_header(project_name, self.full_local_path, "", peer)
                self._logs += f"No such peer\n"
                self._add_logs_footer()
                print(self.get_logs())
                continue

            if self.project_config.sync_type == ProjectConfig.SYNC_TYPE_GIT:
                project_results[remote] = self._sync_echogit_git_project([peer])
                if any(result['dirty'] for result in project_results[remote].values()):
                    dirty = True
                if any(result['push']['code'] != 0 for result in project_results[remote].values()):
                    push_error = True
                if any(result['pull']['code'] != 0 for result in project_results[remote].values()):
                    pull_error = True
            elif self.project_config.sync_type == ProjectConfig.SYNC_TYPE_RSYNC:
                project_results[remote] = self._sync_echogit_rsync_project([peer])
        return {
            'dirty': dirty,
            'push_error': push_error,
            'pull_error': pull_error,
            'peer_error': peer_error,
            'config_error': False,
            'results': project_results
        }

    def sync(self, projects, peers):
        print(f"sync {self.get_name()}")
        if self.is_echogit:
            results = self.sync_echogit_project(peers)
            if results:
                self.dirty = results.get('dirty', False)
                self.push_error = results.get('push_error', True)
                self.pull_error = results.get('pull_error', True)
                self.sync_results = results.get('results', {})
        elif self.is_git:
            self.missing_echogit_error = True
        for child in self.children:
            child.sync(projects, peers)
            self.dirty |= child.dirty
            self.push_error |= child.push_error
            self.pull_error |= child.pull_error

    def print_status(self, indent=""):
        status_msg = "ERROR" if self.has_error() else "OK"
        print(f"{indent}{self.get_name()} - Status: {status_msg}, Dirty: {self.dirty}")
        if self.has_error() and self.is_echogit:
            for remote, branches in self.sync_results.items():
                print(f"remote={remote} branches={branches}")
                for branch, result in branches.items():
                    print(f"{indent}  {remote}/{branch} - Push: {result['push']['output']}, Pull: {result['pull']['output']}")
        for child in self.children:
            child.print_status(indent + "  ")
