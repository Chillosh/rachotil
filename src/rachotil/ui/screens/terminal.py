from textual.screen import Screen
from textual.widgets import Header, Footer, Log, Input
from ssh.ssh import SSH
from ssh.config import get_ssh_config


class TerminalScreen(Screen):
    def compose(self):
        yield Header()
        yield Log(id="terminal_log")
        yield Input(id="sshInput", placeholder="Enter command ...")
        yield Footer()

    def on_mount(self):
        config = get_ssh_config()
        self.host = config["host"]
        self.user = config["user"]
        self.ssh_conn = SSH(self.host, self.user, config["password"])
        log = self.query_one("#terminal_log", Log)

        try:
            self.ssh_conn.connect()
            log.write_line(f"Connected to {self.host}@{self.user}")
        except Exception as e:
            log.write_line(f"Error: {e}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        log = self.query_one("#terminal_log", Log)
        input_box = self.query_one("#sshInput", Input)

        if command:
            log.write_line(f"\n{self.user}@{self.host}:~$ {command}")
            input_box.value = ""
            try:
                out, err = self.ssh_conn.run_command(command)
                if out:
                    log.write_line(out.strip())
                if err:
                    log.write_line(f"{err.strip()}")

            except Exception as e:
                log.write_line(f"Critical error: {e}")

    def on_unmount(self):
        if hasattr(self, 'ssh_conn'):
            self.ssh_conn.close()