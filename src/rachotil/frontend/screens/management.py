"""
Screen for general system management tasks like services, logs, processes, and packages.
"""

from textual import on, work
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Log, Static

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.management.management_manager import ManagementManager

class ManagementScreen(Screen):
    """
    UI Screen that allows executing various management actions on the remote server.
    """
    CSS_PATH = ["../components/styles/global.tcss"]

    def __init__(self):
        super().__init__()
        self.current_section = "services"
        self.ssh_conn = None
        self.mgmt_mgr = None
        self.sections = {}

    def compose(self) -> None:
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

    def on_mount(self) -> None:
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
            self.mgmt_mgr = ManagementManager(self.ssh_conn)
            self.sections = self.mgmt_mgr.load_sections()
            
            log.write_line(f"Connected to {config['host']}@{config['user']}")
            self._apply_section_config()
        except Exception as exc:
            log.write_line(f"Connection error: {exc}")

    def _apply_section_config(self) -> None:
        if not self.sections:
            return
            
        section = self.sections.get(self.current_section)
        if not section:
            return
            
        self.query_one("#mgmt_title", Static).update(section["title"])
        self.query_one("#mgmt_target", Input).placeholder = section["target_placeholder"]
        self.query_one("#mgmt_extra", Input).placeholder = section["extra_placeholder"]
        self.query_one("#mgmt_hint", Static).update("Tip: for complex workflows use custom command.")

        for action_key in ("primary", "secondary", "tertiary", "quaternary"):
            button = self.query_one(f"#act_{action_key}", Button)
            button.label = section["actions"][action_key]["label"]

    @on(Button.Pressed, "#section_services")
    def switch_services(self) -> None:
        self.current_section = "services"
        self._apply_section_config()

    @on(Button.Pressed, "#section_journal")
    def switch_journal(self) -> None:
        self.current_section = "journal"
        self._apply_section_config()

    @on(Button.Pressed, "#section_processes")
    def switch_processes(self) -> None:
        self.current_section = "processes"
        self._apply_section_config()

    @on(Button.Pressed, "#section_packages")
    def switch_packages(self) -> None:
        self.current_section = "packages"
        self._apply_section_config()

    @on(Button.Pressed, "#act_primary")
    def action_primary(self) -> None:
        self._run_action("primary")

    @on(Button.Pressed, "#act_secondary")
    def action_secondary(self) -> None:
        self._run_action("secondary")

    @on(Button.Pressed, "#act_tertiary")
    def action_tertiary(self) -> None:
        self._run_action("tertiary")

    @on(Button.Pressed, "#act_quaternary")
    def action_quaternary(self) -> None:
        self._run_action("quaternary")

    def _run_action(self, action_key: str) -> None:
        if not self.mgmt_mgr:
            self._log_line("Manager not connected.")
            return

        section = self.sections.get(self.current_section)
        if not section:
            return
            
        action = section["actions"][action_key]
        target = self.query_one("#mgmt_target", Input).value.strip()
        extra = self.query_one("#mgmt_extra", Input).value.strip()

        if action.get("requires_target") and not target:
            self._log_line("Missing target value.")
            return

        if action.get("requires_extra") and not extra:
            self._log_line("Missing extra value.")
            return

        self._execute_remote_action(action, target, extra)

    @work(thread=True)
    def _execute_remote_action(self, action_config: dict, target: str, extra: str) -> None:
        """
        Execute a predefined action on the remote server in a background thread.
        """
        success, command, out, err, use_sudo = self.mgmt_mgr.execute_action(action_config, target, extra)
        self.app.call_from_thread(self._show_command_output, command, out, err, use_sudo)

    @on(Button.Pressed, "#custom_run")
    def run_custom(self) -> None:
        custom = self.query_one("#mgmt_custom", Input).value.strip()
        if custom:
            self._execute_custom_remote(custom, False)

    @on(Button.Pressed, "#custom_run_sudo")
    def run_custom_sudo(self) -> None:
        custom = self.query_one("#mgmt_custom", Input).value.strip()
        if custom:
            self._execute_custom_remote(custom, True)

    @work(thread=True)
    def _execute_custom_remote(self, command: str, use_sudo: bool) -> None:
        """
        Execute a custom command on the remote server in a background thread.
        """
        if not self.mgmt_mgr:
            return
            
        success, out, err = self.mgmt_mgr.execute_custom(command, use_sudo)
        self.app.call_from_thread(self._show_command_output, command, out, err, use_sudo)

    def _show_command_output(self, command: str, out: str, err: str, use_sudo: bool) -> None:
        prefix = "[sudo]" if use_sudo else "[cmd]"
        self._log_line(f"\n{prefix} {command}")
        if out.strip():
            for line in out.strip().splitlines():
                self._log_line(line)
        if err.strip():
            for line in err.strip().splitlines():
                self._log_line(f"ERR: {line}")

    def _log_line(self, line: str) -> None:
        self.query_one("#mgmt_log", Log).write_line(line)

    def on_unmount(self) -> None:
        if self.ssh_conn is not None:
            self.ssh_conn.close()