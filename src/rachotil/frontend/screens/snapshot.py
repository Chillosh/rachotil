"""
Screen for managing system snapshots using Timeshift on the remote server.
"""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, Log, DataTable
from textual.containers import Container, Vertical, Horizontal
from textual import work

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.snapshot.snapshot_manager import SnapshotManager

class SnapshotScreen(Screen):
    """
    UI Screen for creating, removing and restoring system snapshots.
    """
    CSS_PATH = ["../components/styles/global.tcss", "../components/styles/snapshot.tcss"]

    def __init__(self):
        super().__init__()
        self.ssh = None
        self.snap_mgr = None

    def compose(self) -> None:
        yield Header()
        yield Footer()

        with Vertical(id="snapshot-main"):
            yield Static("System Snapshot Manager", id="snapshot-title")

            with Horizontal(id="snapshot-create-container"):
                yield Input(placeholder="Enter snapshot description...", id="snapshot-desc-input")
                yield Button("Create Snapshot", id="btn-create-snap", variant="primary")

            with Container(id="snapshot-table-container"):
                yield DataTable(id="snapshot-table", cursor_type="row")

            with Horizontal(id="snapshot-actions"):
                yield Button("Refresh List", id="btn-refresh-snap", variant="default")
                yield Button("Restore Selected", id="btn-restore-snap", variant="warning")
                yield Button("Delete Selected", id="btn-delete-snap", variant="error")

            yield Log(id="snapshot-status-log", classes="status-display")

    def on_mount(self) -> None:
        table = self.query_one("#snapshot-table", DataTable)
        table.add_columns("Index", "Snapshot Name (Date)", "Tags", "Description")

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
            self.snap_mgr = SnapshotManager(self.ssh)
            self.write_log(f"Successfully connected to {config['host']}")
            self.refresh_snapshots()
        except Exception as e:
            self.write_log(f"Connection failed: {str(e)}")

    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#snapshot-status-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-refresh-snap":
            self.refresh_snapshots()
        elif btn_id == "btn-create-snap":
            desc = self.query_one("#snapshot-desc-input", Input).value.strip()
            self.create_snapshot(desc)
        elif btn_id == "btn-restore-snap":
            self.restore_selected_snapshot()
        elif btn_id == "btn-delete-snap":
            self.delete_selected_snapshot()

    @work(thread=True)
    def refresh_snapshots(self) -> None:
        """
        Fetch the list of system snapshots from the server.
        """
        if not self.snap_mgr:
            return

        self.write_log("Fetching snapshots list from server...")
        
        success, result = self.snap_mgr.get_snapshots()
        
        if success:
            self.app.call_from_thread(self._update_table, result)
            self.write_log("Snapshot list updated.")
        else:
            self.write_log(result)

    def _update_table(self, data: list) -> None:
        table = self.query_one("#snapshot-table", DataTable)
        table.clear()
        for row in data:
            table.add_row(*row, key=row[1])

    @work(thread=True)
    def create_snapshot(self, description: str) -> None:
        """
        Create a new system snapshot with the given description.
        """
        if not self.snap_mgr:
            return

        self.write_log("Creating new system snapshot. This may take a few minutes...")
        
        success, message = self.snap_mgr.create_snapshot(description)
        
        if success:
            self.write_log(message)
            self.app.call_from_thread(
                lambda: setattr(self.query_one("#snapshot-desc-input", Input), "value", "")
            )
            self.refresh_snapshots()
        else:
            self.write_log("Failed to create snapshot.")
            self.write_log(message)

    @work(thread=True)
    def delete_selected_snapshot(self) -> None:
        """
        Delete the snapshot currently selected in the table.
        """
        if not self.snap_mgr:
            return
            
        table = self.query_one("#snapshot-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            snap_name = row_key.row_key.value
        except Exception:
            self.write_log("Error: No snapshot selected.")
            return

        self.write_log(f"Deleting snapshot {snap_name}...")
        
        success, message = self.snap_mgr.delete_snapshot(snap_name)
        self.write_log(message)
        
        if success:
            self.refresh_snapshots()

    @work(thread=True)
    def restore_selected_snapshot(self) -> None:
        """
        Restore the system to the selected snapshot.
        """
        if not self.snap_mgr:
            return
            
        table = self.query_one("#snapshot-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            snap_name = row_key.row_key.value
        except Exception:
            self.write_log("Error: No snapshot selected.")
            return

        self.write_log(f"WARNING: Restoring system to {snap_name}...")
        self.write_log("The server will automatically reboot if successful.")
        
        success, message = self.snap_mgr.restore_snapshot(snap_name)
        self.write_log(message)