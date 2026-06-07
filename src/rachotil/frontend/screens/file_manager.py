from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable, Log, Input
from textual.containers import Vertical, Horizontal
from textual import work
import os
from ..components.editor_modal import EditorModal
from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.file_manager.sftp_manager import SFTPManager

class FileManagerScreen(Screen):
    CSS_PATH = ["../components/styles/global.tcss", "../components/styles/file_manager.tcss"]

    def __init__(self):
        super().__init__()
        self.ssh = None
        self.sftp_mgr = None
        self.current_path = "/"

    def compose(self) -> None:
        yield Header()
        yield Footer()
        
        with Vertical(id="fm-main"):
            yield Static("SFTP File Explorer", id="fm-title")
            
            with Horizontal(id="fm-controls"):
                yield Static("Path:", id="fm-path-label")
                yield Static("/", id="fm-current-path")
                yield Button("Up (..)", id="btn-up-dir", variant="warning")
                yield Button("Upload File", id="btn-upload-file", variant="primary")
                yield Button("Edit File", id="btn-edit-file", variant="warning")
                yield Button("Refresh", id="btn-refresh-dir", variant="default")

            with Horizontal(id="fm-actions"):
                yield Input(placeholder="New name / Copy dest", id="fm-input")
                yield Button("Create File", id="btn-create-file", variant="success")
                yield Button("Create Folder", id="btn-create-dir", variant="success")
                yield Button("Copy Selected", id="btn-copy-item", variant="primary")
                yield Button("Delete Selected", id="btn-delete-item", variant="error")

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
            
            self.sftp_mgr = SFTPManager(self.ssh)
            if self.sftp_mgr.open_sftp():
                if config["user"] != "root":
                    self.current_path = f"/home/{config['user']}"
                else:
                    self.current_path = "/root"
                    
                self.write_log(f"Connected to SFTP. Starting at {self.current_path}")
                self.load_directory()
            else:
                self.write_log("Failed to open SFTP session.")
                
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
        elif btn_id == "btn-create-file":
            self.create_file()
        elif btn_id == "btn-create-dir":
            self.create_directory()
        elif btn_id == "btn-copy-item":
            self.copy_item()
        elif btn_id == "btn-delete-item":
            self.delete_item()
        elif btn_id == "btn-edit-file":
            self.open_editor()
        elif btn_id == "btn-upload-file":
            self.upload_file()

    def navigate_up(self) -> None:
        if self.current_path != "/":
            parent = os.path.dirname(self.current_path)
            if not parent:
                parent = "/"
            self.current_path = parent
            self.load_directory()

    @work(thread=True)
    def load_directory(self) -> None:
        if not self.sftp_mgr:
            return
            
        self.write_log(f"Loading {self.current_path}...")
        self.app.call_from_thread(lambda: self.query_one("#fm-current-path", Static).update(self.current_path))
        
        success, result = self.sftp_mgr.list_directory(self.current_path)
        
        if success:
            self.app.call_from_thread(self._update_table, result)
        else:
            self.write_log(str(result))

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
        if not self.sftp_mgr:
            return
            
        self.write_log(f"Starting download: {filename}...")
        success, message = self.sftp_mgr.download_file(remote_path, filename)
        self.write_log(message)

    @work(thread=True)
    def create_file(self) -> None:
        if not self.sftp_mgr:
            return
        filename = self.query_one("#fm-input", Input).value.strip()
        if not filename:
            self.write_log("Provide a file name.")
            return
        success, msg = self.sftp_mgr.create_file(self.current_path, filename)
        self.write_log(msg)
        if success:
            self.app.call_from_thread(lambda: setattr(self.query_one("#fm-input", Input), "value", ""))
            self.load_directory()

    @work(thread=True)
    def delete_item(self) -> None:
        if not self.sftp_mgr:
            return
        table = self.query_one("#fm-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
            _, item_name = row_key.split("|", 1)
        except Exception:
            self.write_log("Select an item to delete.")
            return
        
        target_path = f"{self.current_path}/{item_name}"
        if self.current_path == "/":
            target_path = f"/{item_name}"
            
        success, msg = self.sftp_mgr.delete_item(target_path)
        self.write_log(msg)
        if success:
            self.load_directory()

    @work(thread=True)
    def create_directory(self) -> None:
        if not self.sftp_mgr:
            return
        dirname = self.query_one("#fm-input", Input).value.strip()
        if not dirname:
            self.write_log("Provide a folder name.")
            return
        success, msg = self.sftp_mgr.create_directory(self.current_path, dirname)
        self.write_log(msg)
        if success:
            self.app.call_from_thread(lambda: setattr(self.query_one("#fm-input", Input), "value", ""))
            self.load_directory()

    @work(thread=True)
    def copy_item(self) -> None:
        if not self.sftp_mgr:
            return
        table = self.query_one("#fm-table", DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
            _, item_name = row_key.split("|", 1)
        except Exception:
            self.write_log("Select an item to copy.")
            return

        dest = self.query_one("#fm-input", Input).value.strip()
        if not dest:
            self.write_log("Provide a destination path or new name.")
            return

        target_path = f"{self.current_path}/{item_name}"
        if self.current_path == "/":
            target_path = f"/{item_name}"
            
        dest_path = f"{self.current_path}/{dest}" if not dest.startswith("/") else dest

        success, msg = self.sftp_mgr.copy_item(target_path, dest_path)
        self.write_log(msg)
        if success:
            self.app.call_from_thread(lambda: setattr(self.query_one("#fm-input", Input), "value", ""))
            self.load_directory()
    
    @work(thread=True)
    def open_editor(self) -> None:
        if not self.sftp_mgr:
            return
            
        table = self.query_one("#fm-table", DataTable)
        try:
            row_val = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
            item_type, filename = row_val.split("|", 1)
        except:
            self.write_log("Error: No file selected.")
            return

        if item_type == "[DIR]":
            self.write_log("Error: Cannot edit a directory.")
            return

        current_path = self.current_path
        full_path = f"{current_path}/{filename}".replace("//", "/")

        self.write_log(f"Downloading {filename} for editing...")
        
        success, content = self.sftp_mgr.read_file(full_path)
        
        if success:
            from rachotil.frontend.components.editor_modal import EditorModal
            self.app.call_from_thread(self.app.push_screen, EditorModal(full_path, content, self.sftp_mgr))
        else:
            self.write_log(f"Cannot edit file: {content}")

    @work(thread=True)
    def upload_file(self) -> None:
        if not self.sftp_mgr: return
        local_filepath = self.query_one("#fm-input", Input).value.strip()
        if not local_filepath:
            self.write_log("Type local file path into the input box first!")
            return
            
        current_path = self.current_path
        self.write_log(f"Uploading {local_filepath}...")
        success, msg = self.sftp_mgr.upload_file(local_filepath, current_path)
        self.write_log(msg)
        if success:
            self.app.call_from_thread(lambda: setattr(self.query_one("#fm-input", Input), "value", ""))
            self.load_directory()