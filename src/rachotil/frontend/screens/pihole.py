"""
User interface screen for managing the Pi-hole DNS service.
"""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Log, Label
from textual.containers import Vertical, Horizontal
from textual import work

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.pihole.pihole_manager import PiholeManager

class PiholeScreen(Screen):
    """
    Screen displaying Pi-hole status, web address, and tools to fix port conflicts.
    """
    CSS_PATH = "../styles.tcss"
    
    def __init__(self) -> None:
        super().__init__()
        self.ssh = None
        self.pihole_mgr = None

    def compose(self) -> None:
        yield Header()
        yield Footer()
        
        with Vertical(id="pihole-main"):
            yield Static("Pi-hole Manager", id="pihole-title")
            
            with Vertical(id="pihole-info-panel"):
                yield Label("Status: Checking...", id="lbl-status")
                yield Label("Web Interface: Checking...", id="lbl-web")
            
            with Horizontal(id="pihole-actions"):
                yield Button("Refresh Status", id="btn-refresh", variant="primary")
                yield Button("Fix Port 53 (systemd-resolved)", id="btn-fix-53", variant="warning")
                yield Button("How to Install", id="btn-install", variant="success")
                
            yield Log(id="pihole-log", classes="status-display")

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
            self.pihole_mgr = PiholeManager(self.ssh)
            self.write_log("Connected. Checking Pi-hole status...")
            self.check_status()
        except Exception as e:
            self.write_log(f"Connection failed: {str(e)}")

    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#pihole-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-refresh":
            self.check_status()
        elif btn_id == "btn-fix-53":
            self.fix_port_53()
        elif btn_id == "btn-install":
            self.show_install_info()

    @work(thread=True)
    def check_status(self) -> None:
        """
        Fetch the current Pi-hole status from the backend and update the UI.
        """
        if not self.pihole_mgr:
            return
            
        success, data = self.pihole_mgr.check_status()
        if success:
            lbl_status = self.query_one("#lbl-status", Label)
            lbl_web = self.query_one("#lbl-web", Label)
            
            if data["installed"]:
                status_fmt = f"[bold green]{data['status']}[/bold green]" if data["status"] == "Running" else f"[bold red]{data['status']}[/bold red]"
                self.app.call_from_thread(lbl_status.update, f"Status: Installed & {status_fmt}")
                self.app.call_from_thread(lbl_web.update, f"Web Interface: {data['web_url']}")
                self.write_log("Status updated.")
            else:
                self.app.call_from_thread(lbl_status.update, "Status: [bold red]Not Installed[/bold red]")
                self.app.call_from_thread(lbl_web.update, "Web Interface: N/A")
                self.write_log("Pi-hole is not installed on this server.")
        else:
            self.write_log(f"Error: {data}")

    @work(thread=True)
    def fix_port_53(self) -> None:
        """
        Apply the systemd-resolved fix to free DNS port 53.
        """
        if not self.pihole_mgr:
            return
        self.write_log("Applying fix for port 53 (systemd-resolved)...")
        success, msg = self.pihole_mgr.fix_port_53()
        self.write_log(msg)

    def show_install_info(self) -> None:
        """
        Display instructions for the interactive Pi-hole installation process.
        """
        if not self.pihole_mgr:
            return
        cmd = self.pihole_mgr.get_install_command()
        self.write_log("--- HOW TO INSTALL PI-HOLE ---")
        self.write_log("Pi-hole requires an interactive setup screen (whiptail).")
        self.write_log("Please open the 'Terminal' screen in this app and run:")
        self.write_log(f"[bold cyan]{cmd}[/bold cyan]")
        self.write_log("------------------------------")