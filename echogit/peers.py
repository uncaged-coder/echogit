import os
import sys
import configparser
from config import Config


class Peer:
    def __init__(self, name, priority, ip, git_path, description):
        self.name = name
        self.priority = priority
        self.ip = ip
        self.git_path = git_path
        self.description = description


class Peers:
    def __init__(self, config):
        """
        Initialize the Peers class with the configuration.

        @param config: An instance of the Config class with loaded configuration.
        """
        self.git_data_path = config.git_path
        self.peers_file = os.path.expanduser('~/.config/echogit/peers.ini')

        self.config = configparser.ConfigParser()
        self.peers = {}
        self.read_config()

    def get_peers(self):
        """ Return the dictionary of peers. """
        return self.peers

    def get_peer(self, name):
        """ Return the dictionary of peers. """
        return self.peers.get(name)

    def read_config(self):
        """
        Reads the peers configuration from the peers.ini file and stores it in the peers dictionary.
        """
        if not os.path.exists(self.peers_file):
            print("Error: peers configuration file does not exist.")
            return
        
        self.config.read(self.peers_file)
        for section in self.config.sections():
            if self.validate_peer_config(section):
                self.peers[section] = Peer(
                    name = section,
                    priority = int(self.config[section]['priority']),
                    ip = self.config[section]['ip'],
                    git_path = self.config[section]['git_path'],
                    description = self.config[section]['description']
                )
            else:
                print(f"Warning: Invalid data in section {section}")

    def validate_peer_config(self, section):
        """
        Validates the required fields for a peer configuration.

        @param section: The section name in the configuration file.
        @return: True if the configuration is valid, False otherwise.
        """
        required_fields = ['priority', 'ip', 'git_path', 'description']
        return all(field in self.config[section] for field in required_fields)

    def list_peers(self):
        """
        List all peers from the peers dictionary.
        """
        if not self.peers:
            print("No peers found.")
        else:
            print("Listing all peers:")
            for peer_name, peer in self.peers.items():
                print(f"{peer_name}: Priority {peer.priority}, IP {peer.ip}, Git Path {peer.git_path}, Description {peer.description}")


    @staticmethod
    def parse_peer_arguments(argv):
        """
        Parse the command line arguments for peer commands.

        @param argv: List of command line arguments.
        @return: Tuple containing command, peer_name, and priority.
        """
        command = argv[1] if len(argv) > 1 else None
        peer_name = argv[2] if len(argv) > 2 else None
        priority = argv[3] if len(argv) > 3 else None

        return command, peer_name, priority

    def execute_command(self, command, peer_name=None, priority=None):
        """
        Execute a given command for peers.

        @param command: The command to execute.
        @param peer_name: The name of the peer (for add command).
        @param priority: The priority of the peer (for add command).
        """
        if command == "list":
            self.list_peers()
        else:
            print("Invalid command or missing arguments.")

if __name__ == "__main__":
    config = Config()
    peers = Peers(config)

    command, peer_name, priority = Peers.parse_peer_arguments(sys.argv)
    peers.execute_command(command, peer_name, priority)
