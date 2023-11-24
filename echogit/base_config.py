import configparser
import os

class BaseConfig:
    def __init__(self, config_path):
        """
        Initialize the BaseConfig class.

        @param config_path: Path to the configuration file.
        """
        self.config_file = os.path.expanduser(config_path)
        self.config = configparser.ConfigParser()
        self.read_config()

    def read_config(self):
        """
        Read the configuration file and load the settings.
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file not found at {self.config_file}")

        self.config.read(self.config_file)

    def get_list(self, section, option, fallback=None):
        """
        Get a list from a config option.

        @param section: The config section.
        @param option: The config option.
        @param fallback: The fallback value if the option is not found.
        @return: The list of values, or the fallback.
        """
        value = self.config.get(section, option, fallback=fallback)
        if value is None or value == '':
            return fallback
        return [item.strip() for item in value.split(',')]
