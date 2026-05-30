from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable, Log
from textual.containers import Vertical, Horizontal
from textual import work
from ...core.ssh_client import SSHClientWrapper

class SnapshotScreen(Screen):
    def __init__(self):
        super().__init__()
        self.ssh = SSHClientWrapper()

    def compose(self):
        yield Header()
        yield Footer()
        with Vertical(id="snapshot-main"):
            yield Static("System Snapshot Manager (Timeshift)", id="snapshot-title")
            with Horizontal(id="snapshot-controls"):
                yield Button("List Snapshots", id="btn-list-snap", variant="default")
                yield Button("Create New Snapshot", id="btn-create-snap", variant="success")
                yield Button("Delete Selected", id="btn-delete-snap", variant="error")
            yield DataTable(id="snapshot-table", cursor_type="row")
            yield Log(id="snapshot-log", classes="status-display")

    def on_mount(self) -> None:
        table = self.query_one("#snapshot-table", DataTable)
        table.add_columns("Index", "Date", "Tags", "Comments")
        self.list_snapshots()

    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#snapshot-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-list-snap": self.list_snapshots()
        elif btn_id == "btn-create-snap": self.create_snapshot()
        elif btn_id == "btn-delete-snap": self.delete_snapshot()

    @work(thread=True)
    def list_snapshots(self) -> None:
        self.write_log("Fetching snapshots...")
        try:
            out, err = self.ssh.run_sudo_command("timeshift --list")
            lines = out.split("\n")
            results = []
            parsing = False
            for line in lines:
                if "---" in line:
                    parsing = True
                    continue
                if parsing and line.strip() and not line.startswith("Total"):
                    parts = line.split()
                    if len(parts) >= 3:
                        results.append((parts[0], f"{parts[1]} {parts[2]}", parts[3] if len(parts) > 3 else "", " ".join(parts[4:]) if len(parts) > 4 else ""))
            self.app.call_from_thread(self._update_table, results)
            self.write_log("List updated.")
        except Exception as e:
            self.write_log(f"Error: {str(e)}")

    def _update_table(self, data: list) -> None:
        table = self.query_one("#snapshot-table", DataTable)
        table.clear()
        for row in data:
            table.add_row(*row, key=row[0])

    @work(thread=True)
    def create_snapshot(self) -> None:
        self.write_log("Creating new system snapshot. This may take a few minutes...")
        try:
            out, err = self.ssh.run_sudo_command("timeshift --create")
            self.write_log("Snapshot created successfully.")
            self.list_snapshots()
        except Exception as e:
            self.write_log(f"Error: {str(e)}")

    @work(thread=True)
    def delete_snapshot(self) -> None:
        table = self.query_one("#snapshot-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            snap_index = row_key.row_key.value
        except Exception:
            self.write_log("Error: No snapshot selected.")
            return

        self.write_log(f"Deleting snapshot {snap_index}...")
        try:
            out, err = self.ssh.run_sudo_command(f"timeshift --delete --snapshot '{snap_index}'")
            self.write_log("Snapshot deleted.")
            self.list_snapshots()
        except Exception as e:
            self.write_log(f"Error: {str(e)}")