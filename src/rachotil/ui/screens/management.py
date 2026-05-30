from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Log
from textual.containers import Vertical, Horizontal
from textual import work
from ...core.ssh_client import SSHClientWrapper

class ManagementScreen(Screen):
    def __init__(self):
        super().__init__()
        self.ssh = SSHClientWrapper()

    def compose(self):
        yield Header()
        yield Footer()
        with Vertical(id="mgmt-main"):
            yield Static("Server Management Tools", id="mgmt-title")
            with Horizontal(id="mgmt-controls"):
                yield Button("Apt Update", id="btn-update", variant="primary")
                yield Button("Apt Upgrade", id="btn-upgrade", variant="warning")
                yield Button("Reboot Server", id="btn-reboot", variant="error")
            yield Log(id="mgmt-log")

    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#mgmt-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-update": self.run_command("apt update")
        elif btn_id == "btn-upgrade": self.run_command("apt upgrade -y")
        elif btn_id == "btn-reboot": self.run_command("reboot")

    @work(thread=True)
    def run_command(self, cmd: str) -> None:
        self.write_log(f"Executing: {cmd}...")
        try:
            out, err = self.ssh.run_sudo_command(cmd)
            if out: self.write_log(out)
            if err: self.write_log(err)
            self.write_log("Done.")
        except Exception as e:
            self.write_log(f"Command failed: {str(e)}")