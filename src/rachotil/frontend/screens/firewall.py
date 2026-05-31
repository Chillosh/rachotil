from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, DataTable, Log
from textual.containers import Vertical, Horizontal
from textual import work
from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH

class FirewallScreen(Screen):
    CSS_PATH = "../styles.tcss"

    def __init__(self):
        super().__init__()
        self.ssh = None

    def compose(self):
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
        if not self.ssh:
            return
        self.write_log(f"Executing UFW {action}...")
        out, err = self.ssh.run_sudo_command(f"ufw --force {action}")
        self.write_log(out.strip() or err.strip())
        self.refresh_ufw()

    @work(thread=True)
    def refresh_ufw(self) -> None:
        if not self.ssh:
            return
            
        out, err = self.ssh.run_sudo_command("ufw status numbered")
        lines = out.split("\n")
        
        if "inactive" in out.lower():
            self.write_log("UFW is currently INACTIVE.")
            self.app.call_from_thread(self._update_table, [])
            return
            
        self.write_log("UFW is ACTIVE. Parsing rules...")
        results = []
        parsing_rules = False
        
        for line in lines:
            if line.startswith("[ 1]"): 
                parsing_rules = True
            
            if parsing_rules and line.strip() and line.startswith("["):
                parts = line.replace("]", "").replace("[", "").split()
                if len(parts) >= 4:
                    rule_id = parts[0].strip()
                    rule_to = parts[1].strip()
                    rule_action = parts[2].strip()
                    rule_from = parts[3].strip()
                    results.append((rule_id, rule_to, rule_action, rule_from))
        
        self.app.call_from_thread(self._update_table, results)

    def _update_table(self, data: list) -> None:
        table = self.query_one("#firewall-table", DataTable)
        table.clear()
        for row in data:
            table.add_row(*row, key=row[0])

    @work(thread=True)
    def add_rule(self) -> None:
        port = self.query_one("#fw-port", Input).value.strip()
        proto = self.query_one("#fw-proto", Input).value.strip().lower()
        
        if not port:
            self.write_log("Error: Port is required.")
            return
            
        cmd = f"ufw allow {port}"
        if proto in ["tcp", "udp"]:
            cmd += f"/{proto}"
            
        self.write_log(f"Adding rule: {cmd}")
        out, err = self.ssh.run_sudo_command(cmd)
        self.write_log(out.strip() or err.strip())
        
        self.app.call_from_thread(lambda: setattr(self.query_one("#fw-port", Input), "value", ""))
        self.app.call_from_thread(lambda: setattr(self.query_one("#fw-proto", Input), "value", ""))
        self.refresh_ufw()

    @work(thread=True)
    def delete_rule(self) -> None:
        table = self.query_one("#firewall-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            rule_id = row_key.row_key.value
        except Exception:
            self.write_log("Error: No rule selected.")
            return
            
        self.write_log(f"Deleting rule ID {rule_id}...")
        out, err = self.ssh.run_sudo_command(f"ufw --force delete {rule_id}")
        self.write_log(out.strip() or err.strip())
        self.refresh_ufw()