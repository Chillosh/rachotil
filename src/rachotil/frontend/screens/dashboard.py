"""
Dashboard screen for displaying overview system information.
"""

import json
from pathlib import Path
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Horizontal, Vertical
from textual import work

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.dashboard.dashboard_manager import DashboardManager

class DashboardScreen(Screen):
    """
    UI Screen that shows basic system metrics and information.
    """
    CSS_PATH = ["../components/styles/global.tcss", "../components/styles/dashboard.tcss"]

    def __init__(self) -> None:
        super().__init__()
        self.ssh = None
        self.dashboard_mgr = None

    def compose(self) -> None:
        yield Header()
        yield Footer()
        
        with Vertical(id="dashboard-main"):
            yield Static("System Dashboard", id="dashboard-title")
            with Horizontal(id="dashboard-content"):
                yield Static("", id="dashboard-ascii", classes="dashboard-box")
                yield Static("Loading system info...", id="dashboard-info", classes="dashboard-box")

    def on_mount(self) -> None:
        config_path = Path(__file__).resolve().parents[2] / "backend" / "storage" / "dashboard_config.json"        
        ascii_art = ""
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                ascii_art = data.get("ascii_art", "")
            except Exception:
                pass
                
        if not ascii_art:
            ascii_art = "No ASCII art configured.\nPlease set it up in Settings."

        self.query_one("#dashboard-ascii", Static).update(ascii_art)
        
        try:
            config = get_ssh_config()
            self.ssh = SSH(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                sudo_password=config.get("sudo_password")
            )
            self.ssh.connect()
            self.dashboard_mgr = DashboardManager(self.ssh)
            self.update_sys_info()
        except Exception as e:
            self.query_one("#dashboard-info", Static).update(f"Connection failed: {str(e)}")

    @work(thread=True)
    def update_sys_info(self) -> None:
        if not self.dashboard_mgr:
            return
            
        success, result = self.dashboard_mgr.fetch_sys_info()
        
        if success:
             self.app.call_from_thread(
                lambda: self.query_one("#dashboard-info", Static).update(result)
            )
        else:
             self.app.call_from_thread(
                lambda: self.query_one("#dashboard-info", Static).update(f"Error: {result}")
            )