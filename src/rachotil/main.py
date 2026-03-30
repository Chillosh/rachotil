import paramiko
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Log
from ssh.connection import host, user, password


class Rachotil(App):
    TITLE = "Rachotil"
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Log(id="terminal_log")
        yield Input(placeholder=f"Zadej příkaz pro {user}@{host}...", id="prikaz_input")
        yield Footer()

    def on_mount(self) -> None:
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(hostname=host, username=user, password=password, timeout=10)
        except Exception as e:
            self.log_message(f"CHYBA PŘIPOJENÍ: {e}")

    def log_message(self, text: str) -> None:
        self.query_one("#terminal_log").write_line(text)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        prikaz = event.value.strip()

        if prikaz.lower() in ["exit", "quit"]:
            return self.exit()

        if prikaz:
            self.log_message(f"{user}@{host}:~$ {prikaz}")
            self.query_one("#prikaz_input").value = ""

            try:
                stdin, stdout, stderr = self.client.exec_command(prikaz)
                vystup = stdout.read().decode()
                chyby = stderr.read().decode()

                if vystup:
                    self.log_message(vystup.strip())
                if chyby:
                    self.log_message(f"{chyby.strip()}")
            except Exception as e:
                self.log_message(f"Chyba při provádění: {e}")

    def on_unmount(self) -> None:
        if hasattr(self, 'client'):
            self.client.close()


if __name__ == "__main__":
    Rachotil().run()