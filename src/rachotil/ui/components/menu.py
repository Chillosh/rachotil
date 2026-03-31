from textual.screen import ModalScreen
from textual.widgets import OptionList
from textual.widgets.option_list import Option


class MenuScreen(ModalScreen[str]):
    CSS_PATH = "../styles.tcss"

    def compose(self):
        yield OptionList(
            Option("Stats", id="stats"),
            Option("SSH", id="term"),
            Option("Settings", id="settings"),
            id="main_menu"
        )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option_id)

    def action_close(self) -> None:
        self.dismiss(None)