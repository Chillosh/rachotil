from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, DataTable, Log
from textual.containers import Vertical, Horizontal
from textual import work
from ...core.network import NetworkManager

class FirewallScreen(Screen):
    def __init__(self):
        super().__init__()
        self.net_mgr = NetworkManager()

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
        self.refresh_ufw()

    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#firewall-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-refresh-ufw": self.refresh_ufw()
        elif btn_id == "btn-enable-ufw": self.toggle_ufw(True)
        elif btn_id == "btn-disable-ufw": self.toggle_ufw(False)
        elif btn_id == "btn-add-rule": self.add_rule()
        elif btn_id == "btn-delete-rule": self.delete_rule()

    @work(thread=True)
    def toggle_ufw(self, enable: bool) -> None:
        try:
            self.net_mgr.toggle_ufw(enable)
            self.refresh_ufw()
        except Exception as e:
            self.write_log(f"Error: {str(e)}")

    @work(thread=True)
    def refresh_ufw(self) -> None:
        try:
            out = self.net_mgr.get_ufw_status()
            lines = out.split("\n")
            if "inactive" in out.lower():
                self.write_log("UFW is INACTIVE.")
                self.app.call_from_thread(self._update_table, [])
                return
                
            results = []
            parsing = False
            for line in lines:
                if line.startswith("[ 1]"): parsing = True
                if parsing and line.strip() and line.startswith("["):
                    parts = line.replace("]", "").replace("[", "").split()
                    if len(parts) >= 4:
                        results.append((parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()))
            
            self.app.call_from_thread(self._update_table, results)
            self.write_log("Rules loaded.")
        except Exception as e:
            self.write_log(f"Error: {str(e)}")

    def _update_table(self, data: list) -> None:
        table = self.query_one("#firewall-table", DataTable)
        table.clear()
        for row in data:
            table.add_row(*row, key=row[0])

    @work(thread=True)
    def add_rule(self) -> None:
        port = self.query_one("#fw-port", Input).value.strip()
        proto = self.query_one("#fw-proto", Input).value.strip().lower()
        if not port: return
        try:
            self.net_mgr.add_ufw_rule(port, proto)
            self.app.call_from_thread(lambda: setattr(self.query_one("#fw-port", Input), "value", ""))
            self.app.call_from_thread(lambda: setattr(self.query_one("#fw-proto", Input), "value", ""))
            self.refresh_ufw()
        except Exception as e:
            self.write_log(f"Error: {str(e)}")

    @work(thread=True)
    def delete_rule(self) -> None:
        table = self.query_one("#firewall-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            rule_id = row_key.row_key.value
            self.net_mgr.delete_ufw_rule(rule_id)
            self.refresh_ufw()
        except Exception as e:
            self.write_log(f"Error: {str(e)}")