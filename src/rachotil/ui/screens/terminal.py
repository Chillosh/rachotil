from textual.screen import Screen
from textual.widgets import Header, Footer, Log, Input
from ssh.ssh import SSH
from ssh.config import HOST, USER, PASSWORD


class TerminalScreen(Screen):
    def compose(self):
        yield Header()
        yield Log(id="terminal_log")
        yield Input(id="sshInput", placeholder="Enter command ...")
        yield Footer()

    def on_mount(self):
        self.ssh_conn = SSH(HOST, USER, PASSWORD)
        log = self.query_one("#terminal_log", Log)

        try:
            self.ssh_conn.connect()
            log.write_line(f"Connected to {HOST}@{USER}")
        except Exception as e:
            log.write_line(f"Error: {e}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        commmand = event.value.strip()
        log = self.query_one("#terminal_log", Log)
        Inpur = self.query_one("#sshInput", Input)

        if commmand:
            log.write_line(f"\n{USER}@{HOST}:~$ {commmand}")
            Inpur.value = ""
            try:
                out, err = self.ssh_conn.run_command(commmand)
                if out:
                    log.write_line(out.strip())
                if err:
                    log.write_line(f"{err.strip()}")

            except Exception as e:
                log.write_line(f"Critical error: {e}")

    def on_unmount(self):
        if hasattr(self, 'ssh_conn'):
            self.ssh_conn.close()