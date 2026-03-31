from textual.screen import Screen
from textual.widgets import Header, Footer, Label

class StatsScreen(Screen):
    def compose(self):
        yield Header()
        yield Label("Zatím jen STATY...", id="stats_label")
        yield Footer()