# echogit: Localized Data Synchronization via Git

**Warning:** this is a work in progress work.

## Description:

<img align="left" width="100" height="100" src="docs/icon.png">

Echogit is an open-source tool designed for synchronization of data across multiple devices without the need for an internet connection. Utilizing the robustness of git and the security of SSH, it offers a decentralized approach to manage and sync various types of data.
<br>
<br>

## Core Features:

- Local Synchronization: Synchronize data across your devices using your local network, reducing reliance on cloud services.
- Git-Based: Leverages git's version control capabilities for efficient and reliable data tracking.
- SSH Security: Employs SSH for secure data transfer, ensuring your information remains private and secure.

## Targeted users:

Tech-savvy individuals who prefer local data management, are comfortable with git and SSH.

## Requirements

Echogit uses SSH and Git to synchronize projects between peers. To sync, you need to ensure that:

1. You have set up SSH key authentication between your local machine and each peer. This avoids the need for password entry during synchronization.

You can copy your SSH public key to a peer by running:
   ```bash
   ssh-copy-id user@peer_host
   ```

## Usage

### Synchronizing Projects


Use the following command to sync a folder:

```bash
echogit sync [folder]
```

### Listing Projects

```bash
echogit list [folder] --remote -p peer_name
```

### Running in TUI Mode

```bash
echogit tui
```

## Android support

There is an Android version called echogit-mobile. It provides a UI to control the normal Echogit application through Termux and the Termux API. This allows you to manage synchronization on Android devices, using the same functionality available on the desktop version.

## Tests

Run the test with:

```bash
> pytest
```
