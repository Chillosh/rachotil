"""
Screen for managing Docker containers on the remote server.
"""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable, Log
from textual.containers import Vertical, Horizontal, Container
from textual import work

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.docker.docker_manager import DockerManager

class DockerScreen(Screen):
    """
    UI Screen for listing and managing Docker containers.
    """
    CSS_PATH = "../styles.tcss"

    def __init__(self):
        super().__init__()
        self.ssh = None
        self.docker_mgr = None

    def compose(self) -> None:
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
        
        try:
            config = get_ssh_config()
            self.ssh = SSH(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                sudo_password=config.get("sudo_password")
            )
            self.ssh.connect()
            self.docker_mgr = DockerManager(self.ssh)
            self.write_status("Connected successfully. Checking Docker installation...")
            self.check_docker_and_refresh()
        except Exception as e:
            self.write_status(f"Connection failed: {str(e)}")

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
    def check_docker_and_refresh(self) -> None:
        """
        Verify Docker installation and trigger initial container refresh.
        """
        if not self.docker_mgr:
            return
            
        success, message = self.docker_mgr.check_docker_installed()
        if not success:
            self.write_status(f"Error: {message}")
            self.write_status("Install it manually or use the Service Manager.")
            return
            
        self.write_status(f"Found {message}. Loading containers...")
        self.refresh_containers()

    @work(thread=True)
    def refresh_containers(self) -> None:
        """
        Fetch container data from the server and update the DataTable.
        """
        if not self.docker_mgr:
            return
            
        success, results = self.docker_mgr.get_containers()
        
        if success:
             self.app.call_from_thread(self._update_table, results)
             self.write_status(f"Refreshed. Found {len(results)} containers.")
        else:
             self.write_status(str(results))

    def _update_table(self, data: list) -> None:
        table = self.query_one("#docker-table", DataTable)
        table.clear()
        for row in data:
            table.add_row(*row, key=row[0])

    @work(thread=True)
    def manage_container(self, btn_id: str) -> None:
        """
        Execute container lifecycle operations (start/stop/restart).
        """
        if not self.docker_mgr:
             return

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

        if not action:
            return

        self.write_status(f"Executing '{action}' on container {container_name}...")
        
        success, message = self.docker_mgr.manage_container(action, container_name)
        
        if success:
             self.write_status(f"Command completed: {message}")
             self.refresh_containers()
        else:
             self.write_status(message)

    @work(thread=True)
    def fetch_container_logs(self) -> None:
        """
        Retrieve and display recent logs for the selected container.
        """
        if not self.docker_mgr:
             return

        table = self.query_one("#docker-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            container_name = row_key.row_key.value
        except Exception:
            self.write_status("Error: No container selected for logs.")
            return

        self.write_status(f"Fetching logs for {container_name}...")
        
        success, log_output = self.docker_mgr.get_container_logs(container_name)
        
        if success:
            self.app.call_from_thread(self._update_log_view, container_name, log_output)
            self.write_status("Logs loaded successfully.")
        else:
            self.write_status(log_output)

    def _update_log_view(self, name: str, log_data: str) -> None:
        title = self.query_one("#docker-log-title", Static)
        log_view = self.query_one("#docker-log-view", Log)
        
        title.update(f"Logs: {name}")
        log_view.clear()
        
        for line in log_data.split("\n"):
            if line.strip():
                log_view.write_line(line)