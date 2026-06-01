# Rachotil

Rachotil is a simple Python TUI app (using Textual) for SSH server and homelab management from one place.

You can use it for:

- SSH terminal access
- live server stats with custom blocks
- settings and `.env` management in app
- management actions for systemd, journalctl, processes, and APT and other services tracking
- docker managment
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
  - config stored in `stats_config.json`
- **Settings screen**
  - save SSH host/user/password
  - save optional sudo password
  - values are stored in `.env`
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
  - interactive managment
- **file manager screen**
  - browsing
  - copying, deleting, creating files
  - remotly management
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

## Install

Pick any folder where you want the project.

```bash
git clone https://github.com/Chillosh/rachotil.git
cd rachotil
python -m pip install .
rachotil
```

If `rachotil` command is not found, run:

```bash
python -m rachotil.main
```

---

## Install on Windows / Linux / macOS

### Windows (PowerShell)

```powershell
git clone https://github.com/Chillosh/rachotil.git
cd rachotil
py -3 -m pip install .
rachotil
```

### Linux

```bash
git clone https://github.com/Chillosh/rachotil.git
cd rachotil
python3 -m pip install .
rachotil
```

### macOS

```bash
git clone https://github.com/Chillosh/rachotil.git
cd rachotil
python3 -m pip install .
rachotil
```

I haven't actually tested it on Linux and macOS, but it should work fine

---

## Remote server requirements (important)
Currently works only on Debian based servers (mainly because of APT)

### Setup on server-side
```git clone https://github.com/Chillosh/rachotil.git
cd rachotil
./install.sh
```
Follow the setup as guided in install.sh and then you should be able to to connect through client




---

## Configuration (`.env`)

Rachotil reads and writes `.env` in the project root.

```env
SSH_HOST=192.168.1.10
SSH_USER=root
SSH_PASSWORD=your_ssh_password
SSH_SUDO_PASSWORD=your_sudo_password
```

Notes:

- `SSH_SUDO_PASSWORD` is optional.
- If missing, Rachotil uses `SSH_PASSWORD` for sudo.
- You can set these values from `Settings` in the app.

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
6. `Settings`

---

## Troubleshooting

- **SSH connection fails**
  - verify host, user, password in `Settings`
  - test manually with `ssh user@host`
- **APT/systemctl commands fail**
  - verify user has sudo rights
  - verify `SSH_SUDO_PASSWORD`
  - verify remote server is Linux with systemd and apt
- **No stats output**
  - check enabled blocks in `Settings -> Stats Configuration`
  - check command validity in `stats_config.json`

---

## Project structure

- Backend - logic
-   Components - store each component, that is then utilized in screens
-   Storage - store json files
- Frontend - textual ui for screens
-   Components - components then utilized in screens (e.g. manu.py)
-   Screens - displayed each component
-   App.py - screen switcher

---

## License

MIT (`LICENSE`).
