from textual.app import App
from .components.menu import MenuScreen
from .screens.settings import SettingsScreen
from .screens.terminal import TerminalScreen
from .screens.stats import StatsScreen


class Rachotil(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("space", "show_menu", "Menu"),
        ("q", "quit", "Quit")
    ]

    def on_mount(self) -> None:
        self.push_screen(StatsScreen())

    def action_show_menu(self) -> None:
        def check_menu_result(choice: str | None) -> None:
            if choice == "term":
                self.switch_screen(TerminalScreen())
            elif choice == "stats":
                self.switch_screen(StatsScreen())
            elif choice == "settings":
                self.switch_screen(SettingsScreen())

        self.push_screen(MenuScreen(), check_menu_result)