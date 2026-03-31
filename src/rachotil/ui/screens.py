from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Log, SelectionList
from textual.widgets.selection_list import Selection
from ssh.ssh import SSH
from ssh.config import HOST, USER, PASSWORD


class rachotil(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("space", "toggle_menu", "Tool")
    ]
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Log(id="terminal_log")
        yield Input(id="prikaz_input", placeholder="Zadej příkaz...")
        yield SelectionList(
            Selection("Zkontrolovat disk", "df -h", True),
            Selection("Využití RAM", "free -m"),
            Selection("Běžící procesy", "top -b -n 1"),
            id="tool_selector"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#tool_selector").display = False
        self.ssh_conn = SSH(HOST, USER, PASSWORD)
        self.call_after_refresh(self.connect_ssh)

    def action_toggle_menu(self) -> None:
        menu = self.query_one("#tool_selector")
        menu.display = not menu.display
        if menu.display:
            menu.focus()
        else:
            self.query_one("#prikaz_input").focus()

    def on_selection_list_selected(self, event: SelectionList.Selected) -> None:
        command = event.selection_list.highlighted_child.value

        for command in event.selection_list.selected:
            self.exec_ssh_command(command)

        self.action_toggle_menu()

    def exec_ssh_command(self, command: str) -> None:
        log = self.query_one("#terminal_log", Log)
        log.write_line(f"Spouštím tool: {command}")
        try:
            out, err = self.ssh_conn.run_command(command)
            if out: log.write_line(out.strip())
            if err: log.write_line(f"{err.strip()}")
        except Exception as e:
            log.write_line(f"Chyba: {e}")

    def connect_ssh(self) -> None:
        log = self.query_one("#terminal_log", Log)
        try:
            self.ssh_conn.connect()
            log.write_line(f"Spojení navázáno! {self.ssh_conn.host}@{self.ssh_conn.user}")
        except Exception as e:
            log.write_line(f"CHYBA: {e}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        if command:
            self.query_one("#prikaz_input").value = ""
            self.exec_ssh_command(command)

    def on_unmount(self) -> None:
        if hasattr(self, 'ssh_conn'):
            self.ssh_conn.close()