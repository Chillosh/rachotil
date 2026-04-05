import re
from textual import on
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Input, SelectionList, Static
from ...ssh.config import get_ssh_config, save_ssh_config
from ...stats.config import load_stats_config, save_stats_config

CSS_PATH = "../styles.tcss"

class SettingsScreen(Screen):
    def compose(self):
        yield Header()
        yield Button("Stats Configuration", id="stats")
        yield Button("SSH Connection Settings", id="ssh")
        yield Footer()

    @on(Button.Pressed, "#stats")
    def show_stats_menu(self):
        self.app.push_screen(StatsSettingsModal())

    @on(Button.Pressed, "#ssh")
    def show_ssh_menu(self):
        self.app.push_screen(SSHSettingsModal())

class StatsSettingsModal(ModalScreen):
    def __init__(self):
        super().__init__()
        self.config = load_stats_config()
        self.blocks = self.config["blocks"]

    def compose(self):
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

    def on_mount(self):
        self._rebuild_stats_options()

    @on(Button.Pressed, "#add_custom")
    def add_custom_block(self):
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
    def delete_custom_blocks(self):
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
    def save_stats_settings(self):
        selected_ids = set(self.query_one("#stats_options", SelectionList).selected)

        for block in self.blocks:
            block["enabled"] = block["id"] in selected_ids

        save_stats_config({"version": self.config.get("version", 1), "blocks": self.blocks})
        self.app.pop_screen()

    @on(Button.Pressed, "#cancel")
    def return_to_settings(self):
        self.app.pop_screen()

class SSHSettingsModal(ModalScreen):
    def compose(self):
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
    def save_settings(self):
        host = self.query_one("#ssh_host", Input).value.strip()
        user = self.query_one("#ssh_user", Input).value.strip()
        password = self.query_one("#ssh_password", Input).value
        sudo_password = self.query_one("#ssh_sudo_password", Input).value
        save_ssh_config(host=host, user=user, password=password, sudo_password=sudo_password)
        self.app.pop_screen()

    @on(Button.Pressed, "#cancel_ssh")
    def cancel_settings(self):
        self.app.pop_screen()