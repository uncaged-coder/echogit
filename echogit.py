import os
import subprocess
import argparse
from echogit.config import Config
from echogit.tui import run_ui
from echogit.node_factory import NodeFactory
from echogit.version import Version
from echogit.sync_node_config import SyncNodeConfig


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Echogit CLI")
    subparsers = parser.add_subparsers(dest="command")

    # sync command
    sync_parser = subparsers.add_parser("sync", help="Synchronize projects")
    sync_parser.add_argument("folder", nargs="?", default=None,
                             help="Folder to sync")
    sync_parser.add_argument("-i", "--ignore-peer-down", action="store_true",
                             help="Ignore if peer is down")
    sync_parser.add_argument("-v", "--verbose", action="store_true",
                             help="Verbose output")
    sync_parser.add_argument("-p", "--peer", default=None,
                             help="Specify a peer to sync with")

    # clone command
    clone_parser = subparsers.add_parser("clone", help="Clone a project")
    clone_parser.add_argument("folder", help="Folder to clone")
    clone_parser.add_argument("-p", "--peer", default=None,
                              help="Specify a peer to clone from")

    # config command
    subparsers.add_parser("config", help="Show configuration")

    # list command
    list_parser = subparsers.add_parser("list", help="List projects")
    list_parser.add_argument(
        "folder", nargs="?", default=None, help="Folder to list")
    list_parser.add_argument(
        "--remote", action="store_true", help="List remote projects")
    list_parser.add_argument("-p", "--peer", default=None,
                             help="Specify a peer for remote listing")
    list_parser.add_argument(
        "-c", "--cached", action="store_true", help="Use cached data")

    # tui command
    subparsers.add_parser("tui", help="Launch TUI interface")

    # version command
    list_parser = subparsers.add_parser("version", help="Print version")
    list_parser.add_argument("-p", "--peer", default=None,
                             help="Specify a peer for remote listing")
    list_parser.add_argument(
        "-c", "--cached", action="store_true", help="Use cached data")

    # peers command
    peers_parser = subparsers.add_parser("peers", help="List available peers")
    peers_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output")

    # Parse command-line arguments
    args = parser.parse_args()

    if args.command == "config":
        handle_config_command()
    elif args.command == "version":
        handle_version_command(args.peer, args.cached)
    elif args.command == "sync":
        config = Config.get_local_instance()
        folder = args.folder or config.projects_path
        handle_sync_command(folder, args.verbose, args.ignore_peer_down)
    elif args.command == "clone":
        folder = args.folder
        handle_clone_command(folder, args.peer)
    elif args.command == "tui":
        run_ui()
    elif args.command == "list":
        config = Config.get_local_instance()
        folder = args.folder or config.git_path or config.projects_path
        handle_list_command(folder, args.remote, args.peer, args.cached)
    elif args.command == "peers":
        handle_peers_command(args.verbose)
    else:
        print("Unknown command")
        print_usage()


def print_usage():
    print("Usage: echogit <command> [options]")
    print("Commands:")
    print("  sync           - Synchronize projects")
    print("  clone          - Clone a project")
    print("  config         - Show configuration")
    print("  list           - List projects (local or remote)")
    print("  peers          - List available peers")
    print("  version        - Print version")


def handle_config_command():
    config = Config.get_local_instance()
    print(f"Data Path: {config.projects_path}")
    print(f"Git Path: {config.git_path}")


def handle_version_command(peer_str, cached):
    config = Config.get_local_instance()
    if peer_str is None:
        version = Version.full_version()
    elif peer_str in config.get_peers():
        peer = config.get_peer(peer_str)
        version = peer.get_version()
    else:
        print(f"invalid peer {peer_str}")
        return
    print(version)


def _get_root_node(folder):
    node = NodeFactory.from_folder(folder)
    node.scan()
    return node


def handle_sync_command(folder, verbose, ignore_peer_down):
    node = _get_root_node(folder)
    print(f"Syncing {node.name}...")
    success, total = node.sync(
        verbose=verbose, ignore_peer_down=ignore_peer_down)
    print(f"done on {success}/{total}...")


def _clone_project(folder, peers):
    for peer in peers:
        remote_url = peer.get_remote_project_url(folder)

        if peer.is_down:
            print(f"Skipping peer {peer.name}: peer is down")
            continue

        print(f"Attempting to clone from peer {peer.name} / {remote_url}")
        command = ["git", "clone", "--origin", peer.name, remote_url, folder]

        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=True)
            if result.returncode == 0:
                print(f"Successfully cloned {folder} from {peer.name}")
                return  True
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone from peer {peer.name}: {e.stderr}")

    return False

def handle_clone_command(folder, peer):
    config = Config.get_local_instance()
    peers = [config.get_peer(peer)] if peer else config.get_peers().values()

    # Check if the folder already exists
    if os.path.exists(folder):
        raise FileExistsError(f"Cannot clone into existing folder: {folder}")

    if _clone_project(folder,peers):
        SyncNodeConfig.create_default_config(folder, SyncNodeConfig.SYNC_TYPE_GIT)
    else:
        print(f"Error: Could not clone {folder} from any peer")


def handle_list_command(folder, remote, peer, cached):
    config = Config.get_local_instance()
    node = _get_root_node(folder)
    node.scan()
    ours = node.get_children_tree_by_path()
    print(f"Local projects: {ours}")

    if not remote:
        return

    available = {}
    peers = [config.get_peer(peer)] if peer else config.get_peers().values()

    for p in peers:
        remote_projects = list_remote_projects(p, cached)
        filtered = {pth: name for pth,
                    name in remote_projects.items() if pth not in ours}
        available.update(filtered)

    print(f"Available remote projects: {available}")


def list_remote_projects(peer, cached):
    if peer.is_localhost():
        return {}
    return peer.get_remote_projects(cached)


def handle_peers_command(verbose):
    config = Config.get_local_instance()
    path = os.path.abspath(os.path.expanduser(config.projects_path))
    node = NodeFactory.from_folder(path)
    for _, peer in node.config.get_peers().items():
        status = ": is down" if peer.is_down else ""
        print(f"{peer.name}{status}")


if __name__ == "__main__":
    main()
