"""
Screen for configuring application settings, including UI themes and remote server credentials.
"""

import re
import json
from pathlib import Path
from textual import on, work
from textual.containers import Horizontal, Vertical, Container
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Input, SelectionList, Static, RadioSet, RadioButton, TextArea

from ...backend.components.ssh.config import get_ssh_config, save_ssh_config
from ...backend.components.stats.config import load_stats_config, save_stats_config
from ...backend.components.keybinds.keybinds_manager import load_keybinds, save_keybinds
from ...backend.components.snapshot.snapshot_manager import SnapshotManager
from ...backend.components.power.power_manager import PowerManager
from ...backend.components.network.netplan_manager import NetplanManager
from ...backend.components.ssh.ssh import SSH

class SettingsScreen(Screen):
    """
    UI Screen that provides access to various application configurations.
    """
    CSS_PATH = ["../components/styles/global.tcss", "../components/styles/settings.tcss"]
    
    def compose(self) -> None:
        yield Header()
        yield Footer()
        with Vertical(id="settings-main"):
            yield Static("Control Panel & Settings", id="settings-title")
            
            with Container(classes="settings-card"):
                yield Static("Interface Customization", classes="card-label")
                with RadioSet(id="theme-panel"):
                    yield RadioButton("Default Dark Theme", id="theme-dark", value=True)
                    yield RadioButton("Light Matrix Theme", id="theme-light")
                    yield RadioButton("Cyberpunk Terminal", id="theme-cyber")
                    yield RadioButton("Solarized Code", id="theme-solarized")
                    yield RadioButton("Retro DOS", id="theme-retro")
            
            with Container(classes="settings-card"):
                yield Static("System Configurations", classes="card-label")
                with Horizontal(classes="card-buttons"):
                    yield Button("Stats Configuration", id="stats", variant="primary")
                    yield Button("SSH Connection Settings", id="ssh", variant="primary")
                    yield Button("Keybinds Settings", id="keybinds", variant="primary")
                    yield Button("Dashboard ASCII Art", id="ascii_art_btn", variant="primary")
                    yield Button("MAC Address (WOL)", id="wol_settings_btn", variant="warning")
                    yield Button("Set Static IP", id="static_ip_btn", variant="error")
                    yield Button("Timeshift Device Config", id="timeshift_btn", variant="primary")

    def action_open_main_menu(self) -> None:
        self.app.action_show_menu()

    def action_quit(self) -> None:
        self.app.action_quit()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        selected_id = event.radio_set.pressed_button.id
        all_classes = ["light-layout", "cyber-layout", "solarized-layout", "retro-layout"]
        
        for cls in all_classes:
            self.app.remove_class(cls)

        if selected_id == "theme-light":
            self.app.add_class("light-layout")
        elif selected_id == "theme-cyber":
            self.app.add_class("cyber-layout")
        elif selected_id == "theme-solarized":
            self.app.add_class("solarized-layout")
        elif selected_id == "theme-retro":
            self.app.add_class("retro-layout")

    @on(Button.Pressed, "#stats")
    def show_stats_menu(self) -> None:
        self.app.push_screen(StatsSettingsModal())

    @on(Button.Pressed, "#ssh")
    def show_ssh_menu(self) -> None:
        self.app.push_screen(SSHSettingsModal())
    
    @on(Button.Pressed, "#keybinds")
    def show_keybinds_menu(self) -> None:
        self.app.push_screen(KeybindsSettingsModal())
    
    @on(Button.Pressed, "#ascii_art_btn")
    def show_ascii_modal(self) -> None:
        self.app.push_screen(AsciiArtModal())
    
    @on(Button.Pressed, "#wol_settings_btn")
    def show_wol_modal(self) -> None:
        self.app.push_screen(WolSettingsModal())

    @on(Button.Pressed, "#static_ip_btn")
    def show_static_ip_modal(self) -> None:
        self.app.push_screen(StaticIpModal())
    
    @on(Button.Pressed, "#timeshift_btn")
    def show_ts_modal(self) -> None:
        self.app.push_screen(TimeshiftSettingsModal())


