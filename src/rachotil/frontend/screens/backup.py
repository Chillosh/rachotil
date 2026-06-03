"""
Screen for managing and creating remote server backups.
"""

import os
from datetime import datetime
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, Label, Checkbox, OptionList, Log
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual import work

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.backup.backup_manager import BackupManager

class BackupScreen(Screen):
    """
    UI Screen for selecting directories, searching for additional paths, and performing backups.
    """
    CSS_PATH = ["../components/styles/global.tcss", "../components/styles/backup.tcss"]
    
    DEFAULT_DIRS = {
        "/etc": "System configuration",
        "/home": "User home directories",
        "/var/www": "Web content",
        "/root": "Root home directory",
        "/opt": "Optional software",
        "/srv": "Server data",
    }
    
    def __init__(self) -> None:
        super().__init__()
        self.ssh = None
        self.backup_mgr = None
        self.selected_dirs = set(self.DEFAULT_DIRS.keys())
        self.additional_dirs = set()
        self.checkbox_to_path = {}
    
    def compose(self) -> None:
        yield Header()
        yield Footer()
        
        with Vertical(id="backup-main"):
            yield Static("Backup Manager", id="backup-title")
            
            with ScrollableContainer(id="backup-dirs-container"):
                yield Label("[bold cyan]1. Default directories:[/bold cyan]")
                for path, desc in self.DEFAULT_DIRS.items():
                    safe_name = path.replace("/", "_").strip("_")
                    cb_id = f"dir-{safe_name}"
                    self.checkbox_to_path[cb_id] = path
                    yield Checkbox(f"{path} - {desc}", value=True, id=cb_id)
            
            with Horizontal(classes="horizontal-container"):
                with Container(id="backup-additional", classes="column"):
                    yield Label("[bold cyan]2. Find additional directory:[/bold cyan]")
                    yield Input(placeholder="Enter path part (e.g., log)", id="search-input")
                    yield Label("Results (click to add):")
                    yield OptionList(id="search-results-list")
                
                with Container(id="backup-custom-selected", classes="column"):
                    yield Label("[bold cyan]Manually added directories:[/bold cyan]")
                    yield OptionList(id="custom-dirs-list")
            
            with Container(id="backup-options"):
                yield Label("[bold cyan]3. Backup Settings:[/bold cyan]")
                yield Input(
                    value=f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz",
                    id="backup-name",
                    placeholder="Backup file name"
                )
                yield Input(
                    placeholder="Local download destination (e.g. C:/backups). Leaves empty for Downloads folder.",
                    id="backup-dest-input"
                )
            
            with Horizontal(id="backup-buttons"):
                yield Button("Create & Download Backup", id="create-download-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn", variant="error")
            
            yield Log(id="backup-status-log", classes="status-display")
    
    def on_mount(self) -> None:
        self.write_log("Initialization... Connecting to server.")
        try:
            config = get_ssh_config()
            self.ssh = SSH(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                sudo_password=config.get("sudo_password")
            )
            self.ssh.connect()
            self.backup_mgr = BackupManager(self.ssh)
            self.write_log(f"Successfully connected to {config['host']}")
        except Exception as e:
            self.write_log(f"Connection failed: {str(e)}")
    
    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#backup-status-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        checkbox_id = event.checkbox.id
        if checkbox_id in self.checkbox_to_path:
            path = self.checkbox_to_path[checkbox_id]
            if event.value:
                self.selected_dirs.add(path)
            else:
                self.selected_dirs.discard(path)
    
    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            if len(event.value) >= 2:
                self.search_directories(event.value)
            else:
                self.query_one("#search-results-list", OptionList).clear_options()
    
    @work(thread=True)
    def search_directories(self, query: str) -> None:
        if not self.backup_mgr:
            return
        try:
            results = self.backup_mgr.search_directories(query)
            self.app.call_from_thread(self._update_search_ui, results)
        except Exception as e:
            self.write_log(f"Search error: {str(e)}")

    def _update_search_ui(self, results: list[str]) -> None:
        options = self.query_one("#search-results-list", OptionList)
        options.clear_options()
        for path in results:
            if path not in self.additional_dirs and path not in self.selected_dirs:
                options.add_option(path)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "search-results-list":
            selected_path = str(event.option.prompt)
            self.additional_dirs.add(selected_path)
            custom_list = self.query_one("#custom-dirs-list", OptionList)
            custom_list.add_option(selected_path)
            event.option_list.remove_option_at_index(event.option_index)
            self.write_log(f"Added directory to backup: {selected_path}")
        elif event.option_list.id == "custom-dirs-list":
            selected_path = str(event.option.prompt)
            self.additional_dirs.discard(selected_path)
            event.option_list.remove_option_at_index(event.option_index)
            self.write_log(f"Removed directory: {selected_path}")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-download-btn":
            self.execute_backup()
        elif event.button.id == "cancel-btn":
            self.app.action_show_menu()
    
    @work(thread=True)
    def execute_backup(self) -> None:
        if not self.backup_mgr:
             self.write_log("Error: Connection to server not established.")
             return

        backup_name = self.query_one("#backup-name", Input).value.strip()
        local_dest = self.query_one("#backup-dest-input", Input).value.strip()
        
        if not local_dest:
            local_dest = os.path.join(os.path.expanduser("~"), "Downloads")

        all_dirs = list(self.selected_dirs) + list(self.additional_dirs)
        
        try:
            success, message = self.backup_mgr.create_and_download_backup(
                dirs_to_backup=all_dirs, 
                backup_name=backup_name,
                local_dest=local_dest,
                status_callback=self.write_log
            )
            
            if not success:
                self.write_log(f"Error: {message}")
            else:
                self.write_log(message)
                
        except Exception as e:
            self.write_log(f"Critical error: {str(e)}")