"""
Screen for managing and scanning network services on the remote server.
"""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable, Log
from textual.containers import Vertical, Horizontal
from textual import work

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.network.network_manager import NetworkManager

class NetworkManagerScreen(Screen):
    """
    UI Screen for scanning and viewing details of network services.
    """
    CSS_PATH = "../styles.tcss"

    def __init__(self):
        super().__init__()
        self.ssh = None
        self.net_mgr = None

    def compose(self) -> None:
        yield Header()
        yield Footer()
        
        with Vertical(id="net-main"):
            yield Static("Network Services Manager", id="net-title")
            
            with Horizontal(id="net-controls"):
                yield Button("Scan Services", id="btn-refresh-net", variant="primary")
                yield Button("View Service Details", id="btn-details-net", variant="default")

            yield DataTable(id="net-table", cursor_type="row")
            yield Log(id="net-log", classes="status-display")

    def on_mount(self) -> None:
        table = self.query_one("#net-table", DataTable)
        table.add_columns("Software", "Deployment Type", "Installation Status", "Running State")
        
        try:
            config = get_ssh_config()
            self.ssh = SSH(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                sudo_password=config.get("sudo_password")
            )
            self.ssh.connect()
            self.net_mgr = NetworkManager(self.ssh)
            self.scan_network_services()
        except Exception as e:
            self.write_log(f"Connection failed: {str(e)}")

    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#net-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh-net":
            self.scan_network_services()
        elif event.button.id == "btn-details-net":
            self.view_detailed_status()

    @work(thread=True)
    def scan_network_services(self) -> None:
        """
        Scan the remote server for known network services.
        """
        if not self.net_mgr:
            return
            
        self.write_log("Scanning server for network applications...")
        
        success, result = self.net_mgr.scan_services()
        
        if success:
            self.app.call_from_thread(self._update_table, result)
            self.write_log("Scan finished, data updated.")
        else:
            self.write_log(f"Error: {result}")

    def _update_table(self, data: list) -> None:
        table = self.query_one("#net-table", DataTable)
        table.clear()
        for row in data:
            table.add_row(row[0], row[1], row[2], row[3], key=row[4])

    @work(thread=True)
    def view_detailed_status(self) -> None:
        """
        Fetch and display detailed status information for the selected service.
        """
        if not self.net_mgr:
            return
            
        table = self.query_one("#net-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            soft_id = row_key.row_key.value
        except Exception:
            self.write_log("Error: No service selected.")
            return

        self.write_log("Fetching diagnostic info...")
        
        success, details = self.net_mgr.get_service_details(soft_id)
        
        if not success:
            self.write_log(f"Error: {details}")
            return
            
        self.write_log(f"--- Systemd Status ({details['name']}) ---")
        self.write_log(details['systemd'])
        
        self.write_log(f"--- Recent Container Logs ({details['name']}) ---")
        self.write_log(details['docker'])