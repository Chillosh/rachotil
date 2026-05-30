from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, Log
from textual.containers import Vertical, Horizontal
from textual import work
from ...core.ssh_client import SSHClientWrapper

class BackupScreen(Screen):
    def __init__(self):
        super().__init__()
        self.ssh = SSHClientWrapper()

    def compose(self):
        yield Header()
        yield Footer()
        with Vertical(id="backup-main"):
            yield Static("Backup Manager (Rsync)", id="backup-title")
            with Horizontal(id="backup-controls"):
                yield Input(placeholder="Source path (e.g. /var/www)", id="backup-src")
                yield Input(placeholder="Destination path (e.g. /backup/www)", id="backup-dest")
                yield Button("Run Backup", id="btn-run-backup", variant="primary")
            yield Log(id="backup-log", classes="status-display")

    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#backup-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-run-backup":
            self.run_backup()

    @work(thread=True)
    def run_backup(self) -> None:
        src = self.query_one("#backup-src", Input).value.strip()
        dest = self.query_one("#backup-dest", Input).value.strip()

        if not src or not dest:
            self.write_log("Error: Source and Destination are required.")
            return

        self.write_log(f"Starting backup from {src} to {dest}...")
        try:
            cmd = f"rsync -avz {src} {dest}"
            out, err = self.ssh.run_sudo_command(cmd)
            self.write_log("Backup completed.")
            if out: self.write_log(out)
            if err: self.write_log(err)
        except Exception as e:
            self.write_log(f"Backup failed: {str(e)}")