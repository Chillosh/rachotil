import shlex
from textual import on, work
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Log, Static
from ssh.config import get_ssh_config
from ssh.ssh import SSH


class ManagementScreen(Screen):
    CSS_PATH = "../styles.tcss"

    SECTIONS = {
        "services": {
            "title": "Systemd services",
            "target_placeholder": "Service name (example: nginx.service)",
            "extra_placeholder": "Optional argument",
            "actions": {
                "primary": {
                    "label": "List services",
                    "command": "systemctl list-units --type=service --all --no-pager",
                    "sudo": False,
                },
                "secondary": {
                    "label": "Status target",
                    "command": "systemctl status {target} --no-pager",
                    "sudo": False,
                    "requires_target": True,
                },
                "tertiary": {
                    "label": "Enable+Start",
                    "command": "systemctl enable --now {target}",
                    "sudo": True,
                    "requires_target": True,
                },
                "quaternary": {
                    "label": "Disable+Stop",
                    "command": "systemctl disable --now {target}",
                    "sudo": True,
                    "requires_target": True,
                },
            },
        },
        "journal": {
            "title": "Journalctl logs",
            "target_placeholder": "Unit name (example: nginx.service)",
            "extra_placeholder": "Lines or --since value (example: 200 or '1 hour ago')",
            "actions": {
                "primary": {
                    "label": "Last 100 logs",
                    "command": "journalctl -n 100 --no-pager",
                    "sudo": False,
                },
                "secondary": {
                    "label": "Unit logs",
                    "command": "journalctl -u {target} -n 150 --no-pager",
                    "sudo": False,
                    "requires_target": True,
                },
                "tertiary": {
                    "label": "Since value",
                    "command": "journalctl --since {extra} -n 200 --no-pager",
                    "sudo": False,
                    "requires_extra": True,
                },
                "quaternary": {
                    "label": "Vacuum by days",
                    "command": "journalctl --vacuum-time={extra}d",
                    "sudo": True,
                    "requires_extra": True,
                },
            },
        },
        "processes": {
            "title": "Process management",
            "target_placeholder": "PID or process name",
            "extra_placeholder": "Optional argument",
            "actions": {
                "primary": {
                    "label": "Top CPU",
                    "command": "ps aux --sort=-%cpu | head -n 20",
                    "sudo": False,
                },
                "secondary": {
                    "label": "Top RAM",
                    "command": "ps aux --sort=-%mem | head -n 20",
                    "sudo": False,
                },
                "tertiary": {
                    "label": "Find process",
                    "command": "ps aux | grep -i {target} | grep -v grep",
                    "sudo": False,
                    "requires_target": True,
                },
                "quaternary": {
                    "label": "Kill PID",
                    "command": "kill -9 {target}",
                    "sudo": True,
                    "requires_target": True,
                },
            },
        },
        "packages": {
            "title": "APT package management",
            "target_placeholder": "Package name (example: htop)",
            "extra_placeholder": "Optional argument",
            "actions": {
                "primary": {
                    "label": "APT update",
                    "command": "apt-get update",
                    "sudo": True,
                },
                "secondary": {
                    "label": "APT upgrade -y",
                    "command": "apt-get upgrade -y",
                    "sudo": True,
                },
                "tertiary": {
                    "label": "Install package",
                    "command": "apt-get install -y {target}",
                    "sudo": True,
                    "requires_target": True,
                },
                "quaternary": {
                    "label": "Remove package",
                    "command": "apt-get remove -y {target}",
                    "sudo": True,
                    "requires_target": True,
                },
            },
        },
    }

    def __init__(self):
        super().__init__()
        self.current_section = "services"
        self.ssh_conn = None

    def compose(self):
        yield Header()
        yield Static("Management", id="mgmt_title")
        with Horizontal(id="mgmt_sections"):
            yield Button("Services", id="section_services")
            yield Button("Logs", id="section_journal")
            yield Button("Processes", id="section_processes")
            yield Button("Packages", id="section_packages")
        with Vertical(id="mgmt_controls"):
            yield Input(id="mgmt_target")
            yield Input(id="mgmt_extra")
            with Horizontal():
                yield Button("", id="act_primary")
                yield Button("", id="act_secondary")
                yield Button("", id="act_tertiary")
                yield Button("", id="act_quaternary")
            yield Input(id="mgmt_custom", placeholder="Custom command")
            with Horizontal():
                yield Button("Run custom", id="custom_run")
                yield Button("Run custom (sudo)", id="custom_run_sudo")
            yield Static("", id="mgmt_hint")
        yield Log(id="mgmt_log")
        yield Footer()

    def on_mount(self):
        config = get_ssh_config()
        self.ssh_conn = SSH(
            config["host"],
            config["user"],
            config["password"],
            config.get("sudo_password")
        )
        log = self.query_one("#mgmt_log", Log)

        try:
            self.ssh_conn.connect()
            log.write_line(f"Connected to {config['host']}@{config['user']}")
            self._apply_section_config()
        except Exception as exc:
            log.write_line(f"Connection error: {exc}")

    def _apply_section_config(self):
        section = self.SECTIONS[self.current_section]
        self.query_one("#mgmt_title", Static).update(section["title"])
        self.query_one("#mgmt_target", Input).placeholder = section["target_placeholder"]
        self.query_one("#mgmt_extra", Input).placeholder = section["extra_placeholder"]
        self.query_one("#mgmt_hint", Static).update(
            "Tip: for complex workflows use custom command."
        )

        for action_key in ("primary", "secondary", "tertiary", "quaternary"):
            button = self.query_one(f"#act_{action_key}", Button)
            button.label = section["actions"][action_key]["label"]

    @on(Button.Pressed, "#section_services")
    def switch_services(self):
        self.current_section = "services"
        self._apply_section_config()

    @on(Button.Pressed, "#section_journal")
    def switch_journal(self):
        self.current_section = "journal"
        self._apply_section_config()

    @on(Button.Pressed, "#section_processes")
    def switch_processes(self):
        self.current_section = "processes"
        self._apply_section_config()

    @on(Button.Pressed, "#section_packages")
    def switch_packages(self):
        self.current_section = "packages"
        self._apply_section_config()

    @on(Button.Pressed, "#act_primary")
    def action_primary(self):
        self._run_action("primary")

    @on(Button.Pressed, "#act_secondary")
    def action_secondary(self):
        self._run_action("secondary")

    @on(Button.Pressed, "#act_tertiary")
    def action_tertiary(self):
        self._run_action("tertiary")

    @on(Button.Pressed, "#act_quaternary")
    def action_quaternary(self):
        self._run_action("quaternary")

    def _run_action(self, action_key: str):
        if self.ssh_conn is None:
            self._log_line("SSH is not connected.")
            return

        section = self.SECTIONS[self.current_section]
        action = section["actions"][action_key]
        target = self.query_one("#mgmt_target", Input).value.strip()
        extra = self.query_one("#mgmt_extra", Input).value.strip()

        if action.get("requires_target") and not target:
            self._log_line("Missing target value.")
            return

        if action.get("requires_extra") and not extra:
            self._log_line("Missing extra value.")
            return

        command = action["command"].format(
            target=shlex.quote(target),
            extra=shlex.quote(extra),
        )
        self._execute_remote(command, action.get("sudo", False))

    @on(Button.Pressed, "#custom_run")
    def run_custom(self):
        custom = self.query_one("#mgmt_custom", Input).value.strip()
        if custom:
            self._execute_remote(custom, False)

    @on(Button.Pressed, "#custom_run_sudo")
    def run_custom_sudo(self):
        custom = self.query_one("#mgmt_custom", Input).value.strip()
        if custom:
            self._execute_remote(custom, True)

    @work(thread=True)
    def _execute_remote(self, command: str, use_sudo: bool):
        try:
            if use_sudo:
                out, err = self.ssh_conn.run_sudo_command(command)
            else:
                out, err = self.ssh_conn.run_command(command)
            self.app.call_from_thread(self._show_command_output, command, out, err, use_sudo)
        except Exception as exc:
            self.app.call_from_thread(self._log_line, f"Execution error: {exc}")

    def _show_command_output(self, command: str, out: str, err: str, use_sudo: bool):
        prefix = "[sudo]" if use_sudo else "[cmd]"
        self._log_line(f"\n{prefix} {command}")
        if out.strip():
            for line in out.strip().splitlines():
                self._log_line(line)
        if err.strip():
            for line in err.strip().splitlines():
                self._log_line(f"ERR: {line}")

    def _log_line(self, line: str):
        self.query_one("#mgmt_log", Log).write_line(line)

    def on_unmount(self):
        if self.ssh_conn is not None:
            self.ssh_conn.close()

