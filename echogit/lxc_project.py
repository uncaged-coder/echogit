import subprocess
import os
from project_config import ProjectConfig


class LXCProject:
    def __init__(self, config):
        self.config = config
        self.data_path = config.data_path

    def _is_device_added_to_container(self, container, device_name):
        """
        Check if a device is already added to an LXC container.

        @param container: Name of the LXC container.
        @param device_name: Name of the device to check.
        @return: True if the device is added, False otherwise.
        """
        try:
            result = subprocess.run(["lxc", "config", "device", "show", container],
                                    capture_output=True, text=True, check=True)
            return device_name in result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error checking device in container: {e}")
            return False  # Assuming not added if there's an error

    def _add_project_to_container(self, container, project_path):
        """
        Add project path to an LXC container.

        @param container: Name of the LXC container.
        @param project_path: Path of the project to add.
        """
        # Create a unique device name by replacing '/' with '_'
        device_name = project_path.replace('/', '_').strip('_')
        if not self._is_device_added_to_container(container, device_name):
            try:
                subprocess.run(["lxc", "config", "device", "add", container, device_name, 
                                "disk", f"source={project_path}", f"path={project_path}"],
                               check=True)
                print(f"Added project '{project_path}' to container '{container}'.")
            except subprocess.CalledProcessError as e:
                print(f"Error adding project to container: {e}")
        else:
            print(f"Project '{project_path}' is already added to container '{container}'.")

    def _remove_project_from_container(self, container, project_path):
        """
        Remove project path from an LXC container.

        @param container: Name of the LXC container.
        @param project_path: Path of the project to remove.
        """
        device_name = project_path.replace('/', '_').strip('_')
        if self._is_device_added_to_container(container, device_name):
            try:
                subprocess.run(["lxc", "config", "device", "remove", container, device_name],
                               check=True)
                print(f"Removed project '{project_path}' from container '{container}'.")
            except subprocess.CalledProcessError as e:
                print(f"Error removing project from container: {e}")
        else:
            print(f"Project '{project_path}' is not present in container '{container}'.")

    def updateLXC(self, project_name):
        global_containers = self.config.get_list('LXC', 'containers', fallback=[])
        print(global_containers)

        project_path = os.path.join(self.data_path, project_name)
        if os.path.isdir(project_path):
            project_config = ProjectConfig(project_path)
            self._update_containers_for_project(project_path, project_config, global_containers)

    def _update_containers_for_project(self, project_path, project_config, global_containers):
        """
        Add or remove project path from LXC containers based on project configuration.

        @param project_config: ProjectConfig instance for the project.
        @param global_containers: List of container names allowed globally.
        """
        project_containers = project_config.lxc_containers

        # Add project path to specified containers
        for container in project_containers:
            if container in global_containers:
                self._add_project_to_container(container, project_path)
            else:
                print(f"Container '{container}' is not listed in global configuration and will be ignored.")

        # Remove project path from containers not specified in project configuration
        for container in global_containers:
            if container not in project_containers:
                self._remove_project_from_container(container, project_path)
