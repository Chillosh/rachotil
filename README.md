# Rachotil

Rachotil is a simple Python TUI app (using Textual) for SSH server and homelab management from one place.

You can use it for:

- SSH terminal access
- live server stats with custom blocks
- settings and `.env` management in app
- management actions for systemd, journalctl, processes, and APT

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

## Remote server prerequisites (important)

Rachotil connects to a remote machine over SSH, so SSH must be installed and enabled on that machine.

### Ubuntu / Debian server

```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
sudo systemctl status ssh --no-pager
```

### SSH config (when root login is needed)

Edit `/etc/ssh/sshd_config` and check these options:

```text
PermitRootLogin yes
PasswordAuthentication yes
```

Then restart SSH:

```bash
sudo systemctl restart ssh
```

Friendly reminder: Yes I am retarded and I know PermitRootLogin is not secure, but it's just for a homelab server in a safe network, so yeah I should fix It in the future.

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

Menu sections:

1. `Stats`
2. `SSH`
3. `Management`
4. `Settings`

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

## Project roadmap (weekly, until June)

This is something I want to do, because of my procrastination, however I started it really late. So It this will came in the future.

---

## Project structure

- `src/rachotil/ui/` - Textual screens, components, styles
- `src/rachotil/ssh/` - SSH connection and `.env` config logic
- `src/rachotil/stats/` - stats config loading and validation
- `stats_config.json` - stats blocks configuration

---

## License

MIT (`LICENSE`).
