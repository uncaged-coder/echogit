import os
import configparser
from base_config import BaseConfig

class Config(BaseConfig):
    def __init__(self, config_path=None):
        """
        Initialize the configuration.

        @param config_path: Optional path to the configuration file. If not provided,
                            it defaults to ~/.config/echogit/config.
        """
        self.config_file = config_path if config_path else os.path.expanduser('~/.config/echogit/config.ini')
        super().__init__(self.config_file)
        self.config = configparser.ConfigParser()
        self.read_config()

    def read_config(self):
        """
        Read the configuration file and load the settings.
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file not found at {self.config_file}")

        self.config.read(self.config_file)
        self.data_path = self.config.get('DEFAULT', 'data_path', fallback='~/data/')
        self.git_path = self.config.get('DEFAULT', 'git_path', fallback='~/git/')

        # Expand user home directory symbol (~)
        self.data_path = os.path.expanduser(self.data_path)
        self.git_path = os.path.expanduser(self.git_path)

if __name__ == "__main__":
    config = Config()
    print(f"Data Path: {config.data_path}")
    print(f"Git Path: {config.git_path}")
