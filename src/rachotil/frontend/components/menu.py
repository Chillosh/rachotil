"""
Overlay menu for navigating between different application screens.
"""

from textual.screen import ModalScreen
from textual.widgets import OptionList, Input, Button, Static
from textual.widgets.option_list import Option
from textual.containers import Vertical, Horizontal
from textual import on, work
from ...backend.components.power.power_manager import PowerManager
from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH

class MenuScreen(ModalScreen[str]):
    """
    Modal UI Screen that presents a searchable list of available application modules.
    """
    CSS_PATH = ["styles/global.tcss", "styles/dashboard.tcss"]

    ALL_OPTIONS = [
        ("System Dashboard", "dashboard"),
        ("Stats Monitoring", "stats"),
        ("SSH Terminal", "term"),
        ("File Manager", "file_manager"),
        ("Package Manager", "packages"),
        ("Backup Manager", "backup"),
        ("Snapshot Manager", "snapshot"),
        ("Service Manager", "services"),
        ("Docker Dashboard", "docker"),
        ("Pi-hole", "pihole"),
        ("Settings", "settings")
    ]

    def compose(self) -> None:
        with Vertical(id="menu-container"):
            yield Input(placeholder="Search menu...", id="menu-search")
            
            with Horizontal(id="menu-power-actions"):
                yield Button("Wake up (WOL)", id="btn-wol", variant="success")
                yield Button("Power Off", id="btn-poweroff", variant="error")
                
            yield Static("", id="menu-power-log")
            yield OptionList(id="main_menu")

    def on_mount(self) -> None:
        self.filter_menu("")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "menu-search":
            self.filter_menu(event.value)

    def filter_menu(self, query: str) -> None:
        """
        Filter the menu items based on the search query.
        """
        menu = self.query_one("#main_menu", OptionList)
        menu.clear_options()
        for label, opt_id in self.ALL_OPTIONS:
            if query.lower() in label.lower():
                menu.add_option(Option(label, id=opt_id))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option_id)

    def action_close(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed)
    def handle_power_buttons(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-poweroff":
            self.execute_poweroff()
        elif event.button.id == "btn-wol":
            self.execute_wol()

    @work(thread=True)
    def execute_poweroff(self) -> None:
        self.app.call_from_thread(lambda: self.query_one("#menu-power-log", Static).update("Connecting to power off..."))
        try:
            config = get_ssh_config()
            ssh = SSH(config["host"], config["user"], config["password"], config.get("sudo_password"))
            ssh.connect()
            pm = PowerManager(ssh)
            success, msg = pm.power_off()
            self.app.call_from_thread(lambda: self.query_one("#menu-power-log", Static).update(msg))
        except Exception as e:
            self.app.call_from_thread(lambda: self.query_one("#menu-power-log", Static).update(f"Error: {e}"))

    def execute_wol(self) -> None:
        pm = PowerManager()
        mac = pm.get_saved_mac()
        if not mac:
            self.query_one("#menu-power-log", Static).update("Error: No MAC address saved. Go to Settings!")
            return
            
        self.query_one("#menu-power-log", Static).update("Sending Magic Packet...")
        success, msg = pm.wake_on_lan(mac)
        self.query_one("#menu-power-log", Static).update(msg)