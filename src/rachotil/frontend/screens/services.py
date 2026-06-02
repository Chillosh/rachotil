"""
Screen for managing system services via systemd on the remote server.
"""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable, Log
from textual.containers import Vertical, Horizontal
from textual import work

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.services.services_manager import ServicesManager

class ServicesScreen(Screen):
    """
    UI Screen that allows starting, stopping, and restarting system services.
    """
    CSS_PATH = "../styles.tcss"

    def __init__(self):
        super().__init__()
        self.ssh = None
        self.services_mgr = None

    def compose(self) -> None:
        yield Header()
        yield Footer()
        
        with Vertical(id="services-main"):
            yield Static("Service Manager", id="services-title")
            
            with Horizontal(id="services-actions"):
                yield Button("Refresh List", id="btn-refresh-svc", variant="default")
                yield Button("Start", id="btn-start-svc", variant="success")
                yield Button("Stop", id="btn-stop-svc", variant="error")
                yield Button("Restart", id="btn-restart-svc", variant="warning")
                yield Button("View Logs", id="btn-logs-svc", variant="primary")
                
            yield DataTable(id="services-table", cursor_type="row")
            yield Log(id="services-log", classes="status-display")

    def on_mount(self) -> None:
        table = self.query_one("#services-table", DataTable)
        table.add_columns("Service Name", "Status")
        
        try:
            config = get_ssh_config()
            self.ssh = SSH(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                sudo_password=config.get("sudo_password")
            )
            self.ssh.connect()
            self.services_mgr = ServicesManager(self.ssh)
            self.refresh_services()
        except Exception as e:
            self.write_log(f"Connection failed: {str(e)}")

    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#services-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-refresh-svc":
            self.refresh_services()
        elif btn_id == "btn-logs-svc":
            self.view_logs() # NOVÁ AKCE
        else:
            self.manage_service(btn_id)

    @work(thread=True)
    def refresh_services(self) -> None:
        """
        Scan remote system for active service units.
        """
        if not self.services_mgr:
            return
            
        self.write_log("Scanning system for active service units...")
        
        success, results = self.services_mgr.get_services()
        
        if success:
             self.app.call_from_thread(self._update_table, results)
             self.write_log(f"Scan complete. Found {len(results)} services.")
        else:
             self.write_log(results)

    def _update_table(self, data: list) -> None:
        table = self.query_one("#services-table", DataTable)
        table.clear()
        for row in data:
            table.add_row(*row, key=row[0])

    @work(thread=True)
    def manage_service(self, btn_id: str) -> None:
        """
        Execute start/stop/restart actions on a selected service.
        """
        if not self.services_mgr:
             return

        table = self.query_one("#services-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            svc_name = row_key.row_key.value
        except Exception:
            self.write_log("Error: No service selected.")
            return

        action = ""
        if btn_id == "btn-start-svc": action = "start"
        elif btn_id == "btn-stop-svc": action = "stop"
        elif btn_id == "btn-restart-svc": action = "restart"
        
        if not action:
            return

        self.write_log(f"Sending '{action}' command to {svc_name}...")
        
        success, message = self.services_mgr.manage_service(action, svc_name)
        
        if success:
             if message:
                 self.write_log(f"Command output: {message}")
             self.refresh_services()
        else:
             self.write_log(message)

    @work(thread=True)
    def view_logs(self) -> None:
        """
        Fetch and display logs for the currently selected service.
        """
        if not self.services_mgr:
             return

        table = self.query_one("#services-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            svc_name = row_key.row_key.value
        except Exception:
            self.write_log("Error: No service selected.")
            return

        self.write_log(f"Fetching logs for {svc_name}...")
        success, message = self.services_mgr.get_service_logs(svc_name)
        
        if success:
            self.write_log(f"--- LOGS: {svc_name} ---")
            self.write_log(message)
            self.write_log("-----------------------")
        else:
            self.write_log(message)