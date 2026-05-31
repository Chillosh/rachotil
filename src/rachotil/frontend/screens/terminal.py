"""
Screen for providing an interactive terminal shell via SSH.
"""

from textual.screen import Screen
from textual.widgets import Header, Footer, Log, Input

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.terminal.terminal_manager import TerminalManager


class TerminalScreen(Screen):
    """
    UI Screen that acts as a terminal emulator connected to the remote host.
    """
    CSS_PATH = "../styles.tcss"
    
    def __init__(self):
        super().__init__()
        self.ssh_conn = None
        self.term_mgr = None
        self.host = ""
        self.user = ""

    def compose(self) -> None:
        yield Header()
        yield Log(id="terminal_log")
        yield Input(id="sshInput", placeholder="Enter command ...")
        yield Footer()

    def on_mount(self) -> None:
        config = get_ssh_config()
        self.host = config["host"]
        self.user = config["user"]
        log = self.query_one("#terminal_log", Log)

        try:
            self.ssh_conn = SSH(
                self.host,
                self.user,
                config["password"],
                config.get("sudo_password"),
            )
            self.ssh_conn.connect()
            
            self.term_mgr = TerminalManager(self.ssh_conn)
            success, message = self.term_mgr.open_shell()
            
            if success:
                poll_interval = self.term_mgr.config.get("poll_interval", 0.5)
                self.set_interval(poll_interval, self.poll_shell_output)
                log.write_line(f"Connected to {self.host}@{self.user} (interactive shell)")
            else:
                log.write_line(message)
                
        except Exception as e:
            log.write_line(f"Error: {e}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        log = self.query_one("#terminal_log", Log)
        input_box = self.query_one("#sshInput", Input)

        if command:
            log.write_line(f"\n{self.user}@{self.host}:~$ {command}")
        input_box.value = ""

        if self.term_mgr:
            success, message = self.term_mgr.send_command(command)
            if not success:
                log.write_line(message)

    def poll_shell_output(self) -> None:
        """
        Periodically read and display output from the interactive SSH shell.
        """
        if not self.term_mgr:
            return

        output = self.term_mgr.read_output()
        if output:
            log = self.query_one("#terminal_log", Log)
            log.write_line(output)

    def on_unmount(self) -> None:
        if self.ssh_conn:
            self.ssh_conn.close()