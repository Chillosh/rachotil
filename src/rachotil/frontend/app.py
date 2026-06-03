"""
Main application class for Rachotil.
"""

from textual.app import App
from rachotil.frontend.screens.docker import DockerScreen
from rachotil.frontend.screens.file_manager import FileManagerScreen
from rachotil.frontend.screens.services import ServicesScreen
from rachotil.frontend.screens.dashboard import DashboardScreen
from rachotil.frontend.screens.snapshot import SnapshotScreen
from .components.menu import MenuScreen
from .screens.packages import PackagesScreen
from .screens.settings import SettingsScreen
from .screens.terminal import TerminalScreen
from .screens.stats import StatsScreen
from .screens.backup import BackupScreen
from rachotil.frontend.screens.pihole import PiholeScreen
from rachotil.frontend.screens.helper import HelperScreen
from rachotil.backend.components.keybinds.keybinds_manager import load_keybinds


class Rachotil(App):
    """
    Main Textual Application for controlling remote Linux servers.
    """
    CSS_PATH = ["components/styles/global.tcss"]

    def on_mount(self) -> None:
        self.apply_keybinds()
        self.push_screen(DashboardScreen())

    def apply_keybinds(self) -> None:
        config = load_keybinds()
        self.bind(config.get("menu", "space"), "show_menu", description="Menu")
        self.bind(config.get("quit", "q"), "quit", description="Quit")
        self.bind(config.get("help", "h"), "show_help", description="Help")
        self.bind("h", "show_help", description="Help")
        self.refresh_bindings()

    def action_show_menu(self) -> None:
        """
        Display the main menu overlay.
        """
        def check_menu_result(choice: str | None) -> None:
            if choice == "term":
                self.switch_screen(TerminalScreen())
            elif choice == "dashboard":
                self.switch_screen(DashboardScreen())
            elif choice == "stats":
                self.switch_screen(StatsScreen())
            elif choice == "file_manager":
                self.switch_screen(FileManagerScreen())
            elif choice == "packages":
                self.switch_screen(PackagesScreen())
            elif choice == "backup":
                self.switch_screen(BackupScreen())
            elif choice == "settings":
                self.switch_screen(SettingsScreen())
            elif choice == "snapshot":
                self.switch_screen(SnapshotScreen())
            elif choice == "services":
                self.switch_screen(ServicesScreen())
            elif choice == "docker":
                self.switch_screen(DockerScreen())
            elif choice == "pihole":
                self.switch_screen(PiholeScreen())

        self.push_screen(MenuScreen(), check_menu_result)
    
    def action_show_help(self) -> None:
        """
        Push the global helper modal onto the screen stack.
        """
        self.push_screen(HelperScreen())