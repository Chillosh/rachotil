from textual.app import App
from rachotil.frontend.screens.docker import DockerScreen
from rachotil.frontend.screens.file_manager import FileManagerScreen
from rachotil.frontend.screens.network_manager import NetworkManagerScreen
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


class Rachotil(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("space", "show_menu", "Menu"),
        ("q", "quit", "Quit")
    ]

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen())

    def action_show_menu(self) -> None:
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
            elif choice == "network":
                self.switch_screen(NetworkManagerScreen())

        self.push_screen(MenuScreen(), check_menu_result)