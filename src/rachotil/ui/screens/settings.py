from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Button, SelectionList
from textual.containers import Horizontal
from textual.widgets.option_list import Option
from textual import on

CSS_PATH = "../styles.tcss"

class SettingsScreen(Screen):
    def compose(self):
        yield Header()
        yield Button("Stats Configuration", id="stats")
        yield Footer()

    @on(Button.Pressed, "#stats")
    def show_stats_menu(self):
        self.app.push_screen(StatsSettingsModal())

class StatsSettingsModal(ModalScreen):
    def compose(self):
        yield SelectionList(
            ("RAM+CPU monitoring", 0),
            ("DISK load", 1),
            ("NETWORK", 2),
            ("PROCESSES", 3),
            ("SERVICES", 4),
            ("USERS", 5),
            id="stats_options"
        )
        with Horizontal():
            yield Button("Save", id="save")
            yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#cancel")
    def return_to_settings(self):
        self.app.pop_screen()