class StatsSettingsModal(ModalScreen):
    """
    Modal dialog for configuring which statistics blocks are displayed.
    """
    CSS_PATH = ["../components/styles/global.tcss"]

    def __init__(self):
        super().__init__()
        self.config = load_stats_config()
        self.blocks = self.config["blocks"]

    def compose(self) -> None:
        yield Static("Enable/disable stat blocks")
        yield SelectionList(
            *((block["label"], block["id"]) for block in self.blocks),
            id="stats_options",
        )
        yield Static("Add custom stat block")
        with Vertical():
            yield Input(placeholder="Label (example: Docker)", id="custom_label")
            yield Input(placeholder="Command (example: docker ps)", id="custom_command")
            yield Input(placeholder="Interval in seconds (example: 5)", id="custom_interval")
        with Horizontal():
            yield Button("Add Custom", id="add_custom")
            yield Button("Delete Selected Custom", id="delete_custom")
            yield Button("Save", id="save")
            yield Button("Cancel", id="cancel")
        yield Static("", id="stats_message")

    def _rebuild_stats_options(self, selected_values: set[str] | None = None) -> None:
        selection_list = self.query_one("#stats_options", SelectionList)
        selection_list.clear_options()
        selection_list.add_options(
            [(block["label"], block["id"]) for block in self.blocks]
        )

        if selected_values is None:
            selected_values = {block["id"] for block in self.blocks if block.get("enabled")}

        valid_values = {block["id"] for block in self.blocks}
        for value in selected_values & valid_values:
            selection_list.select(value)

    def on_mount(self) -> None:
        self._rebuild_stats_options()

    @on(Button.Pressed, "#add_custom")
    def add_custom_block(self) -> None:
        label = self.query_one("#custom_label", Input).value.strip()
        command = self.query_one("#custom_command", Input).value.strip()
        interval_raw = self.query_one("#custom_interval", Input).value.strip()
        message = self.query_one("#stats_message", Static)

        if not label or not command or not interval_raw:
            message.update("Please fill label, command and interval.")
            return

        try:
            interval = int(interval_raw)
            if interval < 1:
                raise ValueError
        except ValueError:
            message.update("Interval must be a positive number.")
            return

        slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or "custom"
        block_id = f"custom_{slug}"
        existing = {block["id"] for block in self.blocks}
        suffix = 2
        while block_id in existing:
            block_id = f"custom_{slug}_{suffix}"
            suffix += 1

        self.blocks.append(
            {
                "id": block_id,
                "label": label,
                "command": command,
                "interval_seconds": interval,
                "enabled": True,
                "built_in": False,
            }
        )

        selected_values = set(self.query_one("#stats_options", SelectionList).selected)
        selected_values.add(block_id)
        self._rebuild_stats_options(selected_values)

        self.query_one("#custom_label", Input).value = ""
        self.query_one("#custom_command", Input).value = ""
        self.query_one("#custom_interval", Input).value = ""
        message.update("Custom block added. Save to persist changes.")

    @on(Button.Pressed, "#delete_custom")
    def delete_custom_blocks(self) -> None:
        selection_list = self.query_one("#stats_options", SelectionList)
        message = self.query_one("#stats_message", Static)
        selected_ids = set(selection_list.selected)

        custom_ids = [
            block["id"]
            for block in self.blocks
            if not block.get("built_in") and block["id"] in selected_ids
        ]
        if not custom_ids:
            message.update("Select one or more custom blocks to delete.")
            return

        self.blocks = [block for block in self.blocks if block["id"] not in custom_ids]
        self._rebuild_stats_options(selected_ids - set(custom_ids))

        message.update(f"Deleted {len(custom_ids)} custom block(s). Save to persist changes.")

    @on(Button.Pressed, "#save")
    def save_stats_settings(self) -> None:
        selected_ids = set(self.query_one("#stats_options", SelectionList).selected)

        for block in self.blocks:
            block["enabled"] = block["id"] in selected_ids

        save_stats_config({"version": self.config.get("version", 1), "blocks": self.blocks})
        self.app.pop_screen()

    @on(Button.Pressed, "#cancel")
    def return_to_settings(self) -> None:
        self.app.pop_screen()


