# Rachotil

Rachotil is a Python TUI app (using Textual) for SSH server and homelab management from one place. It uses a client-server architecture where the client runs locally on your machine and controls the remote server via SSH.

You can use it for:

- SSH terminal access
- live server stats with custom blocks
- settings and credentials management in app
- management actions for systemd, journalctl, processes, APT and service tracking
- docker management including docker-compose deployments
- file managing
- firewall settings
- backup and snapshot
- track services and network

---

## What works now

- **SSH screen**
  - interactive remote shell
- **Stats screen**
  - enable/disable stat blocks
  - add/delete custom stat blocks
  - config stored locally in `stats_config.json`
- **Settings screen**
  - save SSH host/user/password
  - save optional sudo password
  - values are stored locally
- **Management screen**
  - services: list, status, enable/start, disable/stop
  - logs: quick `journalctl` actions
  - processes: top CPU, top RAM, find, kill
  - packages: `apt-get update/upgrade/install/remove`
  - custom command and custom sudo command
- **Backup and snapshot screen**
  - Selected files can be downloaded to PC
  - Stored in tar.gz
  - list of files availables
  - Snapshots are stored on server
  - Return, Create, Delete state of machine
- **Docker screen**
  - create, delete, edit containers
  - interactive management
  - direct deployment via docker-compose (YAML)
- **File manager screen**
  - browsing
  - copying, deleting, creating files
  - remote management
- **Firewall screen**
  - UFW interact
  - basic control for port forwarding etc.
- **Network screen**
  - scan for network apps installed on server
  - see state of network apps
- **Services screen**
  - lists all running services on server
  - restart, end, start

---

## Installation

Rachotil requires setup on both your remote server and your local client machine.

### 1. Server-side Setup (Required)
Currently works only on Debian/Ubuntu based servers (mainly because of APT and specific package names).

SSH into your server and run:
```bash
git clone [https://github.com/Chillosh/rachotil.git](https://github.com/Chillosh/rachotil.git)
cd rachotil
chmod +x install.sh
sudo ./install.sh
```
There is possibility you will need to install openssh manually and allow port 22 : 
```bash 
sudo apt install openssh-server -y
sudo systemctl enable --now ssh
```
```bash
sudo ufw allow 22/tcp
sudo ufw reload
```

This script installs core dependencies like Docker, docker-compose-plugin, Python, UFW, Wireguard, and sets up required permissions.

### 2. Client-side Setup (Windows)
For Windows users, there is no need to install Python. 

1. Go to the **Releases** tab on GitHub.
2. Download the `Rachotil-vX.X-Windows.zip` file.
3. Extract the ZIP to any folder.
4. Run `rachotil.exe` from your terminal or by double-clicking it.

*Note: Because the .exe is compiled via PyInstaller without a commercial certificate, Windows SmartScreen or Defender might block it at first launch. Click "More info" and "Run anyway". This is a false positive.*

### 2. Client-side Setup (Linux / macOS)
If you are on Linux or macOS, you can run the app from source:

```bash
git clone [https://github.com/Chillosh/rachotil.git](https://github.com/Chillosh/rachotil.git)
cd rachotil
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 src/rachotil/main.py
```

---

## Configuration

Rachotil handles configuration and credentials locally on the client side so they are never leaked to the server or Git repository. 

Sensitive data (like IP addresses and passwords) are set within the **Settings** menu in the app and stored in local JSON/env files (which are ignored by Git).

Notes:
- Sudo password is optional.
- If missing, Rachotil uses the standard SSH password for sudo operations.

---

## Basic controls

- `space` -> open main menu
- `q` -> quit app
- `tab` -> focus other menus

Menu sections:

1. `Dashboard` 
2. `Stats Monitoring`
3. `SSH Terminal`
4. `File Explorer`
5. `Management Tools`
6. `Backup Manager`
7. `Snapshot Manager`
8. `Service Manager`
9. `Firewall Manager`
10. `Docker Dashboard`
11. `Network Services`
12. `Settings`

---

## Troubleshooting

- **SSH connection fails**
  - verify host, user, password in `Settings`
  - test manually with `ssh user@host` from your PC
- **APT/systemctl commands fail**
  - verify user has sudo rights on the server
  - verify sudo password in Settings
  - verify remote server is Debian/Ubuntu with systemd and apt
- **Docker deployment fails**
  - make sure you restarted your SSH session after running `install.sh` so Docker group permissions apply
- **No stats output**
  - check enabled blocks in `Settings -> Stats Configuration`
  - check command validity in `stats_config.json`

---

## Project structure

- Backend - logic
  - Components - store each component, that is then utilized in screens
  - Storage - store json files (ignored by git if containing local data)
- Frontend - textual ui for screens
  - Components - components then utilized in screens
  - Screens - displayed each component
  - main.py - app entry point and screen switcher

---

## License

MIT (`LICENSE`).
