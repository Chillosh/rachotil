"""
Main application class for Rachotil.
"""

from textual.app import App
from rachotil.frontend.screens.docker import DockerScreen
from rachotil.frontend.screens.file_manager import FileManagerScreen
from rachotil.frontend.screens.services import ServicesScreen
from rachotil.frontend.screens.firewall import FirewallScreen
from rachotil.frontend.screens.dashboard import DashboardScreen
from rachotil.frontend.screens.snapshot import SnapshotScreen
from .components.menu import MenuScreen
from .screens.management import ManagementScreen
from .screens.settings import SettingsScreen
from .screens.terminal import TerminalScreen
from .screens.stats import StatsScreen
from .screens.backup import BackupScreen
from rachotil.frontend.screens.pihole import PiholeScreen
from rachotil.backend.components.keybinds.keybinds_manager import load_keybinds


class Rachotil(App):
    """
    Main Textual Application for controlling remote Linux servers.
    """
    CSS_PATH = "styles.tcss"

    def on_mount(self) -> None:
        self.apply_keybinds()
        self.push_screen(DashboardScreen())

    def apply_keybinds(self) -> None:
        config = load_keybinds()
        self.bind(config.get("menu", "space"), "show_menu", description="Menu")
        self.bind(config.get("quit", "q"), "quit", description="Quit")

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
            elif choice == "management":
                self.switch_screen(ManagementScreen())
            elif choice == "backup":
                self.switch_screen(BackupScreen())
            elif choice == "settings":
                self.switch_screen(SettingsScreen())
            elif choice == "snapshot":
                self.switch_screen(SnapshotScreen())
            elif choice == "services":
                self.switch_screen(ServicesScreen())
            elif choice == "firewall":
                self.switch_screen(FirewallScreen())
            elif choice == "docker":
                self.switch_screen(DockerScreen())
            elif choice == "pihole":
                self.switch_screen(PiholeScreen())

        self.push_screen(MenuScreen(), check_menu_result)