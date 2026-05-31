from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, Label, Log, DataTable
from textual.containers import Container, Vertical, Horizontal
from textual import work
from ...backend.ssh.config import get_ssh_config
from ...backend.ssh.ssh import SSH

class SnapshotScreen(Screen):
    CSS_PATH = "../styles.tcss"

    def __init__(self):
        super().__init__()
        self.ssh = None

    def compose(self):
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
        if not self.ssh:
            return

        self.write_log("Fetching snapshots list from server...")
        try:
            out, err = self.ssh.run_sudo_command("timeshift --list")
            
            if "command not found" in err or "command not found" in out:
                self.write_log("Error: 'timeshift' is not installed on the server.")
                self.write_log("Run: sudo apt install timeshift")
                return

            parsed_data = []
            lines = out.split("\n")
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0].isdigit() and parts[1] == '>':
                    s_id = parts[0]
                    s_date = parts[2]
                    s_tags = parts[3] if len(parts) > 3 else ""
                    s_desc = " ".join(parts[4:]) if len(parts) > 4 else ""
                    parsed_data.append((s_id, s_date, s_tags, s_desc))

            self.app.call_from_thread(self._update_table, parsed_data)
            self.write_log("Snapshot list updated.")

        except Exception as e:
            self.write_log(f"Failed to fetch snapshots: {str(e)}")

    def _update_table(self, data: list) -> None:
        table = self.query_one("#snapshot-table", DataTable)
        table.clear()
        for row in data:
            table.add_row(*row, key=row[1])

    @work(thread=True)
    def create_snapshot(self, description: str) -> None:
        if not self.ssh:
            return

        self.write_log("Creating new system snapshot. This may take a few minutes...")
        try:
            cmd = "timeshift --create"
            if description:
                cmd += f" --comments '{description}'"
            
            out, err = self.ssh.run_sudo_command(cmd)
            
            if "E:" in out or "Error" in err:
                self.write_log("Failed to create snapshot.")
                self.write_log(err or out)
            else:
                self.write_log("Snapshot created successfully.")
                self.app.call_from_thread(
                    lambda: setattr(self.query_one("#snapshot-desc-input", Input), "value", "")
                )
                self.refresh_snapshots()

        except Exception as e:
            self.write_log(f"Error creating snapshot: {str(e)}")

    @work(thread=True)
    def delete_selected_snapshot(self) -> None:
        table = self.query_one("#snapshot-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            snap_name = row_key.row_key.value
        except Exception:
            self.write_log("Error: No snapshot selected.")
            return

        self.write_log(f"Deleting snapshot {snap_name}...")
        try:
            cmd = f"timeshift --delete --snapshot '{snap_name}'"
            out, err = self.ssh.run_sudo_command(cmd)
            self.write_log(f"Snapshot {snap_name} deleted.")
            self.refresh_snapshots()
        except Exception as e:
            self.write_log(f"Error deleting snapshot: {str(e)}")

    @work(thread=True)
    def restore_selected_snapshot(self) -> None:
        table = self.query_one("#snapshot-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            snap_name = row_key.row_key.value
        except Exception:
            self.write_log("Error: No snapshot selected.")
            return

        self.write_log(f"WARNING: Restoring system to {snap_name}...")
        self.write_log("The server will automatically reboot if successful.")
        
        try:
            cmd = f"timeshift --restore --snapshot '{snap_name}' --yes"
            self.ssh.run_sudo_command(cmd)
            self.write_log("Restore command sent. Connection may drop due to reboot.")
        except Exception as e:
            self.write_log(f"Error during restore: {str(e)}")