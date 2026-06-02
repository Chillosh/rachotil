"""
User interface for managing Docker containers.
"""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable, Log, TextArea
from textual.containers import Vertical, Horizontal
from textual import work

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.docker.docker_manager import DockerManager

class DockerScreen(Screen):
    """
    Screen displaying a list of Docker containers with management actions and Compose deployment.
    """
    CSS_PATH = "../styles.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.ssh = None
        self.docker_mgr = None

    def compose(self) -> None:
        yield Header()
        yield Footer()

        with Vertical(id="docker-main"):
            yield Static("Docker Container Dashboard", id="docker-title")

            with Horizontal(id="docker-actions"):
                yield Button("Refresh", id="btn-refresh-dock", variant="default")
                yield Button("Start", id="btn-start-dock", variant="success")
                yield Button("Stop", id="btn-stop-dock", variant="error")
                yield Button("Delete Selected", id="btn-delete-dock", variant="error")
                yield Button("View Logs", id="btn-logs-dock", variant="primary")

            yield Static("Deploy via Docker Compose (YAML):")
            yield TextArea(language="yaml", id="docker-yaml-input")
            yield Button("Deploy Compose", id="btn-deploy-compose", variant="primary")

            yield DataTable(id="docker-table", cursor_type="row")
            
            yield Log(id="docker-log", classes="status-display")
    
    def on_mount(self) -> None:
        table = self.query_one("#docker-table", DataTable)
        table.add_columns("Name", "State", "Status", "Image")

        self.write_log("Initializing... Connecting to server.")
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
            self.write_log(f"Successfully connected to {config['host']}")
            self.refresh_containers()
        except Exception as e:
            self.write_log(f"Connection failed: {str(e)}")

    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#docker-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-refresh-dock":
            self.refresh_containers()
        elif btn_id == "btn-deploy-compose":
            self.deploy_yaml()
        elif btn_id == "btn-delete-dock":
            self.delete_selected()
        else:
            self.manage_container(btn_id)

    @work(thread=True)
    def refresh_containers(self) -> None:
        if not self.docker_mgr:
            return

        success, result = self.docker_mgr.get_containers()
        
        if success:
            self.app.call_from_thread(self._update_table, result)
            self.write_log(f"Refreshed. Found {len(result)} containers.")
        else:
            self.write_log(result)

    def _update_table(self, data: list) -> None:
        table = self.query_one("#docker-table", DataTable)
        table.clear()
        for row in data:
            table.add_row(*row, key=row[0])

    @work(thread=True)
    def manage_container(self, btn_id: str) -> None:
        if not self.docker_mgr:
            return

        table = self.query_one("#docker-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            container_name = row_key.row_key.value
        except Exception:
            self.write_log("Error: No container selected.")
            return

        action = ""
        if btn_id == "btn-start-dock": action = "start"
        elif btn_id == "btn-stop-dock": action = "stop"
        elif btn_id == "btn-logs-dock": action = "logs"

        self.write_log(f"Executing '{action}' on {container_name}...")
        success, message = self.docker_mgr.manage_container(action, container_name)
        self.write_log(message)
        
        if success and action in ["start", "stop"]:
            self.refresh_containers()

    @work(thread=True)
    def delete_selected(self) -> None:
        if not self.docker_mgr:
            return

        table = self.query_one("#docker-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            container_name = row_key.row_key.value
        except Exception:
            self.write_log("Error: No container selected.")
            return

        self.write_log(f"Deleting container {container_name}...")
        success, msg = self.docker_mgr.delete_container(container_name)
        self.write_log(msg)
        if success:
            self.refresh_containers()

    @work(thread=True)
    def deploy_yaml(self) -> None:
        if not self.docker_mgr:
            return
            
        yaml_content = self.query_one("#docker-yaml-input", TextArea).text.strip()
        if not yaml_content:
            self.write_log("Error: YAML content cannot be empty.")
            return
            
        self.write_log("Deploying YAML configuration...")
        self.write_log("--- REAL-TIME OUTPUT ---")
        
        success_overall = True
        
        for success, line in self.docker_mgr.deploy_compose_stream(yaml_content):
            if not success:
                success_overall = False
            self.write_log(line)
            
        self.write_log("--- DONE ---")
        
        if success_overall:
            self.refresh_containers()