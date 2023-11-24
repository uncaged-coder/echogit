import sys
from config import Config
from projects import Projects
from peers import Peers

def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    config = Config()
    projects = Projects(config)

    command = sys.argv[1]

    if command == "config":
        handle_config_command(config)
    elif command == "projects":
        handle_projects_command(projects, sys.argv[1:])
    elif command == "sync":
        handle_sync_command()
    elif command == "peers":
        peers_instance = Peers(config)
        handle_peers_command(peers_instance, sys.argv[1:])
    else:
        print(f"Unknown command: {command}")
        print_usage()

def print_usage():
    print("Usage: echogit <command> [options]")
    print("Commands:")
    print("  sync     - Synchronize")
    print("  config   - Show configuration")
    print("  projects - Manage projects")
    print("  peers    - Manage peers")

def handle_config_command(config):
    print(f"Data Path: {config.data_path}")
    print(f"Git Path: {config.git_path}")

def handle_sync_command():
    config = Config()
    projects = Projects(config)
    print("Sync...")
    projects.sync_projects()

def handle_peers_command(peers, argv):
    command, peer_name, priority = Peers.parse_peer_arguments(argv)
    peers.execute_command(command, peer_name, priority)

def handle_projects_command(projects, argv):
    command, project_name, use_lfs, additional_repo = Projects.parse_project_arguments(argv)
    projects.execute_command(command, project_name, use_lfs, additional_repo)

if __name__ == "__main__":
    main()
