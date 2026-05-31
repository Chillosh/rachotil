from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, Label, Checkbox, OptionList, Log
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual import work
from ...backend.ssh.config import get_ssh_config
from ...backend.ssh.ssh import SSH
import os
from datetime import datetime

class BackupScreen(Screen):
    CSS_PATH = "../styles.tcss"
    
    DEFAULT_DIRS = {
        "/etc": "System configuration",
        "/home": "User home directories",
        "/var/www": "Web content",
        "/root": "Root home directory",
        "/opt": "Optional software",
        "/srv": "Server data",
    }
    
    def __init__(self):
        super().__init__()
        self.ssh = None
        self.selected_dirs = set(self.DEFAULT_DIRS.keys())
        self.additional_dirs = set()
        self.checkbox_to_path = {}
    
    def compose(self):
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
                yield Label("[bold cyan]3. Backup name:[/bold cyan]")
                yield Input(
                    value=f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz",
                    id="backup-name"
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
        if not self.ssh:
            return
        try:
            cmd = f"find / -maxdepth 4 -name '*{query}*' -type d 2>/dev/null | head -10"
            out, err = self.ssh.run_command(cmd)
            results = [line.strip() for line in out.strip().split("\n") if line.strip()]
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
            self.create_and_download_backup()
        elif event.button.id == "cancel-btn":
            self.app.action_show_menu()
    
    @work(thread=True)
    def create_and_download_backup(self) -> None:
        try:
            if not self.selected_dirs and not self.additional_dirs:
                self.write_log("Error: Select at least one directory for backup.")
                return
            
            backup_name = self.query_one("#backup-name", Input).value.strip()
            if not backup_name:
                self.write_log("Error: Backup name cannot be empty.")
                return
            
            if not backup_name.endswith(".tar.gz"):
                backup_name += ".tar.gz"
            
            all_dirs = list(self.selected_dirs) + list(self.additional_dirs)
            dirs_str = " ".join(f'"{d}"' for d in all_dirs)
            
            self.write_log(f"Step 1/3: Archiving data on server into {backup_name}...")
            self.write_log(f"Includes: {', '.join(all_dirs)}")
            
            remote_archive = f"/tmp/{backup_name}"
            cmd = f"tar -czf {remote_archive} {dirs_str} 2>&1"
            
            out, err = self.ssh.run_sudo_command(cmd)
            
            if not self.ssh.file_exists(remote_archive):
                self.write_log("Error: Backup creation on server failed.")
                self.write_log(f"Error details: {err or out}")
                return
            
            self.write_log("Step 1/3 completed. Archive created on server.")
            
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads_dir, exist_ok=True)
            local_file = os.path.join(downloads_dir, backup_name)
            
            self.write_log(f"Step 2/3: Downloading data to local machine...")
            self.write_log(f"Path: {local_file}")
            
            success, message = self.ssh.download_file(remote_archive, local_file)
            
            if success:
                self.write_log("Step 2/3 completed. File successfully downloaded.")
                self.write_log("Step 3/3: Cleaning up remote server /tmp directory...")
                self.ssh.run_command(f"rm {remote_archive}")
                self.write_log("SUCCESS: Backup is ready in your Downloads folder.")
            else:
                self.write_log(f"Download failed: {message}")
        
        except Exception as e:
            self.write_log(f"Critical error: {str(e)}")