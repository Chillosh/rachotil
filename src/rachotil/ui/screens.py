from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Log
from ssh.ssh import SSH
from ssh.config import HOST, USER, PASSWORD


class rachotil(App):
    BINDINGS = [("q", "quit", "Quit")]
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Log(id="terminal_log")
        yield Input(id="prikaz_input", placeholder="Zadej příkaz...")
        yield Footer()

    def on_mount(self) -> None:
        self.ssh_conn = SSH(HOST, USER, PASSWORD)
        self.call_after_refresh(self.connect_ssh)

    def connect_ssh(self) -> None:
        log = self.query_one("#terminal_log", Log)
        try:
            self.ssh_conn.connect()
            log.write_line(f"Spojení navázáno! {self.ssh_conn.host}@{self.ssh_conn.user}")
        except Exception as e:
            log.write_line(f"CHYBA: {e}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        prikaz = event.value.strip()
        log = self.query_one("#terminal_log", Log)
        input_field = self.query_one("#prikaz_input", Input)

        if prikaz:
            log.write_line(f"{prikaz}")
            input_field.value = ""

            try:
                vystup, chyby = self.ssh_conn.run_command(prikaz)

                if vystup:
                    log.write_line(vystup.strip())
                if chyby:
                    log.write_line(f"{chyby.strip()}")
            except Exception as e:
                log.write_line(f"Chyba při provádění: {e}")

    def on_unmount(self) -> None:
        self.ssh_conn.close()