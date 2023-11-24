import os
import sys
import subprocess
import configparser
from config import Config
from lxc_project import LXCProject

class Projects(LXCProject):
    def __init__(self, config):
        """
        Initialize the Projects class with the configuration.

        @param config: An instance of the Config class with loaded configuration.
        """
        super().__init__(config)
        self.config = config
        self.data_path = config.data_path
        self.git_path = config.git_path

    def _walk_git_projects(self, path, callback, parent_path=""):
        """
        Recursively walk through git projects in a given path and apply a callback.

        @param path: Path to search for git projects.
        @param callback: A function to call for each git project found.
        @param parent_path: Path of the parent directory for relative path construction.
        """
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                if self._is_echogit_repository(full_path):
                    callback(os.path.join(parent_path, item))
                else:
                    # Continue searching in subdirectories
                    self._walk_git_projects(full_path, callback, parent_path=item)

    def list_projects(self):
        """
        List all projects. If a directory is not a git repo,
        explore its subdirectories for git projects.
        """
        print("Projects:")
        self._walk_git_projects(self.data_path, self._print_project)

    def _print_project(self, project_name):
        """
        Print the project name.

        @param project_name: Name of the project.
        """
        print(project_name)

    def _is_git_repository(self, path):
        """
        Check if a given path is a git repository.

        @param path: Path to check.
        @return: True if the path is a git repository, False otherwise.
        """
        git_dir = os.path.join(path, ".git")
        return os.path.exists(git_dir)

    def _is_echogit_repository(self, path):
        """
        Check if a given path is an echogit repository.

        @param path: Path to check.
        @return: True if the path is an echogit repository, False otherwise.
        """
        if not self._is_git_repository(path):
            return False
        echogit_dir = os.path.join(path, ".echogit")
        return os.path.exists(echogit_dir)

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
        """
        Add a new project.

        @param project_name: Name of the project to add.
        @param use_lfs: Boolean indicating whether to use Git LFS for this project.
        @param additional_repo: Tuple (remote_name, remote_url) for an additional git repository.
        """
        git_repo_path = os.path.join(self.git_path.rstrip('/'), f"{project_name}.git")
        data_repo_path = os.path.join(self.data_path, project_name)

        if os.path.exists(data_repo_path):
            print(f"Folder '{project_name}' already exists.")
            return

        if not self._can_create_echogit_repository(data_repo_path):
            print(f"Cannot create project here: '{data_repo_path}'.")
            return

        # Check if the git repo already exists
        if os.path.exists(git_repo_path):
            user_input = input(f"Git repository '{git_repo_path}' already exists. Use it? [Y/n] ").strip().lower()
            if user_input != 'y' and user_input != '':
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

        # Create .echogit folder and config.ini file
        echogit_path = os.path.join(data_repo_path, ".echogit")
        os.makedirs(echogit_path, exist_ok=True)
        self._create_echogit_config(echogit_path)

        print(f"Project '{project_name}' added.")

    def _create_echogit_config(self, echogit_path):
        """
        Create the config.ini file in the .echogit folder.

        @param echogit_path: Path to the .echogit folder.
        """
        config = configparser.ConfigParser()
        config['BRANCHES'] = {
            'sync_branches': ['master, dev, echogit-master, echogit-dev'],
            'upstream': 'upstream'
        }

        config_path = os.path.join(echogit_path, 'config.ini')
        with open(config_path, 'w') as configfile:
            config.write(configfile)

    def sync_project(self, project_name):
        """
        Sync a project.

        @param project_name: Name of the project to sync.
        """
        project_path = os.path.join(self.data_path, project_name)
        if not os.path.exists(project_path):
            print(f"Project '{project_name}' does not exist.")
            return

        # Sync logic here. Placeholder for actual sync functionality.
        print(
            f"Syncing project '{project_name}' ... [Placeholder]"
        )

        # if using LXC, update path sharing if needed
        self.updateLXC(project_name)

    def sync_projects(self):
        """
        Sync all projects.
        """
        self._walk_git_projects(self.data_path, self.sync_project)

    def _initialize_git_lfs(self, project_path):
        """
        Initialize Git LFS for a project.

        @param project_path: Path to the project.
        """
        subprocess.run(["git", "lfs", "install"], cwd=project_path)
        subprocess.run(["git", "lfs", "track", "*"], cwd=project_path)
        print(f"Git LFS initialized for project at '{project_path}'.")

    def _parse_containers_from_config(self, containers_string):
        """
        Parse the containers string from config.

        @param containers_string: The containers string in the config.
        @return: List of container names.
        """
        return [container.strip() for container in containers_string.strip('[]').split(',') if container]

    @staticmethod
    def parse_project_arguments(argv):
        """
        Parse the command line arguments for project commands.

        @param argv: List of command line arguments.
        @return: Tuple containing command, project_name, use_lfs, and additional_repo.
        """
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
        """
        Execute a given command on the project.

        @param command: The command to execute.
        @param project_name: The name of the project.
        @param use_lfs: Boolean indicating whether to use Git LFS.
        @param additional_repo: Additional repository details (tuple of remote name and URL).
        """
        if command == "list":
            self.list_projects()
        elif command == "add" and project_name:
            self.add_project(project_name, use_lfs, additional_repo)
        elif command == "sync" and project_name:
            print("sync pn cmd")
            self.sync_project(project_name)
        elif command == "sync":
            print("sync cmd")
            self.sync_projects(project_name)
        else:
            print("Invalid command or missing project name.")


if __name__ == "__main__":
    config = Config()
    projects = Projects(config)

    command, project_name, use_lfs, additional_repo = Projects.parse_project_arguments(sys.argv)
    projects.execute_command(command, project_name, use_lfs, additional_repo)
