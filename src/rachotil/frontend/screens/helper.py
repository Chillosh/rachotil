"""
Global helper modal screen.
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal
from textual.events import Key
from ...backend.components.keybinds.keybinds_manager import load_keybinds

class HelperScreen(ModalScreen):
    """
    A modal screen that displays global keybinds and basic application info.
    """
    CSS_PATH = ["../components/styles/global.tcss"]

    def compose(self) -> ComposeResult:
        with Vertical(id="helper-container", classes="helper-modal"):
            yield Static("Rachotil - Quick Help", id="helper-title")
            
            yield Static(
                "Welcome to Rachotil! This application allows you to manage your remote Linux server.\n\n"
                "[bold cyan]Global Keybinds:[/bold cyan]\n"
                "  [bold]Space[/bold] (or custom) - Open the main navigation menu.\n"
                "  [bold]q[/bold] (or custom) - Quit the application.\n"
                "  [bold]h[/bold] - Open this help screen.\n\n"
                "[bold cyan]Tips:[/bold cyan]\n"
                "  • Use 'Settings' to change your SSH credentials or theme.\n"
                "  • Use the 'Terminal' screen for commands that require an interactive prompt.\n"
                "  • Most tables and lists can be navigated using arrow keys.",
                id="helper-content"
            )
            
            with Horizontal(id="helper-actions"):
                yield Button("Close Help", id="btn-close-help", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close-help":
            self.app.pop_screen()

    def action_close_help(self) -> None:
        self.app.pop_screen()