from textual.app import App
from textual.binding import Binding
from .components.menu import MenuScreen
from .screens.dashboard import DashboardScreen
from .screens.services import ServicesScreen
from .screens.settings import SettingsScreen
from .screens.docker import DockerScreen
from .screens.firewall import FirewallScreen
from .screens.file_manager import FileManagerScreen
from .screens.network_manager import NetworkManagerScreen
from ..storage.config_store import ConfigStore

class RachotilApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        Binding("ctrl+m", "show_menu", "Menu"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.db = ConfigStore()

    def on_mount(self):
        theme = self.db.get("theme", "theme-dark")
        if theme == "theme-light":
            self.add_class("light-layout")
        elif theme == "theme-cyber":
            self.add_class("cyber-layout")
        elif theme == "theme-solarized":
            self.add_class("solarized-layout")
        elif theme == "theme-retro":
            self.add_class("retro-layout")
            
        self.push_screen(DashboardScreen())

    def action_show_menu(self):
        def check_menu(screen_name):
            if screen_name:
                self.switch_screen(screen_name)
        self.push_screen(MenuScreen(), check_menu)

    def switch_screen(self, name: str):
        self.pop_screen()
        if name == "dashboard": self.push_screen(DashboardScreen())
        elif name == "services": self.push_screen(ServicesScreen())
        elif name == "settings": self.push_screen(SettingsScreen())
        elif name == "docker": self.push_screen(DockerScreen())
        elif name == "firewall": self.push_screen(FirewallScreen())
        elif name == "file_manager": self.push_screen(FileManagerScreen())
        elif name == "network_manager": self.push_screen(NetworkManagerScreen())