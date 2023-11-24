import os
from base_config import BaseConfig

class ProjectConfig(BaseConfig):
    def __init__(self, project_path):
        config_file = os.path.join(project_path, '.echogit', 'config.ini')
        super().__init__(config_file)
        self.project_path = project_path
        self.sync_branches = self.get_list('BRANCHES', 'sync_branches', fallback=[])
        self.upstream = self.config.get('BRANCHES', 'upstream', fallback='upstream')
        self.lxc_containers = self.get_list('LXC', 'containers', fallback=[])

