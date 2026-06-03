"""
User interface screen for managing APT packages.
"""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, Log
from textual.containers import Vertical, Horizontal
from textual import work

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.packages.packages_manager import PackagesManager

class PackagesScreen(Screen):
    """
    Screen providing an interface for searching, installing, and removing packages via APT.
    """
    CSS_PATH = ["../components/styles/global.tcss"]

    def __init__(self) -> None:
        super().__init__()
        self.ssh = None
        self.pkg_mgr = None

    def compose(self) -> None:
        yield Header()
        yield Footer()

        with Vertical(id="pkg-main"):
            yield Static("APT Package Manager", id="pkg-title")

            yield Input(placeholder="Package name (e.g. htop, curl, nano)...", id="pkg-input")

            with Horizontal(id="pkg-actions"):
                yield Button("Search", id="btn-search-pkg", variant="default")
                yield Button("Install", id="btn-install-pkg", variant="success")
                yield Button("Remove", id="btn-remove-pkg", variant="error")
            
            with Horizontal(id="pkg-global-actions"):
                yield Button("APT Update (Fetch lists)", id="btn-update-pkg", variant="warning")
                yield Button("APT Upgrade (Install updates)", id="btn-upgrade-pkg", variant="warning")

            yield Log(id="pkg-log", classes="status-display")

    def on_mount(self) -> None:
        try:
            config = get_ssh_config()
            self.ssh = SSH(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                sudo_password=config.get("sudo_password")
            )
            self.ssh.connect()
            self.pkg_mgr = PackagesManager(self.ssh)
            self.write_log("Connected to server. Ready for APT operations.")
        except Exception as e:
            self.write_log(f"Connection failed: {str(e)}")

    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#pkg-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        package_name = self.query_one("#pkg-input", Input).value.strip()

        if btn_id == "btn-search-pkg":
            self.execute_apt_action("search", package_name)
        elif btn_id == "btn-install-pkg":
            self.execute_apt_action("install", package_name)
        elif btn_id == "btn-remove-pkg":
            self.execute_apt_action("remove", package_name)
        elif btn_id == "btn-update-pkg":
            self.execute_apt_action("update")
        elif btn_id == "btn-upgrade-pkg":
            self.execute_apt_action("upgrade")

    @work(thread=True)
    def execute_apt_action(self, action: str, package: str = "") -> None:
        """
        Run the selected APT action through the backend manager and stream logs in real-time.
        """
        if not self.pkg_mgr:
            return

        if action in ["install", "remove", "search"] and not package:
            self.write_log("Error: You must specify a package name for this action.")
            return

        self.write_log(f"Executing: apt {action} {package} ...")
        self.write_log("--- REAL-TIME OUTPUT ---")
        
        success_overall = True

        for success, line in self.pkg_mgr.execute_apt_stream(action, package):
            if not success:
                success_overall = False
            self.write_log(line)
            
        self.write_log("--- DONE ---")
        
        if success_overall and action in ["install", "remove"]:
            self.app.call_from_thread(lambda: setattr(self.query_one("#pkg-input", Input), "value", ""))