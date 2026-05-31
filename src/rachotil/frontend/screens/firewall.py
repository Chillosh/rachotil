"""
Screen for managing the UFW firewall on the remote server.
"""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, DataTable, Log
from textual.containers import Vertical, Horizontal
from textual import work

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.firewall.firewall_manager import FirewallManager

class FirewallScreen(Screen):
    """
    UI Screen for managing firewall rules and status.
    """
    CSS_PATH = "../styles.tcss"

    def __init__(self):
        super().__init__()
        self.ssh = None
        self.firewall_mgr = None

    def compose(self) -> None:
        yield Header()
        yield Footer()
        
        with Vertical(id="firewall-main"):
            yield Static("UFW Firewall Manager", id="firewall-title")
            
            with Horizontal(id="firewall-controls"):
                yield Button("Enable UFW", id="btn-enable-ufw", variant="success")
                yield Button("Disable UFW", id="btn-disable-ufw", variant="error")
                yield Button("Refresh", id="btn-refresh-ufw", variant="default")
                
            yield DataTable(id="firewall-table", cursor_type="row")
            
            with Horizontal(id="firewall-add-rule"):
                yield Input(placeholder="Port (e.g. 80)", id="fw-port")
                yield Input(placeholder="Protocol (tcp/udp)", id="fw-proto")
                yield Button("Allow Port", id="btn-add-rule", variant="primary")
                yield Button("Delete Selected", id="btn-delete-rule", variant="error")
                
            yield Log(id="firewall-log", classes="status-display")

    def on_mount(self) -> None:
        table = self.query_one("#firewall-table", DataTable)
        table.add_columns("ID", "To", "Action", "From")
        
        try:
            config = get_ssh_config()
            self.ssh = SSH(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                sudo_password=config.get("sudo_password")
            )
            self.ssh.connect()
            self.firewall_mgr = FirewallManager(self.ssh)
            self.write_log("Connected successfully.")
            self.refresh_ufw()
        except Exception as e:
            self.write_log(f"Connection failed: {str(e)}")

    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#firewall-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-refresh-ufw":
            self.refresh_ufw()
        elif btn_id == "btn-enable-ufw":
            self.toggle_ufw("enable")
        elif btn_id == "btn-disable-ufw":
            self.toggle_ufw("disable")
        elif btn_id == "btn-add-rule":
            self.add_rule()
        elif btn_id == "btn-delete-rule":
            self.delete_rule()

    @work(thread=True)
    def toggle_ufw(self, action: str) -> None:
        """
        Enable or disable UFW on the server.
        """
        if not self.firewall_mgr:
            return
            
        self.write_log(f"Executing UFW {action}...")
        success, message = self.firewall_mgr.toggle_ufw(action)
        self.write_log(message)
        
        if success:
            self.refresh_ufw()

    @work(thread=True)
    def refresh_ufw(self) -> None:
        """
        Fetch current UFW status and rules.
        """
        if not self.firewall_mgr:
            return
            
        success, message, rules = self.firewall_mgr.get_status_and_rules()
        self.write_log(message)
        
        if success:
            self.app.call_from_thread(self._update_table, rules)

    def _update_table(self, data: list) -> None:
        table = self.query_one("#firewall-table", DataTable)
        table.clear()
        for row in data:
            table.add_row(*row, key=row[0])

    @work(thread=True)
    def add_rule(self) -> None:
        """
        Add a new firewall rule to allow specific ports.
        """
        if not self.firewall_mgr:
            return
            
        port_input = self.query_one("#fw-port", Input)
        proto_input = self.query_one("#fw-proto", Input)
        
        port = port_input.value.strip()
        proto = proto_input.value.strip().lower()
        
        self.write_log(f"Adding rule for port {port}...")
        success, message = self.firewall_mgr.add_rule(port, proto)
        
        if not success:
            self.write_log(f"Error: {message}")
            return
            
        self.write_log(message)
        self.app.call_from_thread(lambda: setattr(port_input, "value", ""))
        self.app.call_from_thread(lambda: setattr(proto_input, "value", ""))
        self.refresh_ufw()

    @work(thread=True)
    def delete_rule(self) -> None:
        """
        Delete the selected firewall rule.
        """
        if not self.firewall_mgr:
            return
            
        table = self.query_one("#firewall-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            rule_id = row_key.row_key.value
        except Exception:
            self.write_log("Error: No rule selected.")
            return
            
        self.write_log(f"Deleting rule ID {rule_id}...")
        success, message = self.firewall_mgr.delete_rule(rule_id)
        
        self.write_log(message)
        if success:
            self.refresh_ufw()