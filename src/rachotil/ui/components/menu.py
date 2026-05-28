from textual.screen import ModalScreen
from textual.widgets import OptionList, Input
from textual.widgets.option_list import Option
from textual.containers import Vertical

class MenuScreen(ModalScreen[str]):
    CSS_PATH = "../styles.tcss"

    ALL_OPTIONS = [
        ("System Dashboard", "dashboard"),
        ("Stats Monitoring", "stats"),
        ("SSH Terminal", "term"),
        ("File Manager", "file_manager"),
        ("Management Tools", "management"),
        ("Backup Manager", "backup"),
        ("Snapshot Manager", "snapshot"),
        ("Service Manager", "services"),
        ("Firewall Manager", "firewall"),
        ("Settings", "settings")
    ]

    def compose(self):
        with Vertical(id="menu-container"):
            yield Input(placeholder="Search menu...", id="menu-search")
            yield OptionList(id="main_menu")

    def on_mount(self) -> None:
        self.filter_menu("")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "menu-search":
            self.filter_menu(event.value)

    def filter_menu(self, query: str) -> None:
        menu = self.query_one("#main_menu", OptionList)
        menu.clear_options()
        for label, opt_id in self.ALL_OPTIONS:
            if query.lower() in label.lower():
                menu.add_option(Option(label, id=opt_id))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option_id)

    def action_close(self) -> None:
        self.dismiss(None)