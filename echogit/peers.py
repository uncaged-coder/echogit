import os
import sys
import configparser
from config import Config

class Peers:
    def __init__(self, config):
        """
        Initialize the Peers class with the configuration.

        @param config: An instance of the Config class with loaded configuration.
        """
        self.git_data_path = config.git_path
        self.peers_file = os.path.join(self.git_data_path, '.echogit', 'peers.ini')
        self.config = configparser.ConfigParser()

    def list_peers(self):
        """
        List all peers.
        """
        if not os.path.exists(self.peers_file):
            print("No peers found.")
            return

        self.config.read(self.peers_file)
        if 'Peers' in self.config:
            for peer, priority in self.config['Peers'].items():
                print(f"{peer}: Priority {priority}")
        else:
            print("No peers found.")

    def add_peer(self, peer_name, priority):
        """
        Add a new peer with the specified priority.

        @param peer_name: Name of the peer to add.
        @param priority: Priority of the peer.
        """
        if not os.path.exists(self.peers_file):
            os.makedirs(os.path.dirname(self.peers_file), exist_ok=True)

        self.config.read(self.peers_file)
        if 'Peers' not in self.config:
            self.config['Peers'] = {}

        self.config['Peers'][peer_name] = str(priority)

        with open(self.peers_file, 'w') as configfile:
            self.config.write(configfile)

        print(f"Peer '{peer_name}' added with priority {priority}.")

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
        elif command == "add" and peer_name and priority:
            self.add_peer(peer_name, priority)
        else:
            print("Invalid command or missing arguments.")

if __name__ == "__main__":
    config = Config()
    peers = Peers(config)

    command, peer_name, priority = Peers.parse_peer_arguments(sys.argv)
    peers.execute_command(command, peer_name, priority)
