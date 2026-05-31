from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable, Log
from textual.containers import Vertical, Horizontal
from textual import work
import os
import stat
from ...ssh.config import get_ssh_config
from ...ssh.ssh import SSH

class FileManagerScreen(Screen):
    CSS_PATH = "../styles.tcss"

    def __init__(self):
        super().__init__()
        self.ssh = None
        self.sftp = None
        self.current_path = "/"

    def compose(self):
        yield Header()
        yield Footer()
        
        with Vertical(id="fm-main"):
            yield Static("SFTP File Explorer", id="fm-title")
            
            with Horizontal(id="fm-controls"):
                yield Static("Path:", id="fm-path-label")
                yield Static("/", id="fm-current-path")
                yield Button("Up (..)", id="btn-up-dir", variant="warning")
                yield Button("Refresh", id="btn-refresh-dir", variant="default")

            yield DataTable(id="fm-table", cursor_type="row")
            yield Log(id="fm-log", classes="status-display")

    def on_mount(self) -> None:
        table = self.query_one("#fm-table", DataTable)
        table.add_columns("Type", "Name", "Size", "Permissions")
        
        try:
            config = get_ssh_config()
            self.ssh = SSH(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                sudo_password=config.get("sudo_password")
            )
            self.ssh.connect()
            self.sftp = self.ssh.get_sftp_client()
            
            if config["user"] != "root":
                self.current_path = f"/home/{config['user']}"
            else:
                self.current_path = "/root"
                
            self.write_log(f"Connected to SFTP. Starting at {self.current_path}")
            self.load_directory()
        except Exception as e:
            self.write_log(f"Connection failed: {str(e)}")

    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#fm-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-refresh-dir":
            self.load_directory()
        elif btn_id == "btn-up-dir":
            self.navigate_up()

    def navigate_up(self) -> None:
        if self.current_path != "/":
            parent = os.path.dirname(self.current_path)
            if not parent:
                parent = "/"
            self.current_path = parent
            self.load_directory()

    @work(thread=True)
    def load_directory(self) -> None:
        if not self.sftp:
            return
            
        self.write_log(f"Loading {self.current_path}...")
        try:
            self.app.call_from_thread(lambda: self.query_one("#fm-current-path", Static).update(self.current_path))
            
            directory_items = self.sftp.listdir_attr(self.current_path)
            
            dirs = []
            files = []
            
            for item in directory_items:
                is_dir = stat.S_ISDIR(item.st_mode)
                size = f"{item.st_size} B"
                if item.st_size > 1048576:
                    size = f"{item.st_size / 1048576:.1f} MB"
                elif item.st_size > 1024:
                    size = f"{item.st_size / 1024:.1f} KB"
                    
                perms = stat.filemode(item.st_mode)
                
                if is_dir:
                    dirs.append(("[DIR]", item.filename, "", perms))
                else:
                    files.append(("[FILE]", item.filename, size, perms))
                    
            dirs.sort(key=lambda x: x[1].lower())
            files.sort(key=lambda x: x[1].lower())
            
            all_items = dirs + files
            self.app.call_from_thread(self._update_table, all_items)
        except Exception as e:
            self.write_log(f"Error reading directory: {str(e)}")

    def _update_table(self, data: list) -> None:
        table = self.query_one("#fm-table", DataTable)
        table.clear()
        for row in data:
            row_key = f"{row[0]}|{row[1]}"
            table.add_row(*row, key=row_key)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_key = event.row_key.value
        item_type, item_name = row_key.split("|", 1)
        
        target_path = f"{self.current_path}/{item_name}"
        if self.current_path == "/":
            target_path = f"/{item_name}"
            
        if item_type == "[DIR]":
            self.current_path = target_path
            self.load_directory()
        else:
            self.download_file(target_path, item_name)

    @work(thread=True)
    def download_file(self, remote_path: str, filename: str) -> None:
        self.write_log(f"Starting download: {filename}...")
        try:
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads_dir, exist_ok=True)
            local_path = os.path.join(downloads_dir, filename)
            
            self.sftp.get(remote_path, local_path)
            self.write_log(f"Successfully downloaded to: {local_path}")
        except Exception as e:
            self.write_log(f"Download failed: {str(e)}")

    def on_unmount(self) -> None:
        if self.sftp:
            self.sftp.close()