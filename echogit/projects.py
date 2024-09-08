import os
import sys
import subprocess
import configparser
from config import Config
from project import Project
from lxc_project import LXCProject

class Projects(LXCProject):
    def __init__(self, config, peers):
        super().__init__(config)
        self.config = config
        self.peers = peers
        self.data_path = config.data_path
        self.git_path = config.git_path
        self.tree = self._build_tree(self.data_path)

    def _build_tree(self, path):
        project_path = path[len(self.config.data_path):]
        root = Project(path, project_path)
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            project_path = full_path[len(self.config.data_path):]
            if os.path.isdir(full_path):
                if self._is_echogit_repository(full_path):
                    child = Project(full_path, project_path, is_echogit=True)
                    root.add_child(child)
                elif self._is_git_repository(full_path):
                    child = Project(full_path, project_path, is_git=True)
                    root.missing_echogit_error = True
                    root.add_child(child)
                else:
                    child = self._build_tree(full_path)
                    if child.is_echogit or any(grandchild.is_echogit for grandchild in child.children):
                        root.add_child(child)
                        root.has_echogit_child = True
                    elif child.is_git or any(grandchild.is_git for grandchild in child.children):
                        root.missing_echogit_error = True
                        root.add_child(child)
        return root

    def _is_git_repository(self, path):
        return os.path.exists(os.path.join(path, ".git"))

    def _is_echogit_repository(self, path):
        return os.path.exists(os.path.join(path, ".echogit"))

    def _initialize_git_lfs(self, project_path):
        subprocess.run(["git", "lfs", "install"], cwd=project_path)
        subprocess.run(["git", "lfs", "track", "*"], cwd=project_path)
        print(f"Git LFS initialized for project at '{project_path}'.")

    def _can_create_echogit_repository(self, path):
        """
        Check if an echogit repository can be created at the given path.

        @param path: The path to check.
        @return: True if an echogit repository can be created, False otherwise.
        """
        current_path = path
        while current_path and current_path != self.data_path:
            parent_path = os.path.dirname(current_path)
            if current_path == self.data_path.rstrip('/'):
                return True
            elif parent_path == current_path:  # Reached the root directory
                return False
            elif self._is_echogit_repository(current_path):
                return False
            current_path = parent_path
        return False

    def add_project(self, project_name, use_lfs=False, additional_repo=None):
        git_repo_path = os.path.join(self.git_path.rstrip('/'), f"{project_name}.git")
        data_repo_path = os.path.join(self.data_path, project_name)

        if os.path.exists(data_repo_path):
            print(f"Folder '{project_name}' already exists.")
            return

        if not self._can_create_echogit_repository(data_repo_path):
            print(f"Cannot create project here: '{data_repo_path}'.")
            return

        if os.path.exists(git_repo_path):
            user_input = input(f"Git repository '{git_repo_path}' already exists. Use it? [Y/n] ").strip().lower()
            if user_input not in ['y', '']:
                print("Operation cancelled.")
                return
        else:
            os.makedirs(git_repo_path, exist_ok=True)
            subprocess.run(["git", "init", "--bare"], cwd=git_repo_path)

        os.makedirs(data_repo_path, exist_ok=True)
        subprocess.run(["git", "init"], cwd=data_repo_path)
        subprocess.run(["git", "remote", "add", "origin", git_repo_path], cwd=data_repo_path)

        if use_lfs:
            self._initialize_git_lfs(data_repo_path)

        if additional_repo:
            remote_name, remote_url = additional_repo
            subprocess.run(["git", "remote", "add", remote_name, remote_url], cwd=data_repo_path)

        echogit_path = os.path.join(data_repo_path, ".echogit")
        os.makedirs(echogit_path, exist_ok=True)
        self._create_echogit_config(echogit_path)

        print(f"Project '{project_name}' added.")

    def _create_echogit_config(self, echogit_path):
        config = configparser.ConfigParser()
        config['BRANCHES'] = {
            'sync_branches': 'master, dev, echogit-master, echogit-dev',
            'upstream': 'upstream'
        }
        config['LXC'] = {
            'containers': ''
        }
        with open(os.path.join(echogit_path, 'config.ini'), 'w') as configfile:
            config.write(configfile)

    def sync_projects(self, verbose=True):
        self.tree.sync(self, self.peers)
        if verbose:
            self.tree.print_status()
        return self.tree

    @staticmethod
    def parse_project_arguments(argv):
        command = argv[1] if len(argv) > 1 else None
        project_name = argv[2] if len(argv) > 2 else None
        use_lfs = "-o" in argv and "lfs" in argv

        additional_repo = None
        if "-a" in argv:
            additional_repo_index = argv.index("-a") + 1
            if additional_repo_index < len(argv) - 1:
                additional_repo = (argv[additional_repo_index], argv[additional_repo_index + 1])

        return command, project_name, use_lfs, additional_repo

    def execute_command(self, command, project_name, use_lfs=False, additional_repo=None):
        if command == "list":
            self.tree.print_status()
        elif command == "add" and project_name:
            self.add_project(project_name, use_lfs, additional_repo)
        elif command == "sync" and project_name:
            self.sync_echogit_project(project_name, self.peers)
        elif command == "sync":
            self.sync_projects()
        else:
            print("Invalid command or missing project name.")


if __name__ == "__main__":
    config = Config()
    peers = Peers(config)

    projects = Projects(config, peers)
    command, project_name, use_lfs, additional_repo = Projects.parse_project_arguments(sys.argv)
    projects.execute_command(command, project_name, use_lfs, additional_repo)
