from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable, Log
from textual.containers import Vertical, Horizontal
from textual import work
from ...core.systemctl import SystemctlManager

class ServicesScreen(Screen):
    CSS_PATH = "../styles.tcss"

    def __init__(self):
        super().__init__()
        self.sys_mgr = SystemctlManager()

    def compose(self):
        yield Header()
        yield Footer()
        with Vertical(id="services-main"):
            yield Static("Service Manager", id="services-title")
            with Horizontal(id="services-actions"):
                yield Button("Refresh List", id="btn-refresh-svc", variant="default")
                yield Button("Start", id="btn-start-svc", variant="success")
                yield Button("Stop", id="btn-stop-svc", variant="error")
                yield Button("Restart", id="btn-restart-svc", variant="warning")
            yield DataTable(id="services-table", cursor_type="row")
            yield Log(id="services-log", classes="status-display")

    def action_open_main_menu(self) -> None:
        self.app.action_show_menu()

    def action_quit(self) -> None:
        self.app.action_quit()

    def on_mount(self) -> None:
        table = self.query_one("#services-table", DataTable)
        table.add_columns("Service Name", "Status")
        self.refresh_services()

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
        else:
            self.manage_service(btn_id)

    @work(thread=True)
    def refresh_services(self) -> None:
        self.write_log("Scanning system for active service units...")
        try:
            services = self.sys_mgr.get_all_services()
            results = []
            for svc_name, active_state in services:
                if active_state == "active":
                    display_status = "[bold green]Active[/bold green]"
                elif active_state in ["inactive", "failed"]:
                    display_status = f"[bold red]{active_state.capitalize()}[/bold red]"
                else:
                    display_status = f"[yellow]{active_state}[/yellow]"
                results.append((svc_name, display_status))
            
            self.app.call_from_thread(self._update_table, results)
            self.write_log(f"Scan complete. Found {len(results)} services.")
        except Exception as e:
            self.write_log(f"Scan failed: {str(e)}")

    def _update_table(self, data: list) -> None:
        table = self.query_one("#services-table", DataTable)
        table.clear()
        for row in data:
            table.add_row(*row, key=row[0])

    @work(thread=True)
    def manage_service(self, btn_id: str) -> None:
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

        self.write_log(f"Sending {action} command to {svc_name}...")
        try:
            out, err = self.sys_mgr.manage_service(svc_name, action)
            self.write_log(f"Command finished.")
            self.refresh_services()
        except Exception as e:
            self.write_log(f"Error: {str(e)}")