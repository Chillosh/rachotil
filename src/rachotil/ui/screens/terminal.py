import re
from textual.screen import Screen
from textual.widgets import Header, Footer, Log, Input
from ...core.ssh_client import SSHClientWrapper

class TerminalScreen(Screen):
    BINDINGS = [
        ("ctrl+m", "open_main_menu", "Menu"),
        ("q", "quit", "Quit")
    ]

    def compose(self):
        yield Header()
        yield Log(id="terminal_log")
        yield Input(id="sshInput", placeholder="Enter command ...")
        yield Footer()

    def action_open_main_menu(self) -> None:
        self.app.action_show_menu()

    def action_quit(self) -> None:
        self.app.action_quit()

    def on_mount(self):
        self.ssh_conn = SSHClientWrapper()
        log = self.query_one("#terminal_log", Log)

        try:
            self.ssh_conn.connect()
            self.ssh_conn.open_shell()
            self.set_interval(0.5, self.poll_shell_output)
            
            # Bezpečné vytažení jména a hosta čistě pro UI log
            user = self.ssh_conn.db.get("ssh", {}).get("user", "user")
            host = self.ssh_conn.db.get("ssh", {}).get("host", "host")
            log.write_line(f"Connected to {host}@{user} (interactive shell)")
        except Exception as e:
            log.write_line(f"Error: {e}")

    def clean_ansi(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        log = self.query_one("#terminal_log", Log)
        input_box = self.query_one("#sshInput", Input)

        if command:
            user = self.ssh_conn.db.get("ssh", {}).get("user", "user")
            host = self.ssh_conn.db.get("ssh", {}).get("host", "host")
            log.write_line(f"\n{user}@{host}:~$ {command}")
            
        input_box.value = ""

        try:
            self.ssh_conn.shell_send(command)
        except Exception as e:
            log.write_line(f"Critical error: {e}")

    def poll_shell_output(self):
        if not hasattr(self, "ssh_conn") or not self.ssh_conn.connected:
            return

        output = self.ssh_conn.shell_read()
        if output:
            clean_output = self.clean_ansi(output)
            log = self.query_one("#terminal_log", Log)
            log.write_line(clean_output)

    def on_unmount(self):
        if hasattr(self, 'ssh_conn'):
            self.ssh_conn.close()