class SSHSettingsModal(ModalScreen):
    """
    Modal dialog for editing SSH connection credentials.
    """
    CSS_PATH = ["../components/styles/global.tcss"]

    def compose(self) -> None:
        config = get_ssh_config()
        with Vertical():
            yield Static("SSH Host")
            yield Input(value=config["host"], id="ssh_host")
            yield Static("SSH User")
            yield Input(value=config["user"], id="ssh_user")
            yield Static("SSH Password")
            yield Input(value=config["password"], password=True, id="ssh_password")
            yield Static("SUDO Password (optional, defaults to SSH password)")
            yield Input(value=config.get("sudo_password", ""), password=True, id="ssh_sudo_password")
        with Horizontal():
            yield Button("Save", id="save_ssh")
            yield Button("Cancel", id="cancel_ssh")

    @on(Button.Pressed, "#save_ssh")
    def save_settings(self) -> None:
        host = self.query_one("#ssh_host", Input).value.strip()
        user = self.query_one("#ssh_user", Input).value.strip()
        password = self.query_one("#ssh_password", Input).value
        sudo_password = self.query_one("#ssh_sudo_password", Input).value
        save_ssh_config(host=host, user=user, password=password, sudo_password=sudo_password)
        self.app.pop_screen()

    @on(Button.Pressed, "#cancel_ssh")
    def cancel_settings(self) -> None:
        self.app.pop_screen()

class KeybindsSettingsModal(ModalScreen):
    CSS_PATH = ["../components/styles/global.tcss"]
    def compose(self) -> None:
        config = load_keybinds()
        with Vertical():
            yield Static("Keybind Configurations")
            yield Static("Main Menu Key (e.g. space, m, ctrl+m)")
            yield Input(value=config.get("menu", "space"), id="kb_menu")
            
            yield Static("Quit App Key (e.g. q, escape, ctrl+q)")
            yield Input(value=config.get("quit", "q"), id="kb_quit")

            yield Static("Help Key (e.g. h, f1)")
            yield Input(value=config.get("help", "h"), id="kb_help")
            
        with Horizontal():
            yield Button("Save", id="save_kb", variant="success")
            yield Button("Cancel", id="cancel_kb", variant="error")

    @on(Button.Pressed, "#save_kb")
    def save_settings(self) -> None:
        menu_key = self.query_one("#kb_menu", Input).value.strip()
        quit_key = self.query_one("#kb_quit", Input).value.strip()
        help_key = self.query_one("#kb_help", Input).value.strip()
        
        save_keybinds({"menu": menu_key, "quit": quit_key, "help": help_key})
        
        if hasattr(self.app, "apply_keybinds"):
            self.app.apply_keybinds()
            self.app.screen.refresh_bindings()
            
        self.app.pop_screen()

    @on(Button.Pressed, "#cancel_kb")
    def cancel_settings(self) -> None:
        self.app.pop_screen()

class AsciiArtModal(ModalScreen):
    CSS_PATH = ["../components/styles/global.tcss"]
    def _storage_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "backend" / "storage" / "dashboard_config.json"

    def compose(self) -> None:
        try:
            config = json.loads(self._storage_path().read_text(encoding="utf-8"))
            current_art = config.get("ascii_art", "")
        except Exception:
            current_art = ""

        with Vertical():
            yield Static("Edit Dashboard ASCII Art")
            yield TextArea(text=current_art, id="ascii_input", language="markdown")
            
        with Horizontal():
            yield Button("Save", id="save_ascii", variant="success")
            yield Button("Cancel", id="cancel_ascii", variant="error")

    @on(Button.Pressed, "#save_ascii")
    def save_art(self) -> None:
        new_art = self.query_one("#ascii_input", TextArea).text
        path = self._storage_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"ascii_art": new_art}, indent=4), encoding="utf-8")
        self.app.pop_screen()

    @on(Button.Pressed, "#cancel_ascii")
    def cancel_art(self) -> None:
        self.app.pop_screen()

