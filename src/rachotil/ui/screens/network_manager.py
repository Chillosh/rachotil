from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable, Log
from textual.containers import Vertical, Horizontal
from textual import work
from ...core.ssh_client import SSHClientWrapper

class NetworkManagerScreen(Screen):
    def __init__(self):
        super().__init__()
        self.ssh = SSHClientWrapper()
        self.supported_software = [
            {"id": "pihole", "name": "Pi-hole", "type": "Docker / Native", "service": "pihole"},
            {"id": "adguard", "name": "AdGuard Home", "type": "Docker / Native", "service": "adguard-home"},
            {"id": "dnsmasq", "name": "Dnsmasq DNS/DHCP", "type": "Native", "service": "dnsmasq"},
            {"id": "dhcpd", "name": "ISC DHCP Server", "type": "Native", "service": "isc-dhcp-server"}
        ]

    def compose(self):
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
        self.scan_network_services()

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
        self.write_log("Scanning server for network applications...")
        results = []
        try:
            for soft in self.supported_software:
                installed = "Not Installed"
                running = "Stopped"
                out_sys, _ = self.ssh.run_command(f"systemctl is-active {soft['service']}")
                if out_sys.strip() == "active":
                    installed = "Installed (System)"
                    running = "Running"
                elif out_sys.strip() in ["inactive", "failed"]:
                    installed = "Installed (System)"
                    running = "Stopped"
                    
                if installed == "Not Installed":
                    out_dock, _ = self.ssh.run_command(f"docker ps --filter name={soft['service']} --format '{{{{.Status}}}}'")
                    if out_dock.strip():
                        installed = "Installed (Docker)"
                        if "Up" in out_dock:
                            running = "Running"
                    else:
                        out_dock_all, _ = self.ssh.run_command(f"docker ps -a --filter name={soft['service']} --format '{{{{.Names}}}}'")
                        if out_dock_all.strip():
                            installed = "Installed (Docker)"
                            running = "Stopped"

                display_inst = f"[bold green]{installed}[/bold green]" if "Installed" in installed else "[yaml_not_inst]Not Installed[/yaml_not_inst]"
                display_run = f"[bold green]Running[/bold green]" if running == "Running" else f"[bold red]{running}[/bold red]"
                results.append((soft["name"], soft["type"], display_inst, display_run, soft["id"]))
                
            self.app.call_from_thread(self._update_table, results)
            self.write_log("Scan finished data updated.")
        except Exception as e:
            self.write_log(f"Error: {str(e)}")

    def _update_table(self, data: list) -> None:
        table = self.query_one("#net-table", DataTable)
        table.clear()
        for row in data:
            table.add_row(row[0], row[1], row[2], row[3], key=row[4])

    @work(thread=True)
    def view_detailed_status(self) -> None:
        table = self.query_one("#net-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            soft_id = row_key.row_key.value
        except Exception:
            self.write_log("Error: No service selected.")
            return

        soft = next((s for s in self.supported_software if s["id"] == soft_id), None)
        if not soft: return

        self.write_log(f"Fetching diagnostic info for {soft['name']}...")
        try:
            out_sys, _ = self.ssh.run_command(f"systemctl status {soft['service']} --no-pager -n 5")
            out_dock, _ = self.ssh.run_command(f"docker logs --tail 5 {soft['service']}")
            self.write_log(f"--- Systemd Status ({soft['name']}) ---")
            self.write_log(out_sys.strip() if out_sys.strip() else "No Native Systemd unit active.")
            self.write_log(f"--- Recent Container Logs ({soft['name']}) ---")
            self.write_log(out_dock.strip() if out_dock.strip() else "No active Docker container logs found.")
        except Exception as e:
            self.write_log(f"Error: {str(e)}")