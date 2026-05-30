from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable, Log
from textual.containers import Vertical, Horizontal, Container
from textual import work
from ...core.docker_api import DockerManager

class DockerScreen(Screen):
    def __init__(self):
        super().__init__()
        self.docker_mgr = DockerManager()

    def compose(self):
        yield Header()
        yield Footer()
        with Vertical(id="docker-main"):
            yield Static("Docker Container Dashboard", id="docker-title")
            with Horizontal(id="docker-controls"):
                yield Button("Refresh", id="btn-refresh-docker", variant="default")
                yield Button("Start", id="btn-start-docker", variant="success")
                yield Button("Stop", id="btn-stop-docker", variant="error")
                yield Button("Restart", id="btn-restart-docker", variant="warning")
                yield Button("View Logs", id="btn-logs-docker", variant="primary")
            with Horizontal(id="docker-content"):
                yield DataTable(id="docker-table", cursor_type="row")
                with Container(id="docker-log-container"):
                    yield Static("Container Logs", id="docker-log-title")
                    yield Log(id="docker-log-view")
            yield Log(id="docker-status-log", classes="status-display")

    def on_mount(self) -> None:
        table = self.query_one("#docker-table", DataTable)
        table.add_columns("Name", "State", "Status", "Image")
        self.check_and_refresh()

    def write_status(self, message: str) -> None:
        try:
            log_widget = self.query_one("#docker-status-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-refresh-docker":
            self.refresh_containers()
        elif btn_id == "btn-logs-docker":
            self.fetch_container_logs()
        else:
            self.manage_container(btn_id)

    @work(thread=True)
    def check_and_refresh(self) -> None:
        try:
            is_installed, version = self.docker_mgr.check_installed()
            if not is_installed:
                self.write_status("Error: Docker is not installed.")
                return
            self.write_status(f"Found {version}. Loading containers...")
            self.refresh_containers()
        except Exception as e:
            self.write_status(f"Connection failed: {str(e)}")

    @work(thread=True)
    def refresh_containers(self) -> None:
        try:
            containers = self.docker_mgr.get_containers()
            results = []
            for name, state, status, image in containers:
                if state == "running":
                    display_state = f"[bold green]{state.capitalize()}[/bold green]"
                elif state == "exited":
                    display_state = f"[bold red]{state.capitalize()}[/bold red]"
                else:
                    display_state = f"[yellow]{state.capitalize()}[/yellow]"
                results.append((name, display_state, status, image))
            self.app.call_from_thread(self._update_table, results)
            self.write_status(f"Refreshed. Found {len(results)} containers.")
        except Exception as e:
            self.write_status(f"Failed: {str(e)}")

    def _update_table(self, data: list) -> None:
        table = self.query_one("#docker-table", DataTable)
        table.clear()
        for row in data:
            table.add_row(*row, key=row[0])

    @work(thread=True)
    def manage_container(self, btn_id: str) -> None:
        table = self.query_one("#docker-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            container_name = row_key.row_key.value
        except Exception:
            self.write_status("Error: No container selected.")
            return

        action = ""
        if btn_id == "btn-start-docker": action = "start"
        elif btn_id == "btn-stop-docker": action = "stop"
        elif btn_id == "btn-restart-docker": action = "restart"

        self.write_status(f"Executing '{action}'...")
        try:
            out, err = self.docker_mgr.manage_container(action, container_name)
            self.write_status(f"Command completed.")
            self.refresh_containers()
        except Exception as e:
            self.write_status(f"Error: {str(e)}")

    @work(thread=True)
    def fetch_container_logs(self) -> None:
        table = self.query_one("#docker-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            container_name = row_key.row_key.value
        except Exception:
            self.write_status("Error: No container selected.")
            return

        try:
            log_output = self.docker_mgr.get_logs(container_name)
            if not log_output:
                log_output = "No logs available."
            self.app.call_from_thread(self._update_log_view, container_name, log_output)
            self.write_status("Logs loaded.")
        except Exception as e:
            self.write_status(f"Error: {str(e)}")

    def _update_log_view(self, name: str, log_data: str) -> None:
        self.query_one("#docker-log-title", Static).update(f"Logs: {name}")
        log_view = self.query_one("#docker-log-view", Log)
        log_view.clear()
        for line in log_data.split("\n"):
            if line.strip():
                log_view.write_line(line)