class WolSettingsModal(ModalScreen):
    def compose(self) -> None:
        pm = PowerManager()
        current_mac = pm.get_saved_mac()
        
        with Vertical(classes="settings-modal"):
            yield Static("Wake On LAN Setup")
            yield Static("Enter target server MAC address (e.g. AA:BB:CC:DD:EE:FF)")
            yield Input(value=current_mac, id="wol_mac_input")
            
            with Horizontal():
                yield Button("Save", id="save_wol", variant="success")
                yield Button("Cancel", id="cancel_wol", variant="error")

    @on(Button.Pressed, "#save_wol")
    def save(self) -> None:
        mac = self.query_one("#wol_mac_input", Input).value.strip()
        PowerManager().save_mac(mac)
        self.app.pop_screen()

    @on(Button.Pressed, "#cancel_wol")
    def cancel(self) -> None:
        self.app.pop_screen()

class StaticIpModal(ModalScreen):
    def compose(self) -> None:
        with Vertical(classes="settings-modal", id="ip-modal-container"):
            yield Static("[bold red]WARNING: Applying this will drop your connection![/bold red]")
            yield Input(placeholder="Interface (e.g. eth0, enp3s0)", id="ip_interface")
            yield Input(placeholder="IP Address with CIDR (e.g. 192.168.1.200/24)", id="ip_address")
            yield Input(placeholder="Gateway (e.g. 192.168.1.1)", id="ip_gateway")
            yield Input(placeholder="DNS (e.g. 1.1.1.1, 8.8.8.8)", value="1.1.1.1, 8.8.8.8", id="ip_dns")
            
            with Horizontal():
                yield Button("APPLY NEW IP", id="save_ip", variant="error")
                yield Button("Cancel", id="cancel_ip", variant="default")

    @work(thread=True)
    def apply_ip(self) -> None:
        interface = self.query_one("#ip_interface", Input).value.strip()
        ip = self.query_one("#ip_address", Input).value.strip()
        gateway = self.query_one("#ip_gateway", Input).value.strip()
        dns = self.query_one("#ip_dns", Input).value.strip()
        
        if not all([interface, ip, gateway, dns]):
            return

        try:
            config = get_ssh_config()
            ssh = SSH(config["host"], config["user"], config["password"], config.get("sudo_password"))
            ssh.connect()
            nm = NetplanManager(ssh)
            nm.apply_static_ip(interface, ip, gateway, dns)
        except:
            pass
            
        self.app.call_from_thread(self.app.pop_screen)

    @on(Button.Pressed, "#save_ip")
    def save(self) -> None:
        self.apply_ip()

    @on(Button.Pressed, "#cancel_ip")
    def cancel(self) -> None:
        self.app.pop_screen()

class TimeshiftSettingsModal(ModalScreen):
    def compose(self) -> None:
        mgr = SnapshotManager(None) 
        config = mgr.load_config()
        current_dev = config.get("backup_device", "")
        
        with Vertical(classes="settings-modal"):
            yield Static("Timeshift Target Device")
            yield Static("Enter target partition path (e.g. /dev/sdb1, /dev/dm-0). Leave empty for auto.")
            yield Input(value=current_dev, id="ts_dev_input")
            
            with Horizontal():
                yield Button("Save", id="save_ts", variant="success")
                yield Button("Cancel", id="cancel_ts", variant="error")

    @on(Button.Pressed, "#save_ts")
    def save(self) -> None:
        dev = self.query_one("#ts_dev_input", Input).value.strip()
        
        mgr = SnapshotManager(None)
        config = mgr.load_config()
        config["backup_device"] = dev
        
        path = mgr._storage_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        import json
        path.write_text(json.dumps(config))
        
        self.app.pop_screen()

    @on(Button.Pressed, "#cancel_ts")
    def cancel(self) -> None:
        self.app.pop_